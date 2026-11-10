# Surplus value against several ratings, 2026

The surplus model asks how much of each team's rating its players explain. This runs the same fit against six ratings instead of SP+ alone, each as a team total on every position group, with the player-score weights chosen by cross-validation for that rating, and prices surplus under each. Method: [`src/nilmodel/ratings.py`](../src/nilmodel/ratings.py).

- **2026 results only** is fit here from 562 completed FBS-vs-FBS games through week 10 (last game 2026-11-08), margins capped at 28; home edge 2.6 points. No prior.
- **Your model** is the team rating implied by CollegeFootballRatings2026's posted model margins, 566 games, week 01 to week 08; home edge 2.5. Those files stop at week 8.

- SP+, ESPN FPI, SRS and Elo are CollegeFootballData's current 2026 ratings. Player production is this season's.

## Player-score weights, pooled

One set of weights for 2025 and 2026 together (274 team-seasons, each season scored on its own rosters and production, a baseline per season, folds grouped by program): production 0.9 / rating 0.1 / class year 0.0. Each published rating's position values are fit on both seasons. What it gives up against each season's own best:

| rating   |   R² 2026, pooled weights |   R² 2026, its own best | its own best (2026)   |   R² 2025, pooled weights |
|:---------|--------------------------:|------------------------:|:----------------------|--------------------------:|
| SP+      |                       0.6 |                     0.6 | 0.4 / 0.1 / 0.5       |                       0.7 |
| ESPN FPI |                       0.7 |                     0.7 | 0.4 / 0.1 / 0.5       |                       0.7 |
| SRS      |                       0.7 |                     0.7 | 0.4 / 0.1 / 0.5       |                       0.6 |
| Elo      |                       0.6 |                     0.6 | 0.7 / 0.1 / 0.2       |                       0.7 |

## How well each rating is explained

Out-of-sample R² (5 folds over 138 FBS teams). "Recruiting + class only" leaves production out: a rating that leans on a preseason prior built from recruiting should be explained better by it.

| rating                              | preseason prior                       | weights (production / recruiting / class year)   |   R² learned |   R² prior weights |   R² production only |   R² recruiting + class only |   QB points |   DL points | $ per point   |
|:------------------------------------|:--------------------------------------|:-------------------------------------------------|-------------:|-------------------:|---------------------:|-----------------------------:|------------:|------------:|:--------------|
| SP+                                 | yes, fading                           | 0.9 / 0.1 / 0.0                                  |         0.66 |               0.53 |                 0.61 |                         0.35 |        8.00 |        2.70 | $511,711      |
| ESPN FPI                            | yes                                   | 0.9 / 0.1 / 0.0                                  |         0.72 |               0.63 |                 0.64 |                         0.49 |        7.10 |        2.30 | $512,659      |
| SRS                                 | no                                    | 0.9 / 0.1 / 0.0                                  |         0.67 |               0.55 |                 0.61 |                         0.40 |        7.50 |        1.90 | $523,931      |
| Elo                                 | carries over last season              | 0.9 / 0.1 / 0.0                                  |         0.64 |               0.51 |                 0.59 |                         0.36 |        7.10 |        2.90 | $530,339      |
| 2026 results only                   | no                                    | 0.9 / 0.1 / 0.0                                  |         0.67 |               0.57 |                 0.65 |                         0.45 |        6.30 |        2.60 | $514,501      |
| SP+ and FEI projections (weeks 1-8) | yes: pre-game projections             | 0.9 / 0.1 / 0.0                                  |         0.65 |               0.67 |                 0.63 |                         0.58 |        3.90 |        2.30 | $594,161      |
| Your model (weeks 1-8)              | market and SP+/FEI, which have priors | 0.9 / 0.1 / 0.0                                  |         0.70 |               0.73 |                 0.68 |                         0.63 |        4.00 |        2.40 | $566,157      |

## Do the ratings agree on surplus?

Rank correlation of program surplus between ratings:

|          |   SP+ |   ESPN FPI |   SRS |   Elo |
|:---------|------:|-----------:|------:|------:|
| SP+      |  1.00 |       0.97 |  0.99 |  0.99 |
| ESPN FPI |  0.97 |       1.00 |  0.99 |  0.97 |
| SRS      |  0.99 |       0.99 |  1.00 |  0.98 |
| Elo      |  0.99 |       0.97 |  0.98 |  1.00 |

- Under the four published ratings (SP+, FPI, SRS, Elo), which the roster numbers use, **28** programs show a surplus under all four and **30** a deficit; **10** depend on the rating. The results-only rating is a check on SP+'s prior, and your model is kept apart as the market's view.

## Every A4 program

Sorted by median surplus across the four published ratings; range and call are theirs too.

| program           | conference       | market value   | SP+    | ESPN FPI   | SRS    | Elo    | 2026 results only   | SP+ and FEI projections (weeks 1-8)   | Your model (weeks 1-8)   | range            | median   | call               |
|:------------------|:-----------------|:---------------|:-------|:-----------|:-------|:-------|:--------------------|:--------------------------------------|:-------------------------|:-----------------|:---------|:-------------------|
| Kentucky          | SEC              | $14.6M         | +$6.6M | +$7.3M     | +$7.2M | +$6.4M | +$5.9M              | +$6.2M                                | +$6.4M                   | +$6.4M to +$7.3M | +$6.9M   | surplus everywhere |
| Alabama           | SEC              | $21.1M         | +$6.1M | +$7.4M     | +$6.8M | +$5.8M | +$6.8M              | +$8.3M                                | +$8.5M                   | +$5.8M to +$7.4M | +$6.5M   | surplus everywhere |
| Utah              | Big 12           | $14.3M         | +$6.5M | +$5.9M     | +$6.5M | +$6.3M | +$5.3M              | +$3.9M                                | +$3.8M                   | +$5.9M to +$6.5M | +$6.4M   | surplus everywhere |
| SMU               | ACC              | $15.4M         | +$6.2M | +$6.1M     | +$6.3M | +$6.6M | +$5.2M              | +$6.9M                                | +$6.8M                   | +$6.1M to +$6.6M | +$6.3M   | surplus everywhere |
| LSU               | SEC              | $22.1M         | +$5.6M | +$6.4M     | +$5.9M | +$6.0M | +$6.0M              | +$8.9M                                | +$8.8M                   | +$5.6M to +$6.4M | +$5.9M   | surplus everywhere |
| Louisville        | ACC              | $14.2M         | +$6.0M | +$3.8M     | +$4.8M | +$5.2M | +$3.8M              | +$0.6M                                | +$0.7M                   | +$3.8M to +$6.0M | +$5.0M   | surplus everywhere |
| North Carolina    | ACC              | $14.0M         | +$5.1M | +$4.6M     | +$4.9M | +$4.3M | +$4.8M              | +$2.9M                                | +$3.0M                   | +$4.3M to +$5.1M | +$4.7M   | surplus everywhere |
| Duke              | ACC              | $13.1M         | +$4.9M | +$3.3M     | +$4.5M | +$5.1M | +$4.0M              | +$1.3M                                | +$0.7M                   | +$3.3M to +$5.1M | +$4.7M   | surplus everywhere |
| Missouri          | SEC              | $15.8M         | +$4.4M | +$4.8M     | +$4.6M | +$4.9M | +$5.2M              | +$5.7M                                | +$5.7M                   | +$4.4M to +$4.9M | +$4.7M   | surplus everywhere |
| Oklahoma State    | Big 12           | $15.3M         | +$5.1M | +$2.9M     | +$4.4M | +$4.9M | +$3.2M              | −$0.3M                                | −$0.3M                   | +$2.9M to +$5.1M | +$4.6M   | surplus everywhere |
| Miami             | ACC              | $19.7M         | +$4.0M | +$5.4M     | +$4.9M | +$3.8M | +$4.7M              | +$7.0M                                | +$7.7M                   | +$3.8M to +$5.4M | +$4.4M   | surplus everywhere |
| Northwestern      | Big Ten          | $14.8M         | +$5.1M | +$4.0M     | +$4.7M | +$4.2M | +$4.0M              | +$1.1M                                | +$0.7M                   | +$4.0M to +$5.1M | +$4.4M   | surplus everywhere |
| Cincinnati        | Big 12           | $13.0M         | +$4.6M | +$2.7M     | +$3.8M | +$4.6M | +$3.0M              | −$0.5M                                | −$1.0M                   | +$2.7M to +$4.6M | +$4.2M   | surplus everywhere |
| Notre Dame        | FBS Independents | $21.7M         | +$2.9M | +$4.0M     | +$3.5M | +$3.9M | +$4.4M              | +$7.5M                                | +$6.9M                   | +$2.9M to +$4.0M | +$3.7M   | surplus everywhere |
| Houston           | Big 12           | $14.4M         | +$3.9M | +$3.2M     | +$3.9M | +$2.6M | +$1.6M              | −$0.5M                                | −$0.0M                   | +$2.6M to +$3.9M | +$3.5M   | surplus everywhere |
| Virginia Tech     | ACC              | $16.0M         | +$3.7M | +$3.1M     | +$3.5M | +$2.4M | +$2.9M              | +$1.0M                                | +$1.0M                   | +$2.4M to +$3.7M | +$3.3M   | surplus everywhere |
| Wake Forest       | ACC              | $13.0M         | +$4.0M | +$2.4M     | +$2.9M | +$3.5M | +$2.1M              | +$0.3M                                | +$0.5M                   | +$2.4M to +$4.0M | +$3.2M   | surplus everywhere |
| West Virginia     | Big 12           | $15.1M         | +$2.6M | +$2.5M     | +$2.7M | +$2.3M | +$2.0M              | +$0.4M                                | +$0.6M                   | +$2.3M to +$2.7M | +$2.6M   | surplus everywhere |
| South Carolina    | SEC              | $17.5M         | +$2.2M | +$2.8M     | +$2.4M | +$2.3M | +$2.7M              | +$3.7M                                | +$4.0M                   | +$2.2M to +$2.8M | +$2.4M   | surplus everywhere |
| Texas Tech        | Big 12           | $16.8M         | +$2.4M | +$1.8M     | +$2.1M | +$2.8M | +$3.0M              | +$2.5M                                | +$1.7M                   | +$1.8M to +$2.8M | +$2.2M   | surplus everywhere |
| Arizona           | Big 12           | $12.7M         | +$1.7M | +$1.1M     | +$1.5M | +$1.0M | +$1.7M              | +$0.3M                                | +$0.3M                   | +$1.0M to +$1.7M | +$1.3M   | surplus everywhere |
| Tennessee         | SEC              | $18.8M         | +$1.3M | +$1.3M     | +$1.2M | +$2.4M | +$1.2M              | +$2.2M                                | +$2.0M                   | +$1.2M to +$2.4M | +$1.3M   | surplus everywhere |
| Nebraska          | Big Ten          | $16.6M         | +$0.7M | +$1.3M     | +$1.1M | +$1.3M | +$0.7M              | +$3.1M                                | +$2.9M                   | +$0.7M to +$1.3M | +$1.2M   | surplus everywhere |
| Indiana           | Big Ten          | $14.5M         | +$1.3M | +$0.9M     | +$0.9M | +$1.2M | +$1.2M              | −$0.0M                                | +$0.6M                   | +$0.9M to +$1.3M | +$1.0M   | surplus everywhere |
| Illinois          | Big Ten          | $13.5M         | +$0.8M | +$0.9M     | +$1.0M | +$0.5M | +$1.5M              | +$0.7M                                | +$1.0M                   | +$0.5M to +$1.0M | +$0.9M   | surplus everywhere |
| Ohio State        | Big Ten          | $21.9M         | +$0.2M | +$1.3M     | +$1.0M | +$0.5M | +$0.0M              | +$2.6M                                | +$3.1M                   | +$0.2M to +$1.3M | +$0.7M   | surplus everywhere |
| TCU               | Big 12           | $13.5M         | +$0.6M | +$0.8M     | +$1.0M | −$0.5M | −$0.0M              | −$0.3M                                | −$0.0M                   | −$0.5M to +$1.0M | +$0.7M   | depends on rating  |
| Stanford          | ACC              | $12.4M         | +$0.3M | +$0.3M     | +$0.6M | +$0.4M | +$0.9M              | +$0.6M                                | +$0.2M                   | +$0.3M to +$0.6M | +$0.3M   | surplus everywhere |
| Wisconsin         | Big Ten          | $14.7M         | +$0.2M | +$0.4M     | +$0.2M | +$0.2M | +$0.9M              | +$1.3M                                | +$0.8M                   | +$0.2M to +$0.4M | +$0.2M   | surplus everywhere |
| Washington        | Big Ten          | $14.2M         | −$0.2M | +$0.7M     | +$0.4M | −$0.5M | −$0.4M              | +$0.3M                                | +$1.1M                   | −$0.5M to +$0.7M | +$0.1M   | depends on rating  |
| Purdue            | Big Ten          | $13.2M         | +$0.2M | −$0.2M     | +$0.1M | −$0.1M | −$0.6M              | −$1.9M                                | −$1.5M                   | −$0.2M to +$0.2M | +$0.0M   | depends on rating  |
| Penn State        | Big Ten          | $16.7M         | −$0.2M | +$0.3M     | +$0.1M | −$0.0M | +$1.3M              | +$3.2M                                | +$2.5M                   | −$0.2M to +$0.3M | +$0.0M   | depends on rating  |
| Mississippi State | SEC              | $16.2M         | −$0.1M | +$0.0M     | −$0.1M | +$0.4M | −$0.6M              | −$0.0M                                | +$0.3M                   | −$0.1M to +$0.4M | −$0.0M   | depends on rating  |
| Georgia           | SEC              | $24.3M         | −$0.8M | +$0.9M     | +$0.2M | −$0.5M | +$1.8M              | +$3.9M                                | +$3.3M                   | −$0.8M to +$0.9M | −$0.1M   | depends on rating  |
| BYU               | Big 12           | $12.4M         | +$0.4M | −$0.7M     | −$0.2M | −$0.1M | −$0.9M              | −$2.0M                                | −$2.0M                   | −$0.7M to +$0.4M | −$0.1M   | depends on rating  |
| Oklahoma          | SEC              | $17.7M         | −$0.4M | +$0.6M     | +$0.0M | −$0.4M | −$0.5M              | +$1.3M                                | +$1.6M                   | −$0.4M to +$0.6M | −$0.2M   | depends on rating  |
| Pittsburgh        | ACC              | $12.9M         | +$0.0M | −$0.4M     | −$0.2M | −$0.6M | −$0.7M              | −$2.7M                                | −$2.5M                   | −$0.6M to +$0.0M | −$0.3M   | depends on rating  |
| Syracuse          | ACC              | $15.5M         | −$0.5M | +$0.1M     | −$0.4M | −$0.4M | +$0.9M              | +$1.9M                                | +$1.6M                   | −$0.5M to +$0.1M | −$0.4M   | depends on rating  |
| Iowa              | Big Ten          | $13.0M         | −$0.4M | −$0.4M     | −$0.5M | −$0.3M | −$0.2M              | +$0.2M                                | −$0.3M                   | −$0.5M to −$0.3M | −$0.4M   | deficit everywhere |
| Iowa State        | Big 12           | $13.6M         | −$0.5M | −$0.8M     | −$0.5M | −$0.4M | +$0.4M              | −$0.8M                                | −$1.3M                   | −$0.8M to −$0.4M | −$0.5M   | deficit everywhere |
| Florida State     | ACC              | $15.1M         | −$0.6M | −$0.7M     | −$0.6M | −$1.1M | −$1.2M              | −$2.9M                                | −$2.4M                   | −$1.1M to −$0.6M | −$0.7M   | deficit everywhere |
| Georgia Tech      | ACC              | $14.2M         | −$0.9M | −$0.4M     | −$0.9M | −$0.6M | +$0.8M              | +$1.9M                                | +$1.6M                   | −$0.9M to −$0.4M | −$0.7M   | deficit everywhere |
| USC               | Big Ten          | $19.7M         | −$1.1M | −$0.6M     | −$0.9M | −$0.8M | −$1.4M              | +$1.1M                                | +$1.2M                   | −$1.1M to −$0.6M | −$0.9M   | deficit everywhere |
| Vanderbilt        | SEC              | $14.7M         | −$1.2M | −$1.6M     | −$1.5M | −$1.4M | −$2.8M              | −$3.3M                                | −$3.1M                   | −$1.6M to −$1.2M | −$1.4M   | deficit everywhere |
| Kansas State      | Big 12           | $14.6M         | −$1.3M | −$1.7M     | −$1.6M | −$1.5M | −$2.5M              | −$2.3M                                | −$2.2M                   | −$1.7M to −$1.3M | −$1.5M   | deficit everywhere |
| Auburn            | SEC              | $17.0M         | −$1.5M | −$1.5M     | −$1.7M | −$1.9M | −$0.6M              | −$2.0M                                | −$1.9M                   | −$1.9M to −$1.5M | −$1.6M   | deficit everywhere |
| Florida           | SEC              | $18.3M         | −$1.7M | −$1.7M     | −$1.7M | −$1.0M | −$1.4M              | −$0.3M                                | −$0.2M                   | −$1.7M to −$1.0M | −$1.7M   | deficit everywhere |
| Baylor            | Big 12           | $14.3M         | −$1.5M | −$2.2M     | −$2.0M | −$1.9M | −$2.3M              | −$3.8M                                | −$3.8M                   | −$2.2M to −$1.5M | −$2.0M   | deficit everywhere |
| UCLA              | Big Ten          | $16.8M         | −$1.9M | −$2.4M     | −$2.2M | −$1.1M | −$0.7M              | −$1.2M                                | −$2.0M                   | −$2.4M to −$1.1M | −$2.1M   | deficit everywhere |
| Texas             | SEC              | $22.7M         | −$2.6M | −$1.6M     | −$2.5M | −$1.8M | −$1.2M              | +$1.0M                                | +$1.0M                   | −$2.6M to −$1.6M | −$2.1M   | deficit everywhere |
| Kansas            | Big 12           | $14.2M         | −$1.9M | −$2.4M     | −$2.5M | −$1.6M | −$1.4M              | −$1.7M                                | −$2.0M                   | −$2.5M to −$1.6M | −$2.1M   | deficit everywhere |
| Boston College    | ACC              | $13.4M         | −$2.4M | −$2.4M     | −$2.6M | −$2.5M | −$2.4M              | −$3.9M                                | −$4.1M                   | −$2.6M to −$2.4M | −$2.5M   | deficit everywhere |
| NC State          | ACC              | $15.5M         | −$2.4M | −$2.6M     | −$2.4M | −$2.8M | −$2.8M              | −$3.0M                                | −$3.3M                   | −$2.8M to −$2.4M | −$2.5M   | deficit everywhere |
| Oregon            | Big Ten          | $19.5M         | −$2.8M | −$2.0M     | −$2.3M | −$2.8M | −$2.5M              | −$1.5M                                | −$1.3M                   | −$2.8M to −$2.0M | −$2.5M   | deficit everywhere |
| Ole Miss          | SEC              | $20.3M         | −$3.0M | −$3.8M     | −$3.5M | −$3.2M | −$4.3M              | −$4.6M                                | −$4.6M                   | −$3.8M to −$3.0M | −$3.4M   | deficit everywhere |
| Arizona State     | Big 12           | $14.4M         | −$3.1M | −$4.0M     | −$3.7M | −$2.7M | −$2.5M              | −$3.5M                                | −$3.7M                   | −$4.0M to −$2.7M | −$3.4M   | deficit everywhere |
| Colorado          | Big 12           | $14.9M         | −$3.4M | −$3.8M     | −$3.9M | −$3.1M | −$3.8M              | −$3.9M                                | −$3.3M                   | −$3.9M to −$3.1M | −$3.6M   | deficit everywhere |
| Maryland          | Big Ten          | $13.6M         | −$3.6M | −$3.9M     | −$3.8M | −$3.7M | −$3.5M              | −$3.9M                                | −$4.0M                   | −$3.9M to −$3.6M | −$3.8M   | deficit everywhere |
| Clemson           | ACC              | $18.6M         | −$4.5M | −$3.0M     | −$4.0M | −$3.8M | −$3.6M              | −$1.2M                                | −$0.7M                   | −$4.5M to −$3.0M | −$3.9M   | deficit everywhere |
| Michigan State    | Big Ten          | $12.2M         | −$4.3M | −$3.6M     | −$4.0M | −$4.2M | −$3.6M              | −$3.1M                                | −$3.1M                   | −$4.3M to −$3.6M | −$4.1M   | deficit everywhere |
| Michigan          | Big Ten          | $19.2M         | −$5.2M | −$3.6M     | −$4.6M | −$4.5M | −$4.3M              | −$1.1M                                | −$0.6M                   | −$5.2M to −$3.6M | −$4.5M   | deficit everywhere |
| Minnesota         | Big Ten          | $15.3M         | −$5.0M | −$4.7M     | −$5.0M | −$4.6M | −$5.3M              | −$4.3M                                | −$3.9M                   | −$5.0M to −$4.6M | −$4.8M   | deficit everywhere |
| Virginia          | ACC              | $15.1M         | −$5.2M | −$5.2M     | −$5.3M | −$5.2M | −$5.0M              | −$5.6M                                | −$5.5M                   | −$5.3M to −$5.2M | −$5.2M   | deficit everywhere |
| California        | ACC              | $13.6M         | −$5.8M | −$4.9M     | −$5.1M | −$6.0M | −$5.0M              | −$5.0M                                | −$4.5M                   | −$6.0M to −$4.9M | −$5.5M   | deficit everywhere |
| UCF               | Big 12           | $13.3M         | −$6.5M | −$7.0M     | −$7.1M | −$6.4M | −$6.0M              | −$6.4M                                | −$6.8M                   | −$7.1M to −$6.4M | −$6.7M   | deficit everywhere |
| Rutgers           | Big Ten          | $15.3M         | −$7.0M | −$7.6M     | −$7.3M | −$6.6M | −$7.1M              | −$7.0M                                | −$6.9M                   | −$7.6M to −$6.6M | −$7.2M   | deficit everywhere |
| Arkansas          | SEC              | $15.0M         | −$6.9M | −$7.4M     | −$7.2M | −$7.1M | −$7.4M              | −$8.4M                                | −$8.5M                   | −$7.4M to −$6.9M | −$7.2M   | deficit everywhere |
| Texas A&M         | SEC              | $21.7M         | −$9.0M | −$6.5M     | −$8.0M | −$7.9M | −$5.5M              | −$0.8M                                | −$1.2M                   | −$9.0M to −$6.5M | −$8.0M   | deficit everywhere |
