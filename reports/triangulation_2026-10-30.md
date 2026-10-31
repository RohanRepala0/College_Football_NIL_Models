# Triangulation, release 2026-10-30

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

- Revenue share: A4 football spending per program = football's share of the calendar-2026 cap ($21.04M, the average of the 2025-26 and 2026-27 caps). Football's share is assumed to be 75%, tested from 60% to 90%.
- NIL Go: football's cleared value, Jan 1 to Sep 30, 2026, is a share of all sports' cleared value. January to August is published ($455.28M); September is assumed to match the July-August pace ($113.6M). Football's share is assumed to be 55%, tested from 40% to 75%.

The multiplier is solved so the football total matches the target. "Below a flat tail" means even paying everyone in the top 10% exactly the published 90th overshoots, so that assumption is ruled out.

| report        | assumption   | football share   | target    | flat-tail total   | fitted-tail total   | tail multiplier   |
|:--------------|:-------------|:-----------------|:----------|:------------------|:--------------------|:------------------|
| revenue_share | central      | 75%              | $1,073.0M | $1,035.1M         | $1,384.2M           | x0.20             |
| revenue_share | low          | 60%              | $858.4M   | $1,035.1M         | $1,384.2M           | below a flat tail |
| revenue_share | high         | 90%              | $1,287.6M | $1,035.1M         | $1,384.2M           | x0.84             |
| nil_go        | central      | 55%              | $312.9M   | $233.9M           | $669.8M             | x0.48             |
| nil_go        | low          | 40%              | $227.6M   | $233.9M           | $669.8M             | below a flat tail |
| nil_go        | high         | 75%              | $426.7M   | $233.9M           | $669.8M             | x0.75             |

## What calibration changes at the top

Dollars past the published 90th, A4 football, at the central assumption. The fitted tail is what the benchmark extrapolates with today.

| report        | A4 position       | published 90th   | 95th fitted   | 95th calibrated   | 99th fitted   | 99th calibrated   |
|:--------------|:------------------|:-----------------|:--------------|:------------------|:--------------|:------------------|
| revenue_share | Quarterback       | $1.6M            | $3.0M         | $1.8M             | $9.4M         | $2.3M             |
| revenue_share | Wide Receiver     | $0.5M            | $0.7M         | $0.5M             | $1.6M         | $0.6M             |
| revenue_share | Offensive Lineman | $0.5M            | $0.8M         | $0.6M             | $2.1M         | $0.7M             |
| revenue_share | Defensive Lineman | $0.5M            | $0.8M         | $0.6M             | $1.8M         | $0.7M             |
| nil_go        | Quarterback       | $1.0M            | $2.5M         | $1.5M             | $13.6M        | $3.5M             |
| nil_go        | Wide Receiver     | $0.2M            | $0.5M         | $0.4M             | $2.2M         | $0.7M             |
| nil_go        | Offensive Lineman | $0.2M            | $0.5M         | $0.3M             | $2.1M         | $0.6M             |
| nil_go        | Defensive Lineman | $0.2M            | $0.5M         | $0.3M             | $2.3M         | $0.7M             |
