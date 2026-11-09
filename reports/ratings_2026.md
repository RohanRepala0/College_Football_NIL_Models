# Surplus value against several ratings, 2026

The surplus model asks how much of each team's rating its players explain. This runs the same fit against six ratings instead of SP+ alone, each as a team total on every position group, with the player-score weights chosen by cross-validation for that rating, and prices surplus under each. Method: [`src/nilmodel/ratings.py`](../src/nilmodel/ratings.py).

- **2026 results only** is fit here from 562 completed FBS-vs-FBS games through week 10 (last game 2026-11-08), margins capped at 28; home edge 2.6 points. No prior.
- **Your model** is the team rating implied by CollegeFootballRatings2026's posted model margins, 566 games, week 01 to week 08; home edge 2.5. Those files stop at week 8.

- SP+, ESPN FPI, SRS and Elo are CollegeFootballData's current 2026 ratings. Player production is this season's.

## How well each rating is explained

Out-of-sample R² (5 folds over 138 FBS teams). "Recruiting + class only" leaves production out: a rating that leans on a preseason prior built from recruiting should be explained better by it.

| rating                 | preseason prior                       | weights (production / recruiting / class year)   |   R² learned |   R² prior weights |   R² production only |   R² recruiting + class only |   QB points |   DL points | $ per point   |
|:-----------------------|:--------------------------------------|:-------------------------------------------------|-------------:|-------------------:|---------------------:|-----------------------------:|------------:|------------:|:--------------|
| SP+                    | yes, fading                           | 0.4 / 0.1 / 0.5                                  |         0.62 |               0.53 |                 0.59 |                         0.38 |        6.50 |        3.10 | $553,327      |
| ESPN FPI               | yes                                   | 0.4 / 0.1 / 0.5                                  |         0.72 |               0.66 |                 0.68 |                         0.52 |        5.30 |        2.90 | $524,491      |
| SRS                    | no                                    | 0.4 / 0.1 / 0.5                                  |         0.68 |               0.58 |                 0.65 |                         0.44 |        6.00 |        2.20 | $536,165      |
| Elo                    | carries over last season              | 0.7 / 0.1 / 0.2                                  |         0.59 |               0.49 |                 0.58 |                         0.38 |        5.90 |        3.40 | $570,627      |
| 2026 results only      | no                                    | 0.5 / 0.1 / 0.4                                  |         0.67 |               0.57 |                 0.65 |                         0.45 |        6.00 |        2.60 | $524,339      |
| Your model (weeks 1-8) | market and SP+/FEI, which have priors | 0.6 / 0.3 / 0.1                                  |         0.74 |               0.73 |                 0.68 |                         0.63 |        3.20 |        2.40 | $607,738      |

## Do the ratings agree on surplus?

Rank correlation of program surplus between ratings:

|                        |   SP+ |   ESPN FPI |   SRS |   Elo |   2026 results only |   Your model (weeks 1-8) |
|:-----------------------|------:|-----------:|------:|------:|--------------------:|-------------------------:|
| SP+                    |  1.00 |       0.97 |  0.99 |  0.96 |                0.97 |                     0.74 |
| ESPN FPI               |  0.97 |       1.00 |  0.98 |  0.96 |                0.97 |                     0.84 |
| SRS                    |  0.99 |       0.98 |  1.00 |  0.96 |                0.99 |                     0.76 |
| Elo                    |  0.96 |       0.96 |  0.96 |  1.00 |                0.97 |                     0.73 |
| 2026 results only      |  0.97 |       0.97 |  0.99 |  0.97 |                1.00 |                     0.72 |
| Your model (weeks 1-8) |  0.74 |       0.84 |  0.76 |  0.73 |                0.72 |                     1.00 |

- **25** programs show a surplus under every rating and **27** a deficit under every rating; **16** depend on the rating. Under the five public ratings alone, 62 of 68 keep one sign.

## Every A4 program

Sorted by median surplus across ratings.

| program           | conference       | market value   | SP+    | ESPN FPI   | SRS    | Elo    | 2026 results only   | Your model (weeks 1-8)   | range            | median   | call               |
|:------------------|:-----------------|:---------------|:-------|:-----------|:-------|:-------|:--------------------|:-------------------------|:-----------------|:---------|:-------------------|
| LSU               | SEC              | $22.1M         | +$6.6M | +$7.0M     | +$6.2M | +$7.5M | +$6.0M              | +$9.6M                   | +$6.0M to +$9.6M | +$6.8M   | surplus everywhere |
| Alabama           | SEC              | $21.1M         | +$6.3M | +$6.8M     | +$6.8M | +$6.4M | +$6.8M              | +$8.8M                   | +$6.3M to +$8.8M | +$6.8M   | surplus everywhere |
| Kentucky          | SEC              | $14.6M         | +$5.9M | +$6.2M     | +$6.5M | +$5.4M | +$6.2M              | +$6.6M                   | +$5.4M to +$6.6M | +$6.2M   | surplus everywhere |
| Missouri          | SEC              | $15.8M         | +$4.4M | +$4.9M     | +$4.9M | +$4.9M | +$5.0M              | +$5.2M                   | +$4.4M to +$5.2M | +$4.9M   | surplus everywhere |
| Louisville        | ACC              | $14.2M         | +$6.8M | +$4.9M     | +$5.8M | +$4.5M | +$4.9M              | +$4.1M                   | +$4.1M to +$6.8M | +$4.9M   | surplus everywhere |
| Notre Dame        | FBS Independents | $21.7M         | +$4.9M | +$4.9M     | +$4.7M | +$5.8M | +$4.5M              | +$7.2M                   | +$4.5M to +$7.2M | +$4.9M   | surplus everywhere |
| Utah              | Big 12           | $14.3M         | +$4.2M | +$3.6M     | +$4.4M | +$4.6M | +$4.5M              | +$0.9M                   | +$0.9M to +$4.6M | +$4.3M   | surplus everywhere |
| SMU               | ACC              | $15.4M         | +$4.5M | +$4.2M     | +$4.3M | +$6.3M | +$4.1M              | +$3.3M                   | +$3.3M to +$6.3M | +$4.2M   | surplus everywhere |
| North Carolina    | ACC              | $14.0M         | +$4.2M | +$4.3M     | +$4.3M | +$3.9M | +$4.6M              | +$3.1M                   | +$3.1M to +$4.6M | +$4.2M   | surplus everywhere |
| Duke              | ACC              | $13.1M         | +$4.9M | +$3.5M     | +$4.9M | +$4.1M | +$4.3M              | +$0.7M                   | +$0.7M to +$4.9M | +$4.2M   | surplus everywhere |
| Miami             | ACC              | $19.7M         | +$3.4M | +$4.8M     | +$3.7M | +$4.3M | +$4.0M              | +$6.2M                   | +$3.4M to +$6.2M | +$4.1M   | surplus everywhere |
| Northwestern      | Big Ten          | $14.8M         | +$4.4M | +$2.9M     | +$4.0M | +$3.5M | +$4.2M              | +$0.4M                   | +$0.4M to +$4.4M | +$3.7M   | surplus everywhere |
| Virginia Tech     | ACC              | $16.0M         | +$4.0M | +$3.2M     | +$3.6M | +$2.6M | +$3.5M              | +$2.7M                   | +$2.6M to +$4.0M | +$3.3M   | surplus everywhere |
| Oklahoma State    | Big 12           | $15.3M         | +$4.7M | +$2.8M     | +$4.5M | +$2.9M | +$3.6M              | +$0.6M                   | +$0.6M to +$4.7M | +$3.3M   | surplus everywhere |
| Texas Tech        | Big 12           | $16.8M         | +$2.7M | +$2.0M     | +$2.7M | +$3.5M | +$2.8M              | +$1.1M                   | +$1.1M to +$3.5M | +$2.7M   | surplus everywhere |
| Cincinnati        | Big 12           | $13.0M         | +$3.1M | +$1.3M     | +$2.7M | +$2.9M | +$2.7M              | −$2.5M                   | −$2.5M to +$3.1M | +$2.7M   | depends on rating  |
| South Carolina    | SEC              | $17.5M         | +$2.0M | +$2.3M     | +$2.1M | +$2.7M | +$2.4M              | +$3.1M                   | +$2.0M to +$3.1M | +$2.3M   | surplus everywhere |
| Tennessee         | SEC              | $18.8M         | +$2.1M | +$2.0M     | +$2.2M | +$2.3M | +$1.6M              | +$4.4M                   | +$1.6M to +$4.4M | +$2.1M   | surplus everywhere |
| Georgia           | SEC              | $24.3M         | +$0.9M | +$1.9M     | +$2.0M | +$1.4M | +$2.2M              | +$4.8M                   | +$0.9M to +$4.8M | +$2.0M   | surplus everywhere |
| Houston           | Big 12           | $14.4M         | +$2.9M | +$1.9M     | +$2.5M | +$1.0M | +$2.0M              | +$0.9M                   | +$0.9M to +$2.9M | +$2.0M   | surplus everywhere |
| Ohio State        | Big Ten          | $21.9M         | +$1.5M | +$2.3M     | +$1.9M | +$0.5M | +$0.9M              | +$6.6M                   | +$0.5M to +$6.6M | +$1.7M   | surplus everywhere |
| Arizona           | Big 12           | $12.7M         | +$1.7M | +$1.3M     | +$1.7M | +$1.0M | +$1.7M              | +$0.3M                   | +$0.3M to +$1.7M | +$1.5M   | surplus everywhere |
| Wake Forest       | ACC              | $13.0M         | +$2.6M | +$1.1M     | +$1.3M | +$2.8M | +$1.5M              | −$1.6M                   | −$1.6M to +$2.8M | +$1.4M   | depends on rating  |
| Georgia Tech      | ACC              | $14.2M         | +$0.8M | +$1.5M     | +$0.6M | +$1.3M | +$0.9M              | +$1.9M                   | +$0.6M to +$1.9M | +$1.1M   | surplus everywhere |
| Syracuse          | ACC              | $15.5M         | +$0.6M | +$1.3M     | +$0.6M | +$0.9M | +$1.0M              | +$1.9M                   | +$0.6M to +$1.9M | +$0.9M   | surplus everywhere |
| West Virginia     | Big 12           | $15.1M         | +$0.8M | +$0.4M     | +$0.9M | +$1.1M | +$1.4M              | −$1.9M                   | −$1.9M to +$1.4M | +$0.9M   | depends on rating  |
| Illinois          | Big Ten          | $13.5M         | +$0.6M | +$1.1M     | +$1.0M | +$0.2M | +$1.3M              | −$0.3M                   | −$0.3M to +$1.3M | +$0.8M   | depends on rating  |
| Penn State        | Big Ten          | $16.7M         | +$0.5M | +$0.8M     | +$0.8M | +$1.8M | +$0.9M              | +$0.7M                   | +$0.5M to +$1.8M | +$0.8M   | surplus everywhere |
| Indiana           | Big Ten          | $14.5M         | +$0.6M | +$1.0M     | +$0.5M | +$0.6M | +$0.9M              | +$0.1M                   | +$0.1M to +$1.0M | +$0.6M   | surplus everywhere |
| Stanford          | ACC              | $12.4M         | −$0.1M | −$0.0M     | +$0.4M | +$0.4M | +$0.6M              | −$1.6M                   | −$1.6M to +$0.6M | +$0.2M   | depends on rating  |
| Nebraska          | Big Ten          | $16.6M         | −$0.1M | +$0.2M     | −$0.0M | +$1.5M | −$0.1M              | +$0.5M                   | −$0.1M to +$1.5M | +$0.1M   | depends on rating  |
| UCLA              | Big Ten          | $16.8M         | +$0.1M | −$0.5M     | +$0.2M | −$0.2M | −$0.0M              | −$0.3M                   | −$0.5M to +$0.2M | −$0.1M   | depends on rating  |
| Mississippi State | SEC              | $16.2M         | −$0.3M | −$0.2M     | −$0.6M | −$0.3M | −$0.6M              | −$0.3M                   | −$0.6M to −$0.2M | −$0.3M   | deficit everywhere |
| TCU               | Big 12           | $13.5M         | −$0.4M | +$0.0M     | −$0.0M | −$1.0M | −$0.2M              | −$0.7M                   | −$1.0M to +$0.0M | −$0.3M   | depends on rating  |
| BYU               | Big 12           | $12.4M         | +$0.2M | −$0.6M     | −$0.4M | −$0.4M | −$0.8M              | −$1.4M                   | −$1.4M to +$0.2M | −$0.5M   | depends on rating  |
| Oregon            | Big Ten          | $19.5M         | −$0.9M | −$0.2M     | −$0.2M | −$2.6M | −$1.2M              | +$3.5M                   | −$2.6M to +$3.5M | −$0.5M   | depends on rating  |
| Texas             | SEC              | $22.7M         | −$0.8M | −$0.1M     | −$1.2M | −$0.3M | −$0.9M              | +$3.5M                   | −$1.2M to +$3.5M | −$0.6M   | depends on rating  |
| Florida           | SEC              | $18.3M         | −$0.7M | −$0.4M     | −$0.3M | −$0.8M | −$0.9M              | +$1.1M                   | −$0.9M to +$1.1M | −$0.6M   | depends on rating  |
| Wisconsin         | Big Ten          | $14.7M         | −$1.1M | −$0.8M     | −$0.6M | +$0.5M | +$0.1M              | −$1.9M                   | −$1.9M to +$0.5M | −$0.7M   | depends on rating  |
| Pittsburgh        | ACC              | $12.9M         | −$0.6M | −$0.9M     | −$0.7M | −$1.4M | −$0.5M              | −$2.4M                   | −$2.4M to −$0.5M | −$0.8M   | deficit everywhere |
| USC               | Big Ten          | $19.7M         | −$1.0M | −$0.7M     | −$1.4M | −$0.1M | −$1.7M              | +$1.3M                   | −$1.7M to +$1.3M | −$0.9M   | depends on rating  |
| Washington        | Big Ten          | $14.2M         | −$1.8M | −$0.6M     | −$1.2M | −$1.6M | −$0.9M              | −$0.2M                   | −$1.8M to −$0.2M | −$1.1M   | deficit everywhere |
| Iowa State        | Big 12           | $13.6M         | −$1.4M | −$1.5M     | −$0.9M | −$0.5M | −$0.3M              | −$3.9M                   | −$3.9M to −$0.3M | −$1.1M   | deficit everywhere |
| Auburn            | SEC              | $17.0M         | −$1.2M | −$1.0M     | −$1.2M | −$1.5M | −$0.6M              | −$1.2M                   | −$1.5M to −$0.6M | −$1.2M   | deficit everywhere |
| Iowa              | Big Ten          | $13.0M         | −$1.3M | −$1.2M     | −$1.2M | −$0.0M | −$0.7M              | −$2.9M                   | −$2.9M to −$0.0M | −$1.2M   | deficit everywhere |
| Purdue            | Big Ten          | $13.2M         | −$1.2M | −$1.4M     | −$1.1M | −$1.3M | −$1.0M              | −$3.1M                   | −$3.1M to −$1.0M | −$1.2M   | deficit everywhere |
| Oklahoma          | SEC              | $17.7M         | −$2.0M | −$1.1M     | −$2.0M | −$0.6M | −$1.4M              | −$0.6M                   | −$2.0M to −$0.6M | −$1.3M   | deficit everywhere |
| Florida State     | ACC              | $15.1M         | −$1.5M | −$1.4M     | −$1.2M | −$2.4M | −$1.2M              | −$1.1M                   | −$2.4M to −$1.1M | −$1.3M   | deficit everywhere |
| Kansas            | Big 12           | $14.2M         | −$1.0M | −$1.6M     | −$1.9M | −$0.4M | −$1.4M              | −$3.0M                   | −$3.0M to −$0.4M | −$1.5M   | deficit everywhere |
| Baylor            | Big 12           | $14.3M         | −$0.8M | −$1.7M     | −$1.5M | −$2.1M | −$1.6M              | −$2.1M                   | −$2.1M to −$0.8M | −$1.6M   | deficit everywhere |
| Kansas State      | Big 12           | $14.6M         | −$1.1M | −$1.9M     | −$1.8M | −$1.4M | −$2.2M              | −$1.9M                   | −$2.2M to −$1.1M | −$1.8M   | deficit everywhere |
| Arizona State     | Big 12           | $14.4M         | −$1.9M | −$2.1M     | −$1.8M | −$2.5M | −$2.1M              | −$2.3M                   | −$2.5M to −$1.8M | −$2.1M   | deficit everywhere |
| Vanderbilt        | SEC              | $14.7M         | −$1.9M | −$2.7M     | −$2.4M | −$2.4M | −$2.7M              | −$2.9M                   | −$2.9M to −$1.9M | −$2.6M   | deficit everywhere |
| NC State          | ACC              | $15.5M         | −$2.7M | −$3.2M     | −$2.9M | −$2.6M | −$3.0M              | −$3.5M                   | −$3.5M to −$2.6M | −$2.9M   | deficit everywhere |
| Clemson           | ACC              | $18.6M         | −$3.7M | −$2.1M     | −$3.3M | −$3.5M | −$3.2M              | +$1.0M                   | −$3.7M to +$1.0M | −$3.2M   | depends on rating  |
| Maryland          | Big Ten          | $13.6M         | −$3.1M | −$3.3M     | −$3.0M | −$3.6M | −$3.2M              | −$3.9M                   | −$3.9M to −$3.0M | −$3.3M   | deficit everywhere |
| Ole Miss          | SEC              | $20.3M         | −$2.8M | −$3.5M     | −$3.4M | −$3.4M | −$3.9M              | −$2.4M                   | −$3.9M to −$2.4M | −$3.4M   | deficit everywhere |
| Michigan          | Big Ten          | $19.2M         | −$3.6M | −$2.4M     | −$3.2M | −$3.8M | −$3.6M              | +$1.2M                   | −$3.8M to +$1.2M | −$3.4M   | depends on rating  |
| Colorado          | Big 12           | $14.9M         | −$3.5M | −$3.2M     | −$3.6M | −$3.8M | −$3.7M              | −$1.8M                   | −$3.8M to −$1.8M | −$3.5M   | deficit everywhere |
| Boston College    | ACC              | $13.4M         | −$3.8M | −$3.9M     | −$4.2M | −$3.1M | −$3.1M              | −$5.8M                   | −$5.8M to −$3.1M | −$3.9M   | deficit everywhere |
| Michigan State    | Big Ten          | $12.2M         | −$4.5M | −$3.9M     | −$4.3M | −$3.9M | −$3.8M              | −$4.7M                   | −$4.7M to −$3.8M | −$4.1M   | deficit everywhere |
| California        | ACC              | $13.6M         | −$5.9M | −$4.5M     | −$4.6M | −$6.6M | −$4.7M              | −$3.7M                   | −$6.6M to −$3.7M | −$4.7M   | deficit everywhere |
| Texas A&M         | SEC              | $21.7M         | −$6.5M | −$4.6M     | −$6.0M | −$4.8M | −$5.6M              | −$0.6M                   | −$6.5M to −$0.6M | −$5.2M   | deficit everywhere |
| UCF               | Big 12           | $13.3M         | −$5.4M | −$5.5M     | −$5.9M | −$5.5M | −$5.7M              | −$5.8M                   | −$5.9M to −$5.4M | −$5.6M   | deficit everywhere |
| Rutgers           | Big Ten          | $15.3M         | −$5.6M | −$5.8M     | −$5.6M | −$6.6M | −$6.4M              | −$5.6M                   | −$6.6M to −$5.6M | −$5.7M   | deficit everywhere |
| Virginia          | ACC              | $15.1M         | −$5.8M | −$5.7M     | −$5.8M | −$5.4M | −$5.3M              | −$7.1M                   | −$7.1M to −$5.3M | −$5.7M   | deficit everywhere |
| Minnesota         | Big Ten          | $15.3M         | −$6.0M | −$5.5M     | −$6.0M | −$5.2M | −$5.8M              | −$5.7M                   | −$6.0M to −$5.2M | −$5.7M   | deficit everywhere |
| Arkansas          | SEC              | $15.0M         | −$6.6M | −$7.0M     | −$6.9M | −$7.4M | −$7.0M              | −$6.7M                   | −$7.4M to −$6.6M | −$6.9M   | deficit everywhere |
