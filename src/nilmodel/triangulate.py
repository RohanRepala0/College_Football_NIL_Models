"""What the CSC percentiles imply about totals, with and without a model.

A cohort's published percentiles bound its mean pay with no model at all. The share of athletes
between two published percentiles is known, and each is paid at least the lower of the two values,
so the sum of share x lower value is a hard floor (partial identification). There is no matching
ceiling, because nothing caps the top 10%. The benchmark curve gives a point estimate, and tail
scenarios show how much of it rests on the extrapolated top.

Each report is totalled on its own; revenue share and NIL Go are never added together.
"""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import benchmark as bm

# CSC participants in the ACC, Big Ten, Big 12 and SEC (69), less Johns Hopkins (Big Ten for lacrosse
# only). Notre Dame is listed in the ACC and counted. Checked against the participant list 2026-10-30.
A4_FOOTBALL_PROGRAMS = 68
# Revenue-share caps per school, from the CSC's Oct 1, 2026 release. Football's window is calendar 2026,
# half in each cap year, so the per-school comparison uses their average.
CAP_2025_26 = 20_500_000
CAP_2026_27 = 21_580_000
CAP_CALENDAR_2026 = (CAP_2025_26 + CAP_2026_27) / 2
TAIL_SCENARIOS = {"light": 0.5, "fitted": 1.0, "heavy": 1.5}   # multipliers on the upper tail's slope

# Outside totals that each report's football total must respect. Each is (central, low, high), and every
# assumption is named in `constraint_notes()`, which the report prints beside the results.
#
# Revenue share: all 68 A4 programs pay football out of one cap that covers every sport. Football's share
# of it is an assumption (reported expectations cluster near 75%).
FOOTBALL_CAP_SHARE = (0.75, 0.60, 0.90)
# NIL Go: football deal holders can't have more cleared value than all sports together, over football's NIL Go
# window (Jan 1 to Sep 30, 2026). All-sports cleared value comes from the CSC's NIL Data Reports as captured in
# data/csc/nil_data_periods.csv (`nil_data`); a period that straddles the window counts in proportion to its days.
# Without the capture, the totals published through August plus an assumed September are used.
NIL_GO_WINDOW = (date(2026, 1, 1), date(2026, 9, 30))
NIL_ALL_SPORTS_JAN_AUG_2026 = 39.29e6 + 75.85e6 + 112.89e6 + 227.25e6     # fallback only
NIL_ALL_SPORTS_SEP_2026 = 227.25e6 / 2                                   # fallback only
NIL_FOOTBALL_SHARE = (0.55, 0.40, 0.75)


def nil_go_cleared(start: date = NIL_GO_WINDOW[0], end: date = NIL_GO_WINDOW[1],
                   path: Path | None = None) -> tuple[float, str]:
    """(all-sports NIL Go value cleared from `start` to `end`, how it was worked out)."""
    from .nil_data import PERIODS_CSV

    path = path or PERIODS_CSV
    if not path.exists():
        return NIL_ALL_SPORTS_JAN_AUG_2026 + NIL_ALL_SPORTS_SEP_2026, (
            f"January to August as published (${NIL_ALL_SPORTS_JAN_AUG_2026 / 1e6:.2f}M), September assumed at the "
            f"July-August pace (${NIL_ALL_SPORTS_SEP_2026 / 1e6:.1f}M)")
    p = pd.read_csv(path, parse_dates=["period_start", "period_end"])
    total, partial = 0.0, []
    for r in p.itertuples(index=False):
        a, b = max(r.period_start.date(), start), min(r.period_end.date(), end)
        if a > b:
            continue
        days, used = (r.period_end - r.period_start).days + 1, (b - a).days + 1
        total += r.cleared_value * used / days
        if used < days:
            partial.append(f"{used} of the {days} days of {r.period} (${r.cleared_value * used / days / 1e6:.1f}M)")
    as_of = p.as_of.iloc[0] if "as_of" in p and len(p) else "?"
    note = f"from the CSC's NIL Data Reports (current as of {as_of}), ${total / 1e6:.2f}M"
    return total, note + (f", counting {'; '.join(partial)}" if partial else "")


def constraint_notes() -> list[str]:
    nil_total, how = nil_go_cleared()
    return [
        "Revenue share: A4 football spending per program = football's share of the calendar-2026 cap "
        f"(${CAP_CALENDAR_2026 / 1e6:.2f}M, the average of the 2025-26 and 2026-27 caps). Football's share is assumed "
        f"to be {FOOTBALL_CAP_SHARE[0]:.0%}, tested from {FOOTBALL_CAP_SHARE[1]:.0%} to {FOOTBALL_CAP_SHARE[2]:.0%}.",
        f"NIL Go: football's cleared value, Jan 1 to Sep 30, 2026, is a share of all sports' cleared value: {how}. "
        f"Football's share is assumed to be {NIL_FOOTBALL_SHARE[0]:.0%}, tested from {NIL_FOOTBALL_SHARE[1]:.0%} to "
        f"{NIL_FOOTBALL_SHARE[2]:.0%}.",
    ]


_trapezoid = getattr(np, "trapezoid", None) or np.trapz


def floor_mean(points: list[tuple[float, float]]) -> float:
    """Model-free lower bound on mean pay from published (percentile, dollars) points."""
    total, prev_p, prev_v = 0.0, 0.0, 0.0
    for p, v in sorted(points):
        total += (p - prev_p) / 100 * prev_v
        prev_p, prev_v = p, v
    return total + (100 - prev_p) / 100 * prev_v


def curve_mean(curve: bm.Curve, tail_mult: float = 1.0, grid: int = 4001) -> float:
    """Mean of the curve's positive part. Between the published ends it integrates the curve; beyond
    them the tails are lognormal, the upper with the curve's slope times `tail_mult` and the lower with
    the fitted slope, both integrated exactly."""
    (q0, v0, _), (q1, v1, _) = curve.knots[0], curve.knots[-1]
    s, s0 = curve.tail_slope * tail_mult, curve.tail_slope
    z0, z1 = norm.ppf(q0), norm.ppf(q1)
    upper = v1 * math.exp(-s * z1 + s * s / 2) * norm.sf(z1 - s)
    lower = v0 * math.exp(-s0 * z0 + s0 * s0 / 2) * norm.cdf(z0 - s0)
    q = np.linspace(q0, q1, grid)
    return lower + float(_trapezoid(curve.quantile(q), q)) + upper


def cohort_totals(df: pd.DataFrame, sport: str = "Football", gender: str = "men") -> pd.DataFrame:
    """Total pay per cohort of one sport: the hard floor and the estimate under each tail scenario.
    Totals are over the base population (paid athletes, or athletes with a deal); the unpaid add $0."""
    rows = []
    for c in bm.curves(df)[0]:
        k = c.key
        if k.sport != sport or k.gender != gender or c.n is None:
            continue
        points = [(p, v) for p, v in c.published[c.population] if v > 0]
        row = {"report": k.report, "cohort": k.cohort, "position": k.position, "athletes": c.n,
               "rostered": c.n_all, "floor": c.n * floor_mean(points)}
        for name, mult in TAIL_SCENARIOS.items():
            row[name] = c.n * curve_mean(c, mult) if c.fitted else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def roll_up(totals: pd.DataFrame) -> pd.DataFrame:
    """Totals per report and cohort across positions. A position without a curve adds its floor to
    every scenario, which keeps the estimates conservative."""
    t = totals.copy()
    for name in TAIL_SCENARIOS:
        t[name] = t[name].fillna(t["floor"])
    return (t.groupby(["report", "cohort"], as_index=False)[["athletes", "rostered", "floor", *TAIL_SCENARIOS]]
            .sum(min_count=1))


def per_program(rolled: pd.DataFrame, programs: int = A4_FOOTBALL_PROGRAMS) -> dict:
    """A4 football revenue share per program, and as a share of the calendar-2026 cap."""
    r = rolled[(rolled.report == "revenue_share") & (rolled.cohort == "A4")].iloc[0]
    out = {"programs": programs, "rostered_per_program": r.rostered / programs}
    for col in ("floor", *TAIL_SCENARIOS):
        out[col] = r[col] / programs
        out[f"{col}_cap_share"] = r[col] / programs / CAP_CALENDAR_2026
    return out


class _Part:
    """One cohort's contribution to a total: the interior integral is fixed, only the tails move."""

    def __init__(self, curve: bm.Curve, grid: int = 4001):
        self.n = curve.n
        if curve.fitted:
            (self.q0, self.v0, _), (self.q1, self.v1, _) = curve.knots[0], curve.knots[-1]
            self.z0, self.z1, self.slope = norm.ppf(self.q0), norm.ppf(self.q1), curve.tail_slope
            q = np.linspace(self.q0, self.q1, grid)
            self.interior, self.floor = float(_trapezoid(curve.quantile(q), q)), None
        else:
            self.floor = floor_mean([(p, v) for p, v in curve.published[curve.population] if v > 0])

    def mean(self, tail_mult: float) -> float:
        if self.floor is not None:
            return self.floor
        s, s0 = self.slope * tail_mult, self.slope
        upper = self.v1 * math.exp(-s * self.z1 + s * s / 2) * norm.sf(self.z1 - s)
        lower = self.v0 * math.exp(-s0 * self.z0 + s0 * s0 / 2) * norm.cdf(self.z0 - s0)
        return lower + self.interior + upper


def football_parts(df: pd.DataFrame, report: str, cohorts: tuple[str, ...]) -> list[_Part]:
    """A position without a curve counts at its floor."""
    return [_Part(c) for c in bm.curves(df)[0]
            if c.key.report == report and c.key.sport == "Football" and c.key.gender == "men"
            and c.key.cohort in cohorts and c.n is not None]


def parts_total(parts: list[_Part], tail_mult: float) -> float:
    return sum(p.n * p.mean(tail_mult) for p in parts)


def solve_tail(parts: list[_Part], target: float, hi: float = 3.0) -> float | None:
    """The tail multiplier at which the total equals `target`, by bisection (the total rises with the
    multiplier). None when even a flat tail (0) overshoots, or the steepest tried falls short."""
    if parts_total(parts, 0.0) > target or parts_total(parts, hi) < target:
        return None
    lo = 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if parts_total(parts, mid) < target else (lo, mid)
    return (lo + hi) / 2


def calibrate(df: pd.DataFrame) -> pd.DataFrame:
    """Tail multipliers that make each report's football total match its outside constraint, at the
    central assumption and at each end of its range."""
    specs = [("revenue_share", ("A4",), A4_FOOTBALL_PROGRAMS * CAP_CALENDAR_2026, FOOTBALL_CAP_SHARE),
             ("nil_go", ("A4", "Non-A4"), nil_go_cleared()[0], NIL_FOOTBALL_SHARE)]
    rows = []
    for report, cohorts, base, (mid, low, high) in specs:
        parts = football_parts(df, report, cohorts)
        for case, share in (("central", mid), ("low", low), ("high", high)):
            rows.append({"report": report, "case": case, "assumed_share": share, "target": base * share,
                         "tail_mult": solve_tail(parts, base * share),
                         "fitted_total": parts_total(parts, 1.0), "flat_tail_total": parts_total(parts, 0.0)})
    return pd.DataFrame(rows)


def tail_quantile(curve: bm.Curve, q, tail_mult: float = 1.0) -> np.ndarray:
    """Dollars at quantiles `q` (0-1) of the positive part, with the upper tail's slope scaled by `tail_mult`."""
    q = np.asarray(q, float)
    (q0, v0, _), (q1, v1, _) = curve.knots[0], curve.knots[-1]
    z = norm.ppf(q)
    out = curve.quantile(np.clip(q, q0, q1))
    out = np.where(q > q1, v1 * np.exp(curve.tail_slope * tail_mult * (z - norm.ppf(q1))), out)
    return np.where(q < q0, v0 * np.exp(curve.tail_slope * (z - norm.ppf(q0))), out)


def tail_value(curve: bm.Curve, percentile: float, tail_mult: float) -> float:
    """Dollars at a percentile of the positive part, with the tail slope scaled by `tail_mult`."""
    return float(tail_quantile(curve, percentile / 100, tail_mult))
