# Simulation, release 2026-10-30

Real individual pay is private, so the methods are tested on synthetic markets where it is known. Each market has the CSC's 7,743 rostered A4 football players by position, spread over 68 programs. A player's latent value is talent plus his school's spending effect plus noise, and his true revenue share is his position's quantile at that rank, so every position reproduces the published percentiles, with the tail calibrated to the cap (x0.20). The analyst sees two noisy features, 10 schools' disclosed totals, and claims about the best-paid players from 4 sources with known biases. 3 markets per scenario; method: [`docs/ESTIMATION.md`](../docs/ESTIMATION.md).

## Estimating each player's pay

Rank correlation is between the estimated and true pay rankings within each position. Typical miss is the median factor between estimate and truth (on 1 + pay, so an unpaid player estimated at $0 is exact).

| features        | players           | method                      |   rank correlation | typical miss   | 80% interval covers   |
|:----------------|:------------------|:----------------------------|-------------------:|:---------------|:----------------------|
| strong features | all               | features only               |              0.661 | x2.04          | 92%                   |
| strong features | all               | + claims as training labels |              0.636 | x2.12          | 93%                   |
| strong features | all               | + claims as anchors         |              0.664 | x2.02          | 93%                   |
| strong features | all               | + anchors + school totals   |              0.675 | x1.97          | 93%                   |
| strong features | claimed           | features only               |              0.304 | x1.27          | 28%                   |
| strong features | claimed           | + claims as training labels |              0.406 | x1.10          | 89%                   |
| strong features | claimed           | + claims as anchors         |              0.406 | x1.10          | 89%                   |
| strong features | claimed           | + anchors + school totals   |              0.406 | x1.10          | 89%                   |
| strong features | disclosed schools | features only               |              0.664 | x2.07          | 92%                   |
| strong features | disclosed schools | + claims as training labels |              0.635 | x2.15          | 93%                   |
| strong features | disclosed schools | + claims as anchors         |              0.665 | x2.05          | 93%                   |
| strong features | disclosed schools | + anchors + school totals   |              0.732 | x1.81          | 93%                   |
| strong features | unclaimed         | features only               |              0.650 | x2.07          | 93%                   |
| strong features | unclaimed         | + claims as training labels |              0.621 | x2.16          | 93%                   |
| strong features | unclaimed         | + claims as anchors         |              0.650 | x2.06          | 93%                   |
| strong features | unclaimed         | + anchors + school totals   |              0.662 | x2.02          | 93%                   |
| weak features   | all               | features only               |              0.425 | x3.05          | 86%                   |
| weak features   | all               | + claims as training labels |              0.335 | x3.58          | 91%                   |
| weak features   | all               | + claims as anchors         |              0.437 | x2.97          | 92%                   |
| weak features   | all               | + anchors + school totals   |              0.450 | x2.90          | 92%                   |
| weak features   | claimed           | features only               |              0.136 | x1.99          | 17%                   |
| weak features   | claimed           | + claims as training labels |              0.406 | x1.10          | 89%                   |
| weak features   | claimed           | + claims as anchors         |              0.406 | x1.09          | 89%                   |
| weak features   | claimed           | + anchors + school totals   |              0.406 | x1.09          | 89%                   |
| weak features   | disclosed schools | features only               |              0.427 | x2.95          | 86%                   |
| weak features   | disclosed schools | + claims as training labels |              0.334 | x3.54          | 91%                   |
| weak features   | disclosed schools | + claims as anchors         |              0.435 | x2.91          | 92%                   |
| weak features   | disclosed schools | + anchors + school totals   |              0.511 | x2.65          | 92%                   |
| weak features   | unclaimed         | features only               |              0.415 | x3.08          | 87%                   |
| weak features   | unclaimed         | + claims as training labels |              0.308 | x3.72          | 91%                   |
| weak features   | unclaimed         | + claims as anchors         |              0.415 | x3.07          | 92%                   |
| weak features   | unclaimed         | + anchors + school totals   |              0.427 | x3.00          | 92%                   |

- **Weak features**: features alone rank pay at 0.425. Training on the claims drops that to 0.335; anchoring on them keeps 0.437 and cuts the typical miss for claimed players from x1.99 to x1.09. School totals lift the disclosed schools from 0.435 to 0.511 (all players 0.450).
- **Strong features**: features alone rank pay at 0.661. Training on the claims drops that to 0.636; anchoring on them keeps 0.664 and cuts the typical miss for claimed players from x1.27 to x1.10. School totals lift the disclosed schools from 0.665 to 0.732 (all players 0.675).

## Checking sources

Estimated bias comes from athletes reported by more than one source, anchored to school records. Strong flags fail the order test under the most generous tail the cap allows; moderate flags fail only under the central tail.

| source         | true bias   | estimated bias   | range over markets   |   claims |   strong flags |   moderate flags |
|:---------------|:------------|:-----------------|:---------------------|---------:|---------------:|-----------------:|
| hype_account   | +150%       | +132%            | +119% to +155%       |       75 |              0 |               74 |
| outlet_a       | +30%        | +28%             | +24% to +35%         |      120 |              0 |               76 |
| outlet_b       | 0%          | -2%              | -2% to -1%           |      120 |              0 |               29 |
| school_records | 0%          | 0%               | 0% to 0%             |       75 |              0 |                7 |

## Limits

- The synthetic market is built to match what is published; how pay really depends on talent and school is assumed, and the features' quality is set by the scenario. Real features need the CFBD data.
- Moderate inflation (+30%) is caught through overlapping sources, not by the aggregate tests; those catch only claims far beyond what the distribution allows.
- The intervals cover the truth somewhat more often than 80%, so they are cautious.