"""Offer benchmark: where an amount sits in a CSC cohort, and what a given percentile pays.

Each cohort publishes up to five percentiles (90/75/50/25/10). A curve is a quantile function through
them, Q(q) = exp(g(z)) with z the normal score of q and g non-decreasing. Between published
percentiles g is linear: on the first release `validate` put it level with PCHIP and well ahead of a
plain lognormal. Beyond them it continues in a straight line whose slope is a lognormal fit to all the
points, and any answer out there is flagged as extrapolated. Past the top point, football cohorts whose
totals an outside constraint pins use a slope calibrated to it (`calibrated_curves`, from triangulate.py).

Revenue share publishes a cohort twice: everyone rostered ("With $0") and only the paid ("Without
$0"). That is one distribution with zero share z = 1 - n_paid / n_all, so all-rostered percentile p
above z is paid percentile q = (p - z) / (1 - z). Those become extra points for the paid curve, and the
all-rostered curve is z of zeros followed by the paid curve.

Flat stretches are real: when neighbouring percentiles are equal, many athletes got that exact amount
(most Non-A4 NIL deal holders sit at about $1,500). An amount on a flat stretch gets a percentile range,
not a point.

Every answer also carries what holds with no model at all: the published percentiles strictly below
and above the amount, and any published percentile it equals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.stats import norm

from .db import insert_df

METHODS = ("pchip", "linear", "lognormal")
METHOD = "linear"
BASE = {"nil_go": "deal_holders", "revenue_share": "paid"}
ZERO_TOL = 0.02          # all-rostered percentiles this close to the zero share add no paid point
TAIL_FLOOR = 0.05        # smallest tail slope, so amounts past the last published percentile still rank
Z_LIMIT = 8.0            # normal scores searched when inverting a curve
KEY = ["report", "gender", "sport", "position", "cohort", "window_label"]


@dataclass(frozen=True)
class CohortKey:
    report: str
    gender: str
    sport: str
    position: str
    cohort: str
    window_label: str

    def label(self) -> str:
        pos = "" if self.position == "All Positions" else f" {self.position}"
        return f"{self.report} · {self.gender}'s {self.sport}{pos} · {self.cohort}"


def _shape(xs: np.ndarray, ys: np.ndarray, method: str, top_mult: float = 1.0):
    """g and its tail slope for points (normal score, log dollars), xs increasing, ys non-decreasing.
    Past the top point the slope is scaled by `top_mult` (a tail calibrated to outside totals)."""
    slope = max(float(np.polyfit(xs, ys, 1)[0]), TAIL_FLOOR) if len(xs) >= 2 else None
    if slope is None:
        return None, None
    if method == "lognormal":
        mu = float(np.mean(ys) - slope * np.mean(xs))
        return (lambda z: mu + slope * np.asarray(z, float)), slope
    inner = PchipInterpolator(xs, ys) if method == "pchip" else (lambda z: np.interp(z, xs, ys))

    def g(z):
        z = np.asarray(z, float)
        mid = inner(np.clip(z, xs[0], xs[-1]))
        return np.where(z < xs[0], ys[0] + slope * (z - xs[0]),
                        np.where(z > xs[-1], ys[-1] + slope * top_mult * (z - xs[-1]), mid))
    return g, slope


@dataclass
class Curve:
    """The positive part of one cohort (paid athletes, or NIL deal holders) as a quantile function."""

    key: CohortKey
    population: str                                   # paid | deal_holders
    n: int | None
    knots: list[tuple[float, float, str]]             # (q, dollars, table it came from), sorted by q
    published: dict[str, list[tuple[float, float]]]   # population -> [(percentile, dollars)] as published
    zero_share: float | None = None
    n_all: int | None = None
    method: str = METHOD
    top_mult: float = 1.0                             # scale on the tail slope past the top point
    _g: object = field(init=False, repr=False, default=None)
    tail_slope: float | None = field(init=False, default=None)

    def __post_init__(self):
        if len(self.knots) >= 2:
            xs = norm.ppf([q for q, _, _ in self.knots])
            ys = np.log([v for _, v, _ in self.knots])
            self._g, self.tail_slope = _shape(xs, ys, self.method, self.top_mult)

    @property
    def fitted(self) -> bool:
        return self._g is not None

    def with_knots(self, knots: list[tuple[float, float, str]], method: str | None = None) -> "Curve":
        return Curve(self.key, self.population, self.n, knots, self.published, self.zero_share, self.n_all,
                     method or self.method)

    def quantile(self, q) -> np.ndarray:
        """Dollars at quantile q (0-1) of the positive part."""
        return np.exp(self._g(norm.ppf(np.asarray(q, float))))

    def rank(self, amount: float) -> tuple[float, float]:
        """(low, high) quantile of `amount` in the positive part; equal unless it sits on a flat stretch."""
        if amount <= 0:
            return 0.0, 0.0
        y = np.log(amount)
        tol = 1e-9

        def first(pred):   # smallest z in [-Z_LIMIT, Z_LIMIT] with pred(g(z)), by bisection
            lo, hi = -Z_LIMIT, Z_LIMIT
            if pred(self._g(lo)):
                return -np.inf
            if not pred(self._g(hi)):
                return np.inf
            for _ in range(80):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if pred(self._g(mid)) else (mid, hi)
            return hi

        z_lo = first(lambda v: v >= y - tol)            # first z reaching the amount
        z_hi = first(lambda v: v > y + tol)             # first z passing it
        return float(norm.cdf(z_lo)), float(norm.cdf(z_hi))

    def extrapolated(self, q: float) -> bool:
        return not (self.knots[0][0] - 1e-9 <= q <= self.knots[-1][0] + 1e-9)


# ---------------------------------------------------------------- building curves

def _monotone(knots: list[tuple[float, float, str]]) -> list[tuple[float, float, str]]:
    """Sort by q and keep a non-decreasing sequence. Published base-table points win; a point added
    from the all-rostered table that disagrees with them (rounding) is dropped."""
    knots = sorted(knots)
    base = [k for k in knots if k[2] != "all_rostered"]
    out = []
    for k in knots:
        if k[2] == "all_rostered":
            below = [v for q, v, _ in base if q < k[0]]
            above = [v for q, v, _ in base if q > k[0]]
            clash = any(abs(q - k[0]) < 1e-9 for q, _, _ in base)
            if clash or (below and k[1] < max(below)) or (above and k[1] > min(above)):
                continue
        if out and k[1] < out[-1][1]:
            continue
        out.append(k)
    return out


def curves(df: pd.DataFrame, method: str = METHOD,
           top_mults: dict[tuple[str, str, str], float] | None = None) -> tuple[list[Curve], list[dict]]:
    """One curve per cohort of a release, from `csc_percentiles` rows (for example `csc_latest`).
    `top_mults` scales the tail past the top point for cohorts keyed (report, sport, cohort)."""
    top_mults = top_mults or {}
    out: list[Curve] = []
    issues: list[dict] = []
    for key, g in df.groupby(KEY, dropna=False, sort=True):
        k = CohortKey(*key)
        base_pop = BASE[k.report]
        base = g[g.population == base_pop]
        if base.empty:
            issues.append({"check": "no_base_table", "severity": "warning", "report": k.report, "key": k.label(),
                           "detail": f"no {base_pop} table; no curve"})
            continue
        n = None if pd.isna(base.n.iloc[0]) else int(base.n.iloc[0])
        pub = base.dropna(subset=["value_usd"]).sort_values("percentile")
        published = {base_pop: [(int(p), float(v)) for p, v in zip(pub.percentile, pub.value_usd)]}
        knots = [(p / 100, v, base_pop) for p, v in published[base_pop] if v > 0]
        z = n_all = None
        allr = g[g.population == "all_rostered"]
        if not allr.empty and n and pd.notna(allr.n.iloc[0]) and int(allr.n.iloc[0]) >= n:
            n_all = int(allr.n.iloc[0])
            z = 1 - n / n_all
            pa = allr.dropna(subset=["value_usd"]).sort_values("percentile")
            published["all_rostered"] = [(int(p), float(v)) for p, v in zip(pa.percentile, pa.value_usd)]
            knots += [((p / 100 - z) / (1 - z), v, "all_rostered")
                      for p, v in published["all_rostered"] if v > 0 and p / 100 > z + ZERO_TOL]
        out.append(Curve(k, base_pop, n, _monotone(knots), published, z, n_all, method,
                         top_mults.get((k.report, k.sport, k.cohort), 1.0)))
    return out, issues



def calibrated_mults(df: pd.DataFrame) -> dict[tuple[str, str, str], float]:
    """Tail multipliers past the top point, from the triangulation's central case, for the cohorts whose
    totals an outside constraint pins: A4 football revenue share (the cap), football NIL Go (NIL Go's all-sports
    totals), and every non-A4 revenue-share cohort (CAPS's year-one total less the A4 schools). Every other
    cohort keeps the fitted tail."""
    from .triangulate import calibrate, calibrate_non_a4

    cal = calibrate(df)
    central = cal[cal.case == "central"].set_index("report").tail_mult
    out = {}
    if pd.notna(central.get("revenue_share")):
        out[("revenue_share", "Football", "A4")] = float(central["revenue_share"])
    if pd.notna(central.get("nil_go")):
        for cut in ("A4", "Non-A4"):
            out[("nil_go", "Football", cut)] = float(central["nil_go"])
    na = calibrate_non_a4(df)
    m = na[na.case == "central"].tail_mult.iloc[0]
    if pd.notna(m):
        for sport in df[(df.report == "revenue_share") & (df.cohort == "Non-A4")].sport.unique():
            out[("revenue_share", sport, "Non-A4")] = float(m)
    return out


def calibrated_curves(df: pd.DataFrame) -> tuple[list[Curve], list[dict]]:
    """The curves the benchmark answers with: fitted, with the calibrated tails (A4 football, football NIL,
    non-A4 revenue share)."""
    return curves(df, top_mults=calibrated_mults(df))

# ---------------------------------------------------------------- answers

@dataclass
class Benchmark:
    key: CohortKey
    population: str                       # paid | all_rostered | deal_holders
    n: int | None
    amount: float
    low: float | None                     # percentile 0-100; low < high only on a flat stretch
    high: float | None
    bracket: tuple[float, float]          # certain: published percentiles strictly below and above it
    matches: tuple[float, ...]            # published percentiles equal to the amount
    extrapolated: bool
    method: str

    @property
    def percentile(self) -> float | None:
        return None if self.low is None else (self.low + self.high) / 2


def bracket(points: list[tuple[float, float]], amount: float) -> tuple[tuple[float, float], tuple[float, ...]]:
    """((below, above), equal): the nearest published percentiles strictly under and over `amount`
    (0 and 100 past the ends), and those it equals. The amount's percentile is certainly in between."""
    below = max([p for p, v in points if v < amount], default=0.0)
    above = min([p for p, v in points if v > amount], default=100.0)
    return (below, above), tuple(sorted(p for p, v in points if v == amount))


def benchmark(curve: Curve, amount: float) -> list[Benchmark]:
    """Where `amount` sits among the base population, and among everyone rostered when that is known."""
    base_points = [(float(p), v) for p, v in curve.published[curve.population]]
    if curve.fitted:
        q_lo, q_hi = curve.rank(amount)
        low, high = 100 * q_lo, 100 * q_hi
        extra = amount > 0 and (curve.extrapolated(q_lo) or curve.extrapolated(q_hi))
    else:
        low = high = None
        extra = False
    out = [Benchmark(curve.key, curve.population, curve.n, amount, low, high, *bracket(base_points, amount),
                     extra, curve.method if curve.fitted else "bracket_only")]
    if curve.zero_share is not None:
        z = curve.zero_share
        points = [(float(p), v) for p, v in curve.published["all_rostered"]] + \
                 [(100 * (z + (1 - z) * p / 100), v) for p, v in base_points]
        if amount <= 0:
            a_low, a_high = 0.0, 100 * z
        elif low is None:
            a_low = a_high = None
        else:
            a_low, a_high = 100 * z + (1 - z) * low, 100 * z + (1 - z) * high
        out.append(Benchmark(curve.key, "all_rostered", curve.n_all, amount, a_low, a_high, *bracket(points, amount),
                             extra if amount > 0 else False, out[0].method))
    return out


def value_at(curve: Curve, percentile: float, population: str | None = None) -> tuple[float, bool]:
    """(dollars, extrapolated) at a whole-roster or base-population percentile."""
    p = percentile / 100
    if population == "all_rostered":
        z = curve.zero_share
        if p <= z:
            return 0.0, False
        p = (p - z) / (1 - z)
    return float(curve.quantile(p)), curve.extrapolated(p)


def find(all_curves: list[Curve], report: str, sport: str, position: str = "All Positions", cohort: str = "A4",
         gender: str | None = None) -> Curve:
    """The one curve matching the description; raises with the choices when there are none or several."""
    hits = [c for c in all_curves if c.key.report == report and c.key.sport.lower() == sport.lower()
            and c.key.position.lower() == position.lower() and c.key.cohort.lower() == cohort.lower()
            and (gender is None or c.key.gender == gender)]
    if len(hits) == 1:
        return hits[0]
    near = sorted({(c.key.gender, c.key.position, c.key.cohort) for c in all_curves
                   if c.key.report == report and c.key.sport.lower() == sport.lower()})
    raise LookupError(f"{len(hits)} {report} cohorts match {sport} / {position} / {cohort} / {gender or 'any gender'}. "
                      f"Available for {sport}: {near or 'none'}")


# ---------------------------------------------------------------- tables

def fit_frames(cs: list[Curve], payload_sha: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(benchmark_fits rows, benchmark_curves rows) for these curves."""
    fits, rows = [], []
    for c in cs:
        k = c.key
        ident = {"payload_sha256": payload_sha[k.report], "report": k.report, "gender": k.gender, "sport": k.sport,
                 "position": k.position, "cohort": k.cohort, "window_label": k.window_label}
        fits.append({**ident, "population": c.population, "n": c.n, "n_all": c.n_all, "zero_share": c.zero_share,
                     "method": c.method if c.fitted else "bracket_only", "n_knots": len(c.knots),
                     "tail_slope": c.tail_slope, "top_tail_mult": c.top_mult,
                     "knots": json.dumps([[round(q, 6), v, s] for q, v, s in c.knots])})
        if not c.fitted:
            continue
        pops = [c.population] + (["all_rostered"] if c.zero_share is not None else [])
        for pop in pops:
            for p in range(1, 100):
                v, extra = value_at(c, p, pop)
                rows.append({**ident, "population": pop, "percentile": p, "value_usd": round(v, 2), "extrapolated": extra})
    return pd.DataFrame(fits), pd.DataFrame(rows)


def store(con, cs: list[Curve]) -> dict[str, int]:
    """The benchmark tables hold the curves of the latest release of each report; refitting replaces them."""
    shas = dict(con.execute("SELECT DISTINCT report, payload_sha256 FROM csc_latest").fetchall())
    fits, rows = fit_frames(cs, shas)
    con.execute("DELETE FROM benchmark_fits")
    con.execute("DELETE FROM benchmark_curves")
    return {"benchmark_fits": insert_df(con, "benchmark_fits", fits),
            "benchmark_curves": insert_df(con, "benchmark_curves", rows)}


def export(con, path: Path) -> Path:
    """benchmark_curves as one row per cohort and population, p1 to p99, for spreadsheets and calculators."""
    cells = ", ".join(f"max(value_usd) FILTER (WHERE percentile = {p}) AS p{p}" for p in range(1, 100))
    wide = con.execute(f"""
        SELECT c.report, c.gender, c.sport, c.position, c.cohort, c.population,
               f.n, f.n_all, f.zero_share, f.method, {cells}, left(c.payload_sha256, 12) AS release
        FROM benchmark_curves c
        JOIN benchmark_fits f USING (payload_sha256, report, gender, sport, position, cohort, window_label)
        GROUP BY ALL ORDER BY c.report, c.gender, c.sport, c.position, c.cohort, c.population""").df()
    path.parent.mkdir(parents=True, exist_ok=True)
    wide.round({f"p{p}": 0 for p in range(1, 100)}).to_csv(path, index=False)
    return path


# ---------------------------------------------------------------- validation

def _miss(curve: Curve, q: float, v: float) -> float:
    """Percentile points between where the curve puts `v` and where it was published (q)."""
    lo, hi = curve.rank(v)
    return 0.0 if lo - 1e-9 <= q <= hi + 1e-9 else 100 * min(abs(q - lo), abs(q - hi))


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Held-out error of each method, in percentile points of the positive part.

    loo: drop one point, refit on the rest, and see where the dropped amount lands. A dropped end point
    tests the tail ("tail"), any other the interpolation ("interior").
    cross (revenue share): fit on the Without $0 table alone, then place every point the With $0
    table adds. That table never touched the fit, so this is a true out-of-sample test.
    """
    rows = []
    for method in METHODS:
        for c in curves(df, method)[0]:
            ks = c.knots
            if len(ks) >= 3:
                for i, (q, v, _) in enumerate(ks):
                    rest = c.with_knots(ks[:i] + ks[i + 1:])
                    kind = "tail" if i in (0, len(ks) - 1) else "interior"
                    rows.append({"method": method, "report": c.key.report, "test": f"loo_{kind}",
                                 "cohort": c.key.label(), "error": _miss(rest, q, v)})
            paid = [k for k in ks if k[2] == "paid"]
            added = [k for k in ks if k[2] == "all_rostered"]
            if added and len(paid) >= 2:
                fit = c.with_knots(paid)
                for q, v, _ in added:
                    rows.append({"method": method, "report": c.key.report, "test": "cross",
                                 "cohort": c.key.label(), "error": _miss(fit, q, v)})
    return pd.DataFrame(rows, columns=["method", "report", "test", "cohort", "error"])


def summarize(errors: pd.DataFrame) -> pd.DataFrame:
    return (errors.groupby(["report", "test", "method"]).error
            .agg(points="count", mean="mean", median="median", p90=lambda e: e.quantile(0.9))
            .reset_index())
