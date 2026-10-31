"""Credibility checks for reported pay claims, against the CSC distributions.

A claim says one athlete is paid an amount. The CSC can't confirm a single claim, but its distributions
bound how many athletes can be paid that much, which catches inflated reporting in aggregate:

- `tail_counts` (no model): at most about n x (1 - p) athletes are paid more than the published p-th
  percentile. More distinct claimed athletes above it than that means at least the excess overstate pay,
  or count money this report doesn't (the other report, several years, unearned incentives).
- `order_test` (model): the k-th largest claim can't exceed the k-th largest pay in the cohort. Under the
  benchmark curve, with the heaviest football tail the outside totals still allow (the triangulation's
  high case), so the test leans toward believing claims, that pay's quantile is U(n-k+1) ~ Beta(n-k+1, k).
  A claim it makes very unlikely is flagged.
- `source_bias` (truth discovery): where several sources report the same athlete, log(claim) = athlete
  level + source bias + noise, fitted by least squares, gives each source's bias relative to the others,
  or to school records when there are any.

A claim is read against one report only. A "package" mixing revenue share and NIL, or several of
either, is kept in the file and never placed on a curve.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta, norm

from . import benchmark as bm
from . import triangulate as tri

CLAIM_COLUMNS = ["claim_id", "player", "school", "sport", "gender", "position", "cohort", "report", "amount",
                 "years", "source_type", "source", "url", "date"]
REPORTS = {"revenue_share", "nil_go", "package"}
SOURCE_TYPES = {"school_record", "reporter", "agent", "athlete", "other"}
ALPHA = 0.05
KEY = ["report", "gender", "sport", "position", "cohort"]


def load(path: Path) -> tuple[pd.DataFrame, list[dict]]:
    """Claims from a CSV with `CLAIM_COLUMNS`. Rows that can't be read are reported, not guessed."""
    df = pd.read_csv(path, dtype=str).fillna("")
    missing = [c for c in CLAIM_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    return clean(df)


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["years"] = pd.to_numeric(df["years"], errors="coerce")
    issues = []
    for i, r in df.iterrows():
        why = ("no amount" if not r.amount > 0 else
               f"report {r.report!r} is not one of {sorted(REPORTS)}" if r.report not in REPORTS else
               f"source_type {r.source_type!r} is not one of {sorted(SOURCE_TYPES)}" if r.source_type not in SOURCE_TYPES
               else None)
        if why:
            issues.append({"claim_id": r.claim_id, "issue": why})
    bad = {i["claim_id"] for i in issues}
    return df[~df.claim_id.isin(bad)].reset_index(drop=True), issues


def comparable(row) -> float:
    """The amount on its report's own scale. Football revenue share is a year's payments, so a multi-year
    figure is divided by its years. NIL Go counts full contract value, so an NIL figure is not."""
    if row.report == "revenue_share" and row.years and row.years > 1:
        return row.amount / row.years
    return row.amount


def cdf(curve: bm.Curve, amount: float, tail_mult: float = 1.0) -> float:
    """Share of the cohort's positive part paid at most `amount`, with the tail slope scaled by `tail_mult`.
    Inside the published range it takes the upper end of a flat stretch, which favours the claim."""
    (q0, v0, _), (q1, v1, _) = curve.knots[0], curve.knots[-1]
    s = max(curve.tail_slope * tail_mult, 1e-9)
    if amount > v1:
        return float(norm.cdf(norm.ppf(q1) + math.log(amount / v1) / s))
    if amount < v0:
        return float(norm.cdf(norm.ppf(q0) - math.log(v0 / amount) / s))
    return curve.rank(amount)[1]


def _athletes(group: pd.DataFrame) -> pd.DataFrame:
    """One row per athlete: his largest claim. A claim with no player name counts as its own athlete."""
    g = group.assign(who=np.where(group.player != "", group.player, "claim:" + group.claim_id))
    return g.sort_values("value", ascending=False).drop_duplicates("who")


def place(claims: pd.DataFrame, curves: list[bm.Curve]) -> pd.DataFrame:
    """Each claim's place in its cohort: percentile range on the curve, and whether that is past the
    published range. `placed` is False for a package, or a cohort with no curve."""
    by_key = {(c.key.report, c.key.gender, c.key.sport, c.key.position, c.key.cohort): c for c in curves}
    rows = []
    for r in claims.itertuples(index=False):
        value = comparable(r)
        out = {**r._asdict(), "value": value, "placed": False, "pct_low": np.nan, "pct_high": np.nan,
               "extrapolated": False, "n": np.nan, "why": ""}
        c = by_key.get((r.report, r.gender, r.sport, r.position, r.cohort))
        if r.report == "package":
            out["why"] = "package: mixes reports or years"
        elif c is None:
            out["why"] = "no published cohort"
        elif not c.fitted:
            out.update(n=c.n, why="cohort too small for a curve")
        else:
            lo, hi = c.rank(value)
            out.update(placed=True, pct_low=100 * lo, pct_high=100 * hi, n=c.n,
                       extrapolated=c.extrapolated(lo) or c.extrapolated(hi))
        rows.append(out)
    return pd.DataFrame(rows)


def tail_counts(placed: pd.DataFrame, published: pd.DataFrame) -> pd.DataFrame:
    """Model-free: distinct claimed athletes above each published percentile against the most the cohort
    can have there. `published` is csc_percentiles rows (for example csc_latest)."""
    rows = []
    claims = placed[placed.report != "package"]
    for key, group in claims.groupby(KEY):
        report, gender, sport, position, cohort = key
        base = published[(published.report == report) & (published.gender == gender) & (published.sport == sport)
                         & (published.position == position) & (published.cohort == cohort)
                         & (published.population == bm.BASE[report])].dropna(subset=["value_usd"])
        if base.empty or pd.isna(base.n.iloc[0]):
            continue
        n = int(base.n.iloc[0])
        athletes = _athletes(group)
        for p, v in zip(base.percentile, base.value_usd):
            above = int((athletes.value > v).sum())
            most = math.ceil(n * (1 - p / 100)) + 1      # +1 for the CSC's "approximately"
            rows.append({"report": report, "position": position, "cohort": cohort, "n": n, "percentile": int(p),
                         "threshold": v, "claimed_above": above, "most_possible": most,
                         "excess": max(0, above - most)})
    return pd.DataFrame(rows, columns=["report", "position", "cohort", "n", "percentile", "threshold",
                                       "claimed_above", "most_possible", "excess"])


def lenient_tails(published: pd.DataFrame) -> dict[str, float]:
    """Per report, the heaviest football tail the outside totals allow: the triangulation's high case."""
    cal = tri.calibrate(published)
    high = cal[cal.case == "high"].set_index("report").tail_mult
    return {r: (1.0 if pd.isna(m) else float(m)) for r, m in high.items()}


def order_test(placed: pd.DataFrame, curves: list[bm.Curve], tails: dict[str, float] | None = None,
               alpha: float = ALPHA) -> pd.DataFrame:
    """Model: within a cohort, sort claimed athletes by amount; the k-th largest is flagged when even the
    cohort's k-th best-paid athlete is unlikely (p < alpha) to be paid that much. `tails` gives football's
    tail multiplier per report (see `lenient_tails`); other sports use the fitted tail."""
    by_key = {(c.key.report, c.key.gender, c.key.sport, c.key.position, c.key.cohort): c for c in curves}
    tails = tails or {}
    rows = []
    for key, group in placed[placed.placed].groupby(KEY):
        c = by_key[key]
        n = int(c.n)
        mult = tails.get(key[0], 1.0) if key[2] == "Football" else 1.0
        for k, r in enumerate(_athletes(group).itertuples(index=False), 1):
            if k > n:
                break
            f = cdf(c, r.value, mult)
            p = float(beta.sf(f, n - k + 1, k))     # P(k-th largest pay >= the claim)
            rows.append({"claim_id": r.claim_id, "source": r.source, "position": key[3], "cohort": key[4],
                         "value": r.value, "k": k, "n": n, "p_value": p, "flagged": p < alpha})
    return pd.DataFrame(rows, columns=["claim_id", "source", "position", "cohort", "value", "k", "n", "p_value", "flagged"])


def source_bias(claims: pd.DataFrame) -> pd.DataFrame:
    """Each source's multiplicative bias, from athletes claimed by more than one source in one report.
    Anchored to school records when any overlap, otherwise centred so the biases average zero. Sources
    that share no athlete with another source can't be compared and are left out."""
    d = claims[(claims.player != "") & (claims.report != "package")].copy()
    d["value"] = [comparable(r) for r in d.itertuples(index=False)]
    d["athlete"] = d.report + "|" + d.player
    multi = d.groupby("athlete").source.transform("nunique") > 1
    d = d[multi & (d.value > 0)]
    if d.empty:
        return pd.DataFrame(columns=["source", "bias", "claims", "athletes", "se"])
    athletes, sources = sorted(d.athlete.unique()), sorted(d.source.unique())
    ai, si = {a: i for i, a in enumerate(athletes)}, {s: i for i, s in enumerate(sources)}
    A = np.zeros((len(d), len(athletes) + len(sources)))
    for row, r in enumerate(d.itertuples(index=False)):
        A[row, ai[r.athlete]] = 1
        A[row, len(athletes) + si[r.source]] = 1
    y = np.log(d.value.to_numpy())
    anchors = sorted(d[d.source_type == "school_record"].source.unique())
    con = np.zeros(len(athletes) + len(sources))
    for s in anchors or sources:                      # school records at zero, or all biases summing to zero
        con[len(athletes) + si[s]] = 1
    w = 1e3
    sol, *_ = np.linalg.lstsq(np.vstack([A, w * con]), np.append(y, 0.0), rcond=None)
    resid = y - A @ sol
    dof = max(1, len(d) - np.linalg.matrix_rank(A))
    sigma = float(np.sqrt(resid @ resid / dof))
    out = []
    for s in sources:
        b = sol[len(athletes) + si[s]]
        m = d.source == s
        out.append({"source": s, "bias": math.exp(b) - 1, "claims": int(m.sum()),
                    "athletes": int(d[m].athlete.nunique()), "se": sigma / math.sqrt(max(1, int(m.sum())))})
    return pd.DataFrame(out)


def summary(placed: pd.DataFrame, order: pd.DataFrame, bias: pd.DataFrame) -> pd.DataFrame:
    """One row per source: claims, how many could be placed, how many the order test flags, and its bias."""
    rows = []
    for s, g in placed.groupby("source"):
        o = order[order.source == s]
        b = bias[bias.source == s]
        rows.append({"source": s, "source_type": g.source_type.iloc[0], "claims": len(g), "placed": int(g.placed.sum()),
                     "flagged": int(o.flagged.sum()), "flagged_share": (o.flagged.mean() if len(o) else np.nan),
                     "bias": (b.bias.iloc[0] if len(b) else np.nan)})
    return pd.DataFrame(rows)
