# Triangulation, release 2026-11-09

What the published percentiles imply about football totals, first with no model and then with the benchmark curves. Revenue share and NIL Go are totalled separately and never added together. Method: [`docs/ESTIMATION.md`](../docs/ESTIMATION.md).

## Hard floors

Each athlete between two published percentiles is paid at least the lower of the two, so share x lower value, summed, is a floor that needs no model. Nothing caps the top 10%, so there is no matching ceiling.

- A4 football revenue share is at least **$11.7M per program** across the 68 A4 programs, **56% of the calendar-2026 cap** ($21.04M, which also has to cover every other sport).
- The CSC counts 114 rostered football players per A4 program, above the 105-player roster limit: everyone on a 2026 roster at any point in the calendar year is counted, so turnover adds names.

## Totals under each tail

Between published percentiles the curve is the benchmark's; past the 10th and 90th it is lognormal with the fitted slope times the multiplier.

| report        | group   |   athletes | floor (no model)   | light tail (x0.5)   | fitted tail (x1.0)   | heavy tail (x1.5)   |
|:--------------|:--------|-----------:|:-------------------|:--------------------|:---------------------|:--------------------|
| nil_go        | A4      |       3917 | $167.8M            | $313.5M             | $665.0M              | $3,994.8M           |
| nil_go        | Non-A4  |       2208 | $3.7M              | $4.6M               | $4.8M                | $5.2M               |
| revenue_share | A4      |       5817 | $797.1M            | $1,151.3M           | $1,384.2M            | $1,972.8M           |
| revenue_share | Non-A4  |       5502 | $126.7M            | $197.5M             | $261.3M              | $446.9M             |

Under the fitted tail, A4 football alone would take 97% of the cap, and under the heavy tail 138%, which is impossible.

## Tails calibrated to outside totals

- Revenue share: A4 football spending per program = football's share of the calendar-2026 cap ($21.04M, the average of the 2025-26 and 2026-27 caps). Football's share is assumed to be 75%, tested from 60% to 88% (the assumed 90% is above what CAPS's year-one totals allow).
- NIL Go: football's cleared value, Jan 1 to Sep 30, 2026, is a share of all sports' cleared value: from the CSC's NIL Data Reports (current as of 2026-11-01), $550.01M, counting 30 of the 61 days of Sept. 1 – Oct. 31, 2026 ($94.7M). Football's share is assumed to be 55%, tested from 40% to 75%.

The multiplier is solved so the football total matches the target. "Below a flat tail" means even paying everyone in the top 10% exactly the published 90th overshoots, so that assumption is ruled out.

| report        | assumption   | football share   | target    | flat-tail total   | fitted-tail total   | tail multiplier   |
|:--------------|:-------------|:-----------------|:----------|:------------------|:--------------------|:------------------|
| revenue_share | central      | 75%              | $1,073.0M | $1,035.1M         | $1,384.2M           | x0.20             |
| revenue_share | low          | 60%              | $858.4M   | $1,035.1M         | $1,384.2M           | below a flat tail |
| revenue_share | high         | 88%              | $1,258.8M | $1,035.1M         | $1,384.2M           | x0.78             |
| nil_go        | central      | 55%              | $302.5M   | $233.9M           | $669.8M             | x0.44             |
| nil_go        | low          | 40%              | $220.0M   | $233.9M           | $669.8M             | below a flat tail |
| nil_go        | high         | 75%              | $412.5M   | $233.9M           | $669.8M             | x0.73             |

## Checked against what schools actually paid

CAPS recorded [$1,770.5M in revenue-share payments](https://www.collegesportscommission.org/college-sports-commission-tracks-1-8-billion-in-payments-to-student-athletes-during-first-year-of-revenue-sharing/) in the first cap year (July 1, 2025 to June 30, 2026), to 34,915 athletes at 307 schools; 68 schools paid the cap or came within 5% of it. The published cohorts, by group. Most sports' window is that cap year; basketball's ends April 6, 2026; football's is calendar 2026. Estimates put A4 football at its assumed share of the 2025-26 cap (the cap-year figure), the non-A4 tails as calibrated below, and fitted tails elsewhere.

| group        |        |   paid athletes | floor (no model)   | estimate   |
|:-------------|:-------|----------------:|:-------------------|:-----------|
| Other sports | A4     |           3,941 | $24.1M             | $70.2M     |
| Other sports | Non-A4 |           3,078 | $11.5M             | $16.3M     |
| Basketball   | A4     |           1,237 | $143.4M            | $246.4M    |
| Basketball   | Non-A4 |           3,771 | $130.1M            | $203.5M    |
| Football     | A4     |           5,817 | $797.1M            | $1,045.5M  |
| Football     | Non-A4 |           5,502 | $126.7M            | $191.6M    |

- **Floors:** $1,232.9M, safely under CAPS's $1,770.5M. The published cohorts hold 23,346 paid athletes against CAPS's 34,915 (CAPS counts each athlete once, and football's window differs, so the counts don't compare exactly).
- **With fitted tails outside A4 football** the published cohorts would total $1,934.6M, more than schools paid. With the non-A4 tails calibrated they total $1,773.4M, against CAPS's $1,770.5M.
- **Football's share of the A4 cap:** A4 schools can pay at most $1,394.0M (68 x the 2025-26 cap), and their other sports were paid at least $167.5M, so football can take at most **88%**. The tail calibration's high case is held there. With the published sports' estimates ($316.6M) football's share would be about 77%, and less once the unpublished sports are counted, which fits the assumed 75%.

### Non-A4 tails

What CAPS recorded, less the A4 schools' spending, is what every non-A4 cohort can sum to. The 68 schools at the cap or within 5% of it are taken to be the 68 A4 programs. Sports too small to publish get no allowance, so the tails are thinned only as far as the total forces. One multiplier on the fitted slope past the 90th covers every non-A4 cohort (football, basketball and the other sports); the offer check uses the central case.

| case     | A4 schools pay    | left for non-A4   | flat-tail total   | fitted-tail total   | tail multiplier   |
|:---------|:------------------|:------------------|:------------------|:--------------------|:------------------|
| central  | 97.5% of the cap  | $411.3M           | $360.8M           | $572.5M             | x0.42             |
| generous | 95.0% of the cap  | $446.2M           | $360.8M           | $572.5M             | x0.61             |
| strict   | 100.0% of the cap | $376.5M           | $360.8M           | $572.5M             | x0.16             |

## What calibration changes at the top

Dollars past the published 90th, A4 football, at the central assumption. The fitted tail is what the benchmark extrapolates with today.

| report        | A4 position       | published 90th   | 95th fitted   | 95th calibrated   | 99th fitted   | 99th calibrated   |
|:--------------|:------------------|:-----------------|:--------------|:------------------|:--------------|:------------------|
| revenue_share | Quarterback       | $1.6M            | $3.0M         | $1.8M             | $9.4M         | $2.3M             |
| revenue_share | Wide Receiver     | $0.5M            | $0.7M         | $0.5M             | $1.6M         | $0.6M             |
| revenue_share | Offensive Lineman | $0.5M            | $0.8M         | $0.6M             | $2.1M         | $0.7M             |
| revenue_share | Defensive Lineman | $0.5M            | $0.8M         | $0.6M             | $1.8M         | $0.7M             |
| nil_go        | Quarterback       | $1.0M            | $2.5M         | $1.5M             | $13.6M        | $3.2M             |
| nil_go        | Wide Receiver     | $0.2M            | $0.5M         | $0.3M             | $2.2M         | $0.7M             |
| nil_go        | Offensive Lineman | $0.2M            | $0.5M         | $0.3M             | $2.1M         | $0.6M             |
| nil_go        | Defensive Lineman | $0.2M            | $0.5M         | $0.3M             | $2.3M         | $0.6M             |
