# Surplus value, 2026

What each A4 roster delivers on the field against what it would cost at market rates. On-field value comes from SP+ team ratings for all 138 FBS teams: a regression of each unit's rating (offense, defense, special teams) on its position groups' quality (starters' scores above a national replacement level, weights kept non-negative) prices each position in rating points. The player score's weights are learned the same way, by cross-validation against every team's rating, so no selection is involved. Points are priced at the A4 market: **$742,523 per rating point** (total A4 roster market value / total A4 points). Market value uses last season's production (what was known when deals were struck); on-field points use this season's. Team totals only. Method: [`docs/ESTIMATION.md`](../docs/ESTIMATION.md).

## Weights learned from team results

Out-of-sample R² of each unit's regression (5 folds) under the best weights on a 0.1 grid, against the prior weights the market value uses.

| unit          |   production |   rating |   class year |   R² learned |   R² prior weights |
|:--------------|-------------:|---------:|-------------:|-------------:|-------------------:|
| offense       |         0.40 |     0.10 |         0.50 |         0.73 |               0.62 |
| defense       |         0.50 |     0.50 |         0.00 |         0.41 |               0.41 |
| special teams |         0.00 |     0.90 |         0.10 |         0.01 |               0.01 |

## What each position is worth

The average team's points from each position's starters (and rotation), above replacement. Summed, player quality correlates 0.83 with SP+ overall team ratings.

| unit          | position          |   starters |   points per starter group |
|:--------------|:------------------|-----------:|---------------------------:|
| offense       | Quarterback       |          1 |                        4.7 |
| offense       | Running Back      |          1 |                        1.9 |
| offense       | Wide Receiver     |          3 |                        1.3 |
| offense       | Tight End         |          1 |                        0.3 |
| offense       | Offensive Lineman |          5 |                        1.3 |
| defense       | Defensive Lineman |          4 |                        2.7 |
| defense       | Linebacker        |          3 |                        2.2 |
| defense       | Defensive Back    |          4 |                        0.4 |
| special teams | Kicker            |          1 |                        0.0 |
| special teams | Punter            |          1 |                        0.0 |

## Surplus by program

On-field value minus market value. One rating point is about 0.30 wins over a 12-game season.

|   rank | program           | conference       | market value   |   on-field points | on-field value   | surplus   |   points per $1M |   SP+ |
|-------:|:------------------|:-----------------|:---------------|------------------:|:-----------------|:----------|-----------------:|------:|
|      1 | LSU               | SEC              | $22.1M         |              43.0 | $31.9M           | +$9.8M    |              1.9 |  25.2 |
|      2 | Ohio State        | Big Ten          | $21.9M         |              40.4 | $30.0M           | +$8.1M    |              1.9 |  28.6 |
|      3 | Notre Dame        | FBS Independents | $21.7M         |              39.9 | $29.6M           | +$8.0M    |              1.8 |  25.2 |
|      4 | Louisville        | ACC              | $14.2M         |              28.9 | $21.5M           | +$7.3M    |              2.0 |  12.2 |
|      5 | Miami             | ACC              | $19.7M         |              35.2 | $26.2M           | +$6.5M    |              1.8 |  24.7 |
|      6 | Alabama           | SEC              | $21.1M         |              36.4 | $27.1M           | +$6.0M    |              1.7 |  20.9 |
|      7 | South Carolina    | SEC              | $17.5M         |              30.4 | $22.6M           | +$5.1M    |              1.7 |  11.0 |
|      8 | Kentucky          | SEC              | $14.6M         |              26.3 | $19.6M           | +$5.0M    |              1.8 |  10.6 |
|      9 | Missouri          | SEC              | $15.8M         |              28.0 | $20.8M           | +$4.9M    |              1.8 |  14.2 |
|     10 | Florida           | SEC              | $18.3M         |              30.6 | $22.7M           | +$4.4M    |              1.7 |  10.6 |
|     11 | Duke              | ACC              | $13.1M         |              23.1 | $17.2M           | +$4.1M    |              1.8 |   6.8 |
|     12 | Northwestern      | Big Ten          | $14.8M         |              24.9 | $18.5M           | +$3.7M    |              1.7 |  13.7 |
|     13 | USC               | Big Ten          | $19.7M         |              31.5 | $23.4M           | +$3.7M    |              1.6 |  14.2 |
|     14 | Tennessee         | SEC              | $18.8M         |              30.2 | $22.4M           | +$3.6M    |              1.6 |  17.9 |
|     15 | Georgia           | SEC              | $24.3M         |              37.5 | $27.8M           | +$3.6M    |              1.6 |  27.1 |
|     16 | Utah              | Big 12           | $14.3M         |              24.0 | $17.8M           | +$3.5M    |              1.7 |  18.0 |
|     17 | Oklahoma State    | Big 12           | $15.3M         |              24.7 | $18.4M           | +$3.1M    |              1.6 |  12.4 |
|     18 | Mississippi State | SEC              | $16.2M         |              25.6 | $19.0M           | +$2.7M    |              1.6 |   6.0 |
|     19 | Oregon            | Big Ten          | $19.5M         |              29.4 | $21.8M           | +$2.3M    |              1.5 |  17.0 |
|     20 | SMU               | ACC              | $15.4M         |              23.8 | $17.6M           | +$2.2M    |              1.5 |  13.4 |
|     21 | Wake Forest       | ACC              | $13.0M         |              20.0 | $14.9M           | +$1.9M    |              1.5 |  12.2 |
|     22 | Indiana           | Big Ten          | $14.5M         |              21.9 | $16.3M           | +$1.8M    |              1.5 |  24.2 |
|     23 | Virginia Tech     | ACC              | $16.0M         |              23.7 | $17.6M           | +$1.6M    |              1.5 |   9.0 |
|     24 | Texas             | SEC              | $22.7M         |              32.7 | $24.2M           | +$1.6M    |              1.4 |  20.4 |
|     25 | Ole Miss          | SEC              | $20.3M         |              29.2 | $21.7M           | +$1.4M    |              1.4 |  14.7 |
|     26 | Cincinnati        | Big 12           | $13.0M         |              18.9 | $14.0M           | +$1.0M    |              1.4 |   6.7 |
|     27 | Auburn            | SEC              | $17.0M         |              24.0 | $17.9M           | +$0.8M    |              1.4 |   6.5 |
|     28 | Nebraska          | Big Ten          | $16.6M         |              23.4 | $17.4M           | +$0.7M    |              1.4 |  15.4 |
|     29 | UCLA              | Big Ten          | $16.8M         |              23.4 | $17.4M           | +$0.6M    |              1.4 |  14.4 |
|     30 | Houston           | Big 12           | $14.4M         |              19.8 | $14.7M           | +$0.4M    |              1.4 |  13.3 |
|     31 | North Carolina    | ACC              | $14.0M         |              19.1 | $14.2M           | +$0.2M    |              1.4 |   3.7 |
|     32 | Georgia Tech      | ACC              | $14.2M         |              19.3 | $14.3M           | +$0.1M    |              1.4 |  -1.1 |
|     33 | Stanford          | ACC              | $12.4M         |              16.7 | $12.4M           | -$0.0M    |              1.3 | -10.8 |
|     34 | Kansas State      | Big 12           | $14.6M         |              19.5 | $14.5M           | -$0.1M    |              1.3 |   8.8 |
|     35 | Pittsburgh        | ACC              | $12.9M         |              17.2 | $12.8M           | -$0.1M    |              1.3 |   7.9 |
|     36 | Florida State     | ACC              | $15.1M         |              19.8 | $14.7M           | -$0.4M    |              1.3 |   5.8 |
|     37 | Arizona           | Big 12           | $12.7M         |              16.1 | $12.0M           | -$0.7M    |              1.3 |  16.0 |
|     38 | Michigan          | Big Ten          | $19.2M         |              24.8 | $18.4M           | -$0.8M    |              1.3 |  11.5 |
|     39 | BYU               | Big 12           | $12.4M         |              15.5 | $11.5M           | -$1.0M    |              1.2 |  16.7 |
|     40 | Oklahoma          | SEC              | $17.7M         |              22.5 | $16.7M           | -$1.0M    |              1.3 |  10.3 |
|     41 | Clemson           | ACC              | $18.6M         |              23.6 | $17.6M           | -$1.1M    |              1.3 |   4.7 |
|     42 | Texas Tech        | Big 12           | $16.8M         |              21.1 | $15.7M           | -$1.2M    |              1.2 |  18.4 |
|     43 | West Virginia     | Big 12           | $15.1M         |              18.4 | $13.7M           | -$1.5M    |              1.2 |   0.0 |
|     44 | Washington        | Big Ten          | $14.2M         |              16.5 | $12.2M           | -$2.0M    |              1.2 |   9.5 |
|     45 | Purdue            | Big Ten          | $13.2M         |              14.8 | $11.0M           | -$2.2M    |              1.1 |   0.2 |
|     46 | Arizona State     | Big 12           | $14.4M         |              16.1 | $12.0M           | -$2.4M    |              1.1 |   2.3 |
|     47 | Penn State        | Big Ten          | $16.7M         |              18.5 | $13.8M           | -$2.9M    |              1.1 |   9.3 |
|     48 | Kansas            | Big 12           | $14.2M         |              15.1 | $11.2M           | -$3.0M    |              1.1 |   2.8 |
|     49 | Baylor            | Big 12           | $14.3M         |              15.1 | $11.2M           | -$3.1M    |              1.1 |   8.5 |
|     50 | NC State          | ACC              | $15.5M         |              16.7 | $12.4M           | -$3.1M    |              1.1 |  -0.9 |
|     51 | Wisconsin         | Big Ten          | $14.7M         |              15.5 | $11.5M           | -$3.2M    |              1.1 |   8.7 |
|     52 | Colorado          | Big 12           | $14.9M         |              15.7 | $11.6M           | -$3.2M    |              1.1 |  -4.3 |
|     53 | TCU               | Big 12           | $13.5M         |              13.7 | $10.2M           | -$3.3M    |              1.0 |   8.6 |
|     54 | Illinois          | Big Ten          | $13.5M         |              13.8 | $10.2M           | -$3.3M    |              1.0 |   6.8 |
|     55 | Syracuse          | ACC              | $15.5M         |              16.0 | $11.9M           | -$3.6M    |              1.0 |  -2.8 |
|     56 | Iowa              | Big Ten          | $13.0M         |              12.6 | $9.4M            | -$3.6M    |              1.0 |  12.4 |
|     57 | California        | ACC              | $13.6M         |              13.4 | $10.0M           | -$3.6M    |              1.0 |  -8.2 |
|     58 | Vanderbilt        | SEC              | $14.7M         |              14.4 | $10.7M           | -$4.0M    |              1.0 |  -1.4 |
|     59 | Iowa State        | Big 12           | $13.6M         |              12.7 | $9.5M            | -$4.2M    |              0.9 |  -1.2 |
|     60 | Rutgers           | Big Ten          | $15.3M         |              14.6 | $10.8M           | -$4.4M    |              1.0 |  -4.9 |
|     61 | Maryland          | Big Ten          | $13.6M         |              12.2 | $9.1M            | -$4.6M    |              0.9 |  -2.1 |
|     62 | UCF               | Big 12           | $13.3M         |              11.0 | $8.2M            | -$5.1M    |              0.8 |   4.5 |
|     63 | Michigan State    | Big Ten          | $12.2M         |               9.3 | $6.9M            | -$5.3M    |              0.8 |  -3.0 |
|     64 | Arkansas          | SEC              | $15.0M         |              12.0 | $8.9M            | -$6.1M    |              0.8 |  -0.4 |
|     65 | Texas A&M         | SEC              | $21.7M         |              21.0 | $15.6M           | -$6.1M    |              1.0 |   9.7 |
|     66 | Virginia          | ACC              | $15.1M         |              12.1 | $9.0M            | -$6.2M    |              0.8 |   5.8 |
|     67 | Boston College    | ACC              | $13.4M         |               9.5 | $7.1M            | -$6.3M    |              0.7 |  -1.5 |
|     68 | Minnesota         | Big Ten          | $15.3M         |              11.4 | $8.5M            | -$6.8M    |              0.8 |   3.9 |

## By conference

| conference       |   programs | surplus   |   efficiency |
|:-----------------|-----------:|:----------|-------------:|
| ACC              |         17 | -$0.0M    |          1.3 |
| Big 12           |         16 | -$1.3M    |          1.2 |
| Big Ten          |         18 | -$1.0M    |          1.2 |
| FBS Independents |          1 | +$8.0M    |          1.8 |
| SEC              |         16 | +$2.0M    |          1.5 |

## Limits

- This season's production partly reflects team quality, so strong teams' players look productive; the regression measures that association, not cause.
- Offensive linemen and specialists have no individual production; special teams show almost no signal.
- Market value is a market price for the roster, not what the school pays; surplus is relative to that price.
- Ratings are SP+ as of this pull, mid-season.