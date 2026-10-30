# Offer benchmark

Answers two questions for any published cohort, one report at a time:

- **Where does an amount sit?** "$150,000 of revenue share for an A4 linebacker" is the 59th percentile
  of paid A4 linebackers and the 70th of all rostered ones.
- **What does a percentile pay?** The 80th percentile of paid A4 quarterbacks is about $882,000.

```bash
nil benchmark --sport Football --position Linebacker --cohort A4 --revenue-share 150000 --nil 40000
nil curve --sport Football --position Quarterback --cohort A4            # --report nil_go for NIL
nil query "SELECT * FROM benchmark_curves WHERE sport = 'Football' AND percentile = 80"
```

Every answer has three parts:

| | Meaning |
|---|---|
| **percentile** | The curve's estimate. It is a range when the amount sits where many athletes got exactly that amount, and is marked *extrapolated* past the published 10th–90th. |
| **published percentiles** | What holds with no model: the published percentiles strictly below and above the amount, or the ones it equals. |
| **n** | The cohort size behind it. |

Revenue share and NIL amounts are read separately, each against its own report. They are never added
or compared. An NIL amount is the full contract value of deals cleared in the window, not a yearly
figure.

## The curve

A cohort publishes up to five points: the 90th, 75th, 50th, 25th and 10th percentiles. The curve is a
quantile function through them, Q(q) = exp(g(z)), where z is the normal score of q and g is
non-decreasing.

- **Between published points**, g is linear in (normal score, log dollars). Read on that scale, a
  lognormal is a straight line, so the interpolation bends only where the data does.
- **Beyond them**, g continues with the slope of a least-squares lognormal fit to all the points
  (at least 0.05), and the answer is flagged as extrapolated.
- **Flat stretches are kept.** When neighbouring percentiles are equal, many athletes got that exact
  amount. For example, Non-A4 running backs with an NIL deal have $1,500 at the 10th, 25th and 50th.
  An amount there gets a range ("10th to 50th"), not an invented point.

**Revenue share uses both tables.** The "With $0" and "Without $0" tables are one distribution. The
zero share is z = 1 − n_paid / n_all, so the all-rostered percentile p (above z) is the paid
percentile q = (p − z) / (1 − z). Those points join the paid curve: for football, up to eight points
instead of five. The all-rostered curve is then z of zeros followed by the paid curve. If an added
point disagrees with a published paid point (from rounding), the published point wins.

**Small cohorts get brackets only.** A cohort with fewer than two published amounts gets no curve,
only the published bracket. On the first release, 67 of 100 NIL cohorts and 75 of 92 revenue-share
cohorts have a curve.

## Validation (release of 2026-10-30)

Two tests, both measured in percentile points between where the curve puts a held-out amount and
where it was published:

- **Cross-table (revenue share).** Fit the curve to the "Without $0" table alone, then place every
  amount from the "With $0" table. That table never touched the fit, so this is a genuine
  out-of-sample test: 106 points.
- **Leave one out.** Drop each published point in turn and refit on the rest. Dropping an end point
  tests the tail; any other tests interpolation.

| Test | linear | PCHIP | lognormal |
|---|---|---|---|
| Revenue share, cross-table (106 points) | **1.87** | 1.90 | 3.35 |
| Revenue share, leave one out, interior (271) | **3.38** | 3.42 | 5.22 |
| NIL Go, leave one out, interior (157) | **7.36** | 7.80 | 8.97 |
| Revenue share, leave one out, tail (146) | 8.23 | 8.23 | 10.45 |
| NIL Go, leave one out, tail (134) | 7.80 | 7.80 | 8.57 |

Mean miss in percentile points (lower is better).

**What this says:**
- Linear and PCHIP are effectively tied, and linear is simpler, so it is the default. A single
  lognormal per cohort is clearly worse: pay is not lognormal within a cohort.
- Placing the With $0 values within about 2 percentile points supports both the curve and the
  zero-share identity.
- NIL errors are larger because NIL cohorts have only five points, and many have the $1,500 flat
  stretch next to a long upper tail.
- Tails are rough (around 8 points of miss, worst cases about 25), which is why anything past the
  published range is flagged.

Every release report re-runs this table, so a release where another method wins will show it.

## Limits

- A benchmark is only as current as the release, and football revenue share counts performance
  incentives as payable until the season ends.
- Cohorts are position × A4 / Non-A4 (or conference for basketball). There is no school, class, or
  starter-status dimension. A starting A4 quarterback is benchmarked against every paid A4 quarterback.
- Revenue share is rounded to $500, so the low end of small cohorts is coarse.
