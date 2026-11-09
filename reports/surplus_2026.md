# Surplus value, 2026

What each A4 roster delivers on the field against what it would cost at market rates. On-field value comes from SP+ team ratings for all 138 FBS teams: a regression of each unit's rating (offense, defense, special teams) on its position groups' quality (starters' scores above a national replacement level, weights kept non-negative) prices each position in rating points. The player score's weights are learned the same way, by cross-validation against every team's rating, so no selection is involved. Points are priced at the A4 market: **$699,624 per rating point** (total A4 roster market value / total A4 points). Market value uses last season's production (what was known when deals were struck); on-field points use this season's. Team totals only. Method: [`docs/ESTIMATION.md`](../docs/ESTIMATION.md).

## Weights learned from team results

Out-of-sample R² of each unit's regression (5 folds) under the best weights on a 0.1 grid, against the prior weights the market value uses.

| unit          |   production |   rating |   class year |   R² learned |   R² prior weights |
|:--------------|-------------:|---------:|-------------:|-------------:|-------------------:|
| offense       |         0.50 |     0.10 |         0.40 |         0.73 |               0.57 |
| defense       |         0.50 |     0.40 |         0.10 |         0.37 |               0.37 |
| special teams |         0.00 |     0.00 |         1.00 |        -0.00 |              -0.01 |

## What each position is worth

The average team's points from each position's starters (and rotation), above replacement. Summed, player quality correlates 0.81 with SP+ overall team ratings.

| unit          | position          |   starters |   points per starter group |
|:--------------|:------------------|-----------:|---------------------------:|
| offense       | Quarterback       |          1 |                        5.8 |
| offense       | Running Back      |          1 |                        2.1 |
| offense       | Wide Receiver     |          3 |                        0.9 |
| offense       | Tight End         |          1 |                        0.4 |
| offense       | Offensive Lineman |          5 |                        1.0 |
| defense       | Defensive Lineman |          4 |                        3.3 |
| defense       | Linebacker        |          3 |                        2.9 |
| defense       | Defensive Back    |          4 |                        0.0 |
| special teams | Kicker            |          1 |                        0.0 |
| special teams | Punter            |          1 |                        0.0 |

## Surplus by program

On-field value minus market value. One rating point is about 0.30 wins over a 12-game season.

|   rank | program           | conference       | market value   |   on-field points | on-field value   | surplus   |   points per $1M |   SP+ |
|-------:|:------------------|:-----------------|:---------------|------------------:|:-----------------|:----------|-----------------:|------:|
|      1 | Louisville        | ACC              | $14.2M         |              33.4 | $23.4M           | +$9.2M    |              2.4 |  17.7 |
|      2 | LSU               | SEC              | $22.1M         |              43.3 | $30.3M           | +$8.2M    |              2.0 |  22.9 |
|      3 | Notre Dame        | FBS Independents | $21.7M         |              41.9 | $29.3M           | +$7.7M    |              1.9 |  24.4 |
|      4 | Duke              | ACC              | $13.1M         |              28.7 | $20.1M           | +$7.0M    |              2.2 |  13.0 |
|      5 | Ohio State        | Big Ten          | $21.9M         |              39.6 | $27.7M           | +$5.9M    |              1.8 |  24.0 |
|      6 | Miami             | ACC              | $19.7M         |              36.0 | $25.2M           | +$5.5M    |              1.8 |  24.0 |
|      7 | Oklahoma State    | Big 12           | $15.3M         |              29.7 | $20.8M           | +$5.5M    |              1.9 |  15.5 |
|      8 | Alabama           | SEC              | $21.1M         |              37.7 | $26.4M           | +$5.3M    |              1.8 |  22.7 |
|      9 | South Carolina    | SEC              | $17.5M         |              32.3 | $22.6M           | +$5.1M    |              1.9 |  13.7 |
|     10 | Kentucky          | SEC              | $14.6M         |              27.4 | $19.2M           | +$4.6M    |              1.9 |   8.3 |
|     11 | Utah              | Big 12           | $14.3M         |              26.5 | $18.6M           | +$4.2M    |              1.9 |  21.5 |
|     12 | Missouri          | SEC              | $15.8M         |              28.5 | $19.9M           | +$4.1M    |              1.8 |  13.7 |
|     13 | Northwestern      | Big Ten          | $14.8M         |              26.4 | $18.5M           | +$3.7M    |              1.8 |  12.4 |
|     14 | SMU               | ACC              | $15.4M         |              27.2 | $19.0M           | +$3.6M    |              1.8 |  15.8 |
|     15 | Virginia Tech     | ACC              | $16.0M         |              27.7 | $19.4M           | +$3.4M    |              1.7 |   6.6 |
|     16 | Florida           | SEC              | $18.3M         |              30.6 | $21.4M           | +$3.1M    |              1.7 |   5.9 |
|     17 | Tennessee         | SEC              | $18.8M         |              31.0 | $21.7M           | +$2.9M    |              1.6 |  20.5 |
|     18 | Wake Forest       | ACC              | $13.0M         |              22.4 | $15.7M           | +$2.7M    |              1.7 |  20.0 |
|     19 | Cincinnati        | Big 12           | $13.0M         |              22.3 | $15.6M           | +$2.6M    |              1.7 |   3.0 |
|     20 | Georgia           | SEC              | $24.3M         |              38.3 | $26.8M           | +$2.6M    |              1.6 |  31.3 |
|     21 | Mississippi State | SEC              | $16.2M         |              26.2 | $18.4M           | +$2.1M    |              1.6 |   3.8 |
|     22 | Houston           | Big 12           | $14.4M         |              23.4 | $16.4M           | +$2.0M    |              1.6 |  14.1 |
|     23 | North Carolina    | ACC              | $14.0M         |              22.8 | $15.9M           | +$1.9M    |              1.6 |   5.3 |
|     24 | USC               | Big Ten          | $19.7M         |              30.7 | $21.5M           | +$1.8M    |              1.6 |  15.8 |
|     25 | Auburn            | SEC              | $17.0M         |              26.6 | $18.6M           | +$1.5M    |              1.6 |   2.8 |
|     26 | Oregon            | Big Ten          | $19.5M         |              28.8 | $20.1M           | +$0.6M    |              1.5 |  16.9 |
|     27 | Indiana           | Big Ten          | $14.5M         |              21.5 | $15.0M           | +$0.5M    |              1.5 |  23.5 |
|     28 | Texas             | SEC              | $22.7M         |              32.9 | $23.0M           | +$0.3M    |              1.4 |  23.5 |
|     29 | Ole Miss          | SEC              | $20.3M         |              29.5 | $20.6M           | +$0.3M    |              1.4 |  13.5 |
|     30 | Nebraska          | Big Ten          | $16.6M         |              24.2 | $16.9M           | +$0.3M    |              1.4 |  14.4 |
|     31 | Texas Tech        | Big 12           | $16.8M         |              24.4 | $17.1M           | +$0.2M    |              1.4 |  18.1 |
|     32 | BYU               | Big 12           | $12.4M         |              17.9 | $12.5M           | +$0.1M    |              1.4 |  16.2 |
|     33 | UCLA              | Big Ten          | $16.8M         |              24.0 | $16.8M           | +$0.0M    |              1.4 |  20.2 |
|     34 | Arizona           | Big 12           | $12.7M         |              18.1 | $12.7M           | +$0.0M    |              1.4 |  15.4 |
|     35 | West Virginia     | Big 12           | $15.1M         |              21.3 | $14.9M           | -$0.2M    |              1.4 |  -0.2 |
|     36 | Kansas State      | Big 12           | $14.6M         |              20.1 | $14.1M           | -$0.5M    |              1.4 |   4.5 |
|     37 | Pittsburgh        | ACC              | $12.9M         |              17.6 | $12.3M           | -$0.7M    |              1.4 |  10.2 |
|     38 | Florida State     | ACC              | $15.1M         |              20.6 | $14.4M           | -$0.7M    |              1.4 |   5.5 |
|     39 | Oklahoma          | SEC              | $17.7M         |              23.9 | $16.7M           | -$0.9M    |              1.4 |   7.8 |
|     40 | Stanford          | ACC              | $12.4M         |              16.4 | $11.4M           | -$1.0M    |              1.3 | -13.3 |
|     41 | Purdue            | Big Ten          | $13.2M         |              16.6 | $11.6M           | -$1.6M    |              1.3 |  -2.4 |
|     42 | Georgia Tech      | ACC              | $14.2M         |              17.9 | $12.5M           | -$1.7M    |              1.3 |  -8.1 |
|     43 | Kansas            | Big 12           | $14.2M         |              17.9 | $12.5M           | -$1.7M    |              1.3 |   2.0 |
|     44 | Washington        | Big Ten          | $14.2M         |              17.8 | $12.5M           | -$1.7M    |              1.3 |   8.9 |
|     45 | Baylor            | Big 12           | $14.3M         |              17.9 | $12.6M           | -$1.8M    |              1.2 |  13.3 |
|     46 | Clemson           | ACC              | $18.6M         |              23.7 | $16.6M           | -$2.0M    |              1.3 |   3.3 |
|     47 | Arizona State     | Big 12           | $14.4M         |              17.4 | $12.2M           | -$2.3M    |              1.2 |   1.9 |
|     48 | Illinois          | Big Ten          | $13.5M         |              16.1 | $11.3M           | -$2.3M    |              1.2 |   8.0 |
|     49 | Penn State        | Big Ten          | $16.7M         |              20.6 | $14.4M           | -$2.3M    |              1.2 |   9.3 |
|     50 | TCU               | Big 12           | $13.5M         |              15.4 | $10.8M           | -$2.7M    |              1.1 |   7.9 |
|     51 | Syracuse          | ACC              | $15.5M         |              18.1 | $12.7M           | -$2.8M    |              1.2 |  -2.7 |
|     52 | Iowa              | Big Ten          | $13.0M         |              14.6 | $10.2M           | -$2.8M    |              1.1 |  16.4 |
|     53 | Iowa State        | Big 12           | $13.6M         |              15.3 | $10.7M           | -$2.9M    |              1.1 |  -2.3 |
|     54 | Michigan          | Big Ten          | $19.2M         |              23.4 | $16.3M           | -$2.9M    |              1.2 |  10.0 |
|     55 | Wisconsin         | Big Ten          | $14.7M         |              16.7 | $11.7M           | -$3.0M    |              1.1 |   9.1 |
|     56 | Maryland          | Big Ten          | $13.6M         |              14.8 | $10.3M           | -$3.3M    |              1.1 |  -2.1 |
|     57 | Colorado          | Big 12           | $14.9M         |              16.4 | $11.5M           | -$3.4M    |              1.1 |  -5.2 |
|     58 | Vanderbilt        | SEC              | $14.7M         |              16.0 | $11.2M           | -$3.5M    |              1.1 |  -1.5 |
|     59 | NC State          | ACC              | $15.5M         |              16.7 | $11.7M           | -$3.9M    |              1.1 |  -2.3 |
|     60 | California        | ACC              | $13.6M         |              12.1 | $8.5M            | -$5.1M    |              0.9 | -11.4 |
|     61 | Rutgers           | Big Ten          | $15.3M         |              14.3 | $10.0M           | -$5.3M    |              0.9 |  -9.2 |
|     62 | UCF               | Big 12           | $13.3M         |              10.9 | $7.6M            | -$5.7M    |              0.8 |   1.3 |
|     63 | Michigan State    | Big Ten          | $12.2M         |               9.1 | $6.3M            | -$5.8M    |              0.7 |  -2.4 |
|     64 | Arkansas          | SEC              | $15.0M         |              13.0 | $9.1M            | -$5.9M    |              0.9 |  -3.6 |
|     65 | Boston College    | ACC              | $13.4M         |              10.5 | $7.4M            | -$6.0M    |              0.8 |  -5.4 |
|     66 | Virginia          | ACC              | $15.1M         |              11.9 | $8.3M            | -$6.8M    |              0.8 |   2.1 |
|     67 | Minnesota         | Big Ten          | $15.3M         |              11.9 | $8.3M            | -$7.0M    |              0.8 |   1.3 |
|     68 | Texas A&M         | SEC              | $21.7M         |              18.8 | $13.2M           | -$8.5M    |              0.9 |   8.3 |

## By conference

| conference       |   programs | surplus   |   efficiency |
|:-----------------|-----------:|:----------|-------------:|
| ACC              |         17 | +$0.2M    |          1.4 |
| Big 12           |         16 | -$0.4M    |          1.4 |
| Big Ten          |         18 | -$1.4M    |          1.3 |
| FBS Independents |          1 | +$7.7M    |          1.9 |
| SEC              |         16 | +$1.3M    |          1.5 |

## Limits

- This season's production partly reflects team quality, so strong teams' players look productive; the regression measures that association, not cause.
- Offensive linemen and specialists have no individual production; special teams show almost no signal.
- Market value is a market price for the roster, not what the school pays; surplus is relative to that price.
- Ratings are SP+ as of this pull, mid-season.