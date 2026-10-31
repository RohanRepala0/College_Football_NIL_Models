# Simulation, release 2026-10-30

Real individual pay is private, so the methods are tested on synthetic markets where it is known. Each market has the CSC's 7,743 rostered A4 football players by position, spread over 68 programs. A player's latent value is talent plus his school's spending effect plus noise, and his true revenue share is his position's quantile at that rank, so every position reproduces the published percentiles, with the tail calibrated to the cap (x0.19). The analyst sees two noisy features, 10 schools' disclosed totals, and claims about the best-paid players from 4 sources with known biases. 3 markets per scenario; method: [`docs/ESTIMATION.md`](../docs/ESTIMATION.md).

## Estimating each player's pay

Rank correlation is between the estimated and true pay rankings within each position. Typical miss is the median factor between estimate and truth (on 1 + pay, so an unpaid player estimated at $0 is exact).

| features        | players           | method                      |   rank correlation | typical miss   | 80% interval covers   |
|:----------------|:------------------|:----------------------------|-------------------:|:---------------|:----------------------|
| strong features | all               | features only               |              0.661 | x1.99          | 92%                   |
| strong features | all               | + claims as training labels |              0.619 | x2.12          | 93%                   |
| strong features | all               | + claims as anchors         |              0.664 | x1.97          | 92%                   |
| strong features | all               | + anchors + school totals   |              0.675 | x1.92          | 93%                   |
| strong features | claimed           | features only               |              0.307 | x1.26          | 29%                   |
| strong features | claimed           | + claims as training labels |              0.351 | x1.10          | 87%                   |
| strong features | claimed           | + claims as anchors         |              0.351 | x1.09          | 87%                   |
| strong features | claimed           | + anchors + school totals   |              0.351 | x1.09          | 87%                   |
| strong features | disclosed schools | features only               |              0.664 | x1.99          | 92%                   |
| strong features | disclosed schools | + claims as training labels |              0.614 | x2.13          | 92%                   |
| strong features | disclosed schools | + claims as anchors         |              0.665 | x1.97          | 92%                   |
| strong features | disclosed schools | + anchors + school totals   |              0.732 | x1.78          | 93%                   |
| strong features | unclaimed         | features only               |              0.651 | x2.01          | 93%                   |
| strong features | unclaimed         | + claims as training labels |              0.604 | x2.16          | 93%                   |
| strong features | unclaimed         | + claims as anchors         |              0.651 | x2.01          | 92%                   |
| strong features | unclaimed         | + anchors + school totals   |              0.662 | x1.96          | 93%                   |
| weak features   | all               | features only               |              0.425 | x2.92          | 86%                   |
| weak features   | all               | + claims as training labels |              0.249 | x3.90          | 91%                   |
| weak features   | all               | + claims as anchors         |              0.438 | x2.85          | 91%                   |
| weak features   | all               | + anchors + school totals   |              0.450 | x2.80          | 91%                   |
| weak features   | claimed           | features only               |              0.146 | x1.94          | 18%                   |
| weak features   | claimed           | + claims as training labels |              0.351 | x1.10          | 87%                   |
| weak features   | claimed           | + claims as anchors         |              0.351 | x1.10          | 87%                   |
| weak features   | claimed           | + anchors + school totals   |              0.351 | x1.10          | 87%                   |
| weak features   | disclosed schools | features only               |              0.427 | x2.85          | 86%                   |
| weak features   | disclosed schools | + claims as training labels |              0.245 | x3.99          | 91%                   |
| weak features   | disclosed schools | + claims as anchors         |              0.435 | x2.79          | 92%                   |
| weak features   | disclosed schools | + anchors + school totals   |              0.511 | x2.54          | 92%                   |
| weak features   | unclaimed         | features only               |              0.415 | x2.95          | 87%                   |
| weak features   | unclaimed         | + claims as training labels |              0.218 | x4.01          | 91%                   |
| weak features   | unclaimed         | + claims as anchors         |              0.415 | x2.94          | 91%                   |
| weak features   | unclaimed         | + anchors + school totals   |              0.427 | x2.88          | 91%                   |

- **Weak features**: features alone rank pay at 0.425. Training on the claims drops that to 0.249; anchoring on them keeps 0.438 and cuts the typical miss for claimed players from x1.94 to x1.10. School totals lift the disclosed schools from 0.435 to 0.511 (all players 0.450).
- **Strong features**: features alone rank pay at 0.661. Training on the claims drops that to 0.619; anchoring on them keeps 0.664 and cuts the typical miss for claimed players from x1.26 to x1.09. School totals lift the disclosed schools from 0.665 to 0.732 (all players 0.675).

## Checking sources

Estimated bias comes from athletes reported by more than one source, anchored to school records. Strong flags fail the order test under the most generous tail the cap allows; moderate flags fail only under the central tail.

| source         | true bias   | estimated bias   | range over markets   |   claims |   strong flags |   moderate flags |
|:---------------|:------------|:-----------------|:---------------------|---------:|---------------:|-----------------:|
| hype_account   | +150%       | +121%            | +105% to +141%       |       75 |              0 |               74 |
| outlet_a       | +30%        | +28%             | +19% to +43%         |      120 |              0 |               82 |
| outlet_b       | 0%          | -7%              | -12% to -3%          |      120 |              0 |               26 |
| school_records | 0%          | 0%               | 0% to 0%             |       75 |              0 |                6 |

## Limits

- The synthetic market is built to match what is published; how pay really depends on talent and school is assumed, and the features' quality is set by the scenario. Real features need the CFBD data.
- Moderate inflation (+30%) is caught through overlapping sources, not by the aggregate tests; those catch only claims far beyond what the distribution allows.
- The intervals cover the truth somewhat more often than 80%, so they are cautious.