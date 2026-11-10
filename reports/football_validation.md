# Football model review

Stress tests for the football models before reading insights off them. Method: [`src/nilmodel/football_validation.py`](../src/nilmodel/football_validation.py). Rerun with `nil validate-football`.

## Verdicts

| output                                                 | status           | evidence                                                                                                                                                                                                                                           |
|:-------------------------------------------------------|:-----------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Offer check: revenue share, inside the published range | Ready            | Held-out published values are placed within 1.4 percentile points on average.                                                                                                                                                                      |
| Offer check: NIL Go                                    | Use with caution | Held-out values miss by 12 percentile points: flat payment tiers and wide gaps make NIL percentiles coarse.                                                                                                                                        |
| Anything past the published 90th                       | Use with caution | The A4 quarterback revenue-share 99th is $2.3M at the central assumption and up to $6.4M under the most generous total; NIL $3.2M to $6.7M. Quote ranges.                                                                                          |
| Floor on A4 program spending                           | Ready            | Needs no model: it follows from the published percentiles.                                                                                                                                                                                         |
| Roster market value, program level                     | Ready            | Program rankings hold at a rank correlation of 0.96 or better under other assumptions (median change 5%); each value carries a 29%-wide range.                                                                                                     |
| Roster surplus, program level                          | Ready            | 56 of 68 programs keep their sign in 90% of bootstrap resamples; shuffled rosters explain nothing (placebo R² -0.05 against 0.64).                                                                                                                 |
| On-field value across seasons                          | Ready            | Fit on 2025, the model predicts 2026 team ratings at R² 0.62 to 0.65 (correlation 0.81), as well as fitting 2026 itself.                                                                                                                           |
| Position values                                        | Use with caution | Quarterback (4.7 to 7.8 points), offensive line, linebacker and running back are stable; defensive backs get zero in 51% of resamples and wide receivers in 26%, so those two can't be valued.                                                     |
| Comparisons within one conference                      | Use with caution | Predicting a held-out conference correlates 0.45 (Big 12) to 0.85 (SEC): rankings across FBS are firmer than within a conference.                                                                                                                  |
| Pre-season market value as a guide to results          | Use with caution | Correlates 0.59 with how A4 teams have played: it explains about 35% of it.                                                                                                                                                                        |
| Player-score weights                                   | Use with caution | One set fit on 2025 and 2026 together, each season on its own rosters: production 0.9 / rating 0.1 / class year 0.0. Against each rating's own best for this season it gives up at most 0.02 R². Read it as production first, not as exact shares. |
| Individual player values                               | Not ready        | No individual contracts exist to test against, so only program totals are shown.                                                                                                                                                                   |

## Quality gates

The weekly job stops before publishing when one fails.

| check                                                                              |   value |   threshold | passed   | note                |
|:-----------------------------------------------------------------------------------|--------:|------------:|:---------|:--------------------|
| A4 rosters within 5% of the CSC's rostered count                                   |    0.01 |        0.05 | pass     |                     |
| At least 60% of A4 players have a recruiting or portal rating                      |    0.74 |        0.60 | pass     |                     |
| Every published rating explained out of sample (R² at least 0.45)                  |    0.59 |        0.45 | pass     |                     |
| Shuffled rosters explain nothing (placebo R² at most 0.15)                         |    0.04 |        0.15 | pass     |                     |
| Last season's model predicts this season (R² at least 0.40)                        |    0.62 |        0.40 | pass     |                     |
| At least 75% of programs keep one surplus sign under all four ratings              |    0.85 |        0.75 | pass     |                     |
| Program surplus ranks hold from the last snapshot (rank correlation at least 0.80) |         |        0.80 | pass     | no earlier snapshot |

## Offer benchmark on football

Mean, median and 90th-percentile miss in percentile points, leave-one-out.

| report        | test         | method    |   points |   mean |   median |   p90 |
|:--------------|:-------------|:----------|---------:|-------:|---------:|------:|
| nil_go        | loo_interior | linear    |       57 |  11.74 |    10.98 | 23.42 |
| nil_go        | loo_interior | lognormal |       57 |  16.00 |     9.77 | 46.27 |
| nil_go        | loo_interior | pchip     |       57 |  12.40 |    14.52 | 20.63 |
| nil_go        | loo_tail     | linear    |       42 |  10.53 |    10.00 | 15.00 |
| nil_go        | loo_tail     | lognormal |       42 |  12.41 |     9.94 | 27.85 |
| nil_go        | loo_tail     | pchip     |       42 |  10.53 |    10.00 | 15.00 |
| revenue_share | cross        | linear    |       56 |   1.19 |     0.93 |  2.50 |
| revenue_share | cross        | lognormal |       56 |   2.13 |     1.93 |  4.29 |
| revenue_share | cross        | pchip     |       56 |   1.21 |     0.97 |  2.39 |
| revenue_share | loo_interior | linear    |      115 |   1.39 |     1.01 |  2.87 |
| revenue_share | loo_interior | lognormal |      115 |   2.46 |     1.85 |  5.00 |
| revenue_share | loo_interior | pchip     |      115 |   1.36 |     1.01 |  2.75 |
| revenue_share | loo_tail     | linear    |       46 |   2.43 |     1.79 |  4.77 |
| revenue_share | loo_tail     | lognormal |       46 |   3.04 |     2.46 |  5.25 |
| revenue_share | loo_tail     | pchip     |       46 |   2.43 |     1.79 |  4.77 |

## The top of the A4 market

| report        | case    |   assumed_share |   tail_mult | qb_p95   | qb_p99   |
|:--------------|:--------|----------------:|------------:|:---------|:---------|
| revenue_share | fitted  |          nan    |        1.00 | $2.98M   | $9.40M   |
| revenue_share | central |            0.75 |        0.20 | $1.82M   | $2.29M   |
| revenue_share | low     |            0.60 |      nan    |          |          |
| revenue_share | high    |            0.88 |        0.78 | $2.60M   | $6.37M   |
| nil_go        | fitted  |          nan    |        1.00 | $2.47M   | $13.62M  |
| nil_go        | central |            0.55 |        0.44 | $1.49M   | $3.16M   |
| nil_go        | low     |            0.40 |      nan    |          |          |
| nil_go        | high    |            0.75 |        0.73 | $1.94M   | $6.73M   |

## Roster market value under other assumptions

| variant                                             |   rank_corr_with_shown |   median_abs_change |   max_abs_change |   total_change |
|:----------------------------------------------------|-----------------------:|--------------------:|-----------------:|---------------:|
| rank correlation 0.43                               |                  0.995 |               0.018 |            0.047 |         -0.001 |
| rank correlation 0.66                               |                  0.985 |               0.045 |            0.114 |          0.002 |
| weights learned from team results (0.4 / 0.1 / 0.5) |                  0.961 |               0.049 |            0.152 |          0.000 |

## On-field value

Placebo: players dealt to random teams within their position.

| source   | label    |   cv_r2 |   placebo_mean |   placebo_max |
|:---------|:---------|--------:|---------------:|--------------:|
| sp       | SP+      |   0.608 |         -0.050 |        -0.013 |
| fpi      | ESPN FPI |   0.700 |         -0.046 |         0.006 |
| srs      | SRS      |   0.666 |         -0.055 |         0.036 |
| elo      | Elo      |   0.591 |         -0.042 |         0.032 |

Leave one conference out (correlation of predicted and actual ratings):

| held_out   |   elo |   fpi |   sp |   srs |
|:-----------|------:|------:|-----:|------:|
| ACC        |  0.49 |  0.59 | 0.60 |  0.61 |
| Big 12     |  0.43 |  0.48 | 0.45 |  0.44 |
| Big Ten    |  0.70 |  0.84 | 0.77 |  0.71 |
| Non-A4     |  0.61 |  0.61 | 0.59 |  0.62 |
| SEC        |  0.78 |  0.87 | 0.86 |  0.89 |

Position values, bootstrap over teams (200 resamples, four ratings): average points per team from each group, median and 10th to 90th percentile.

| group             |   median |   low |   high |   zero_share |
|:------------------|---------:|------:|-------:|-------------:|
| Quarterback       |     6.20 |  4.69 |   7.75 |         0.00 |
| Running Back      |     2.13 |  1.32 |   2.85 |         0.00 |
| Wide Receiver     |     1.03 |  0.00 |   2.93 |         0.26 |
| Tight End         |     1.28 |  0.30 |   2.14 |         0.05 |
| Offensive Lineman |     3.84 |  2.92 |   4.66 |         0.00 |
| Defensive Lineman |     2.96 |  1.34 |   4.97 |         0.01 |
| Linebacker        |     3.26 |  1.48 |   5.02 |         0.00 |
| Defensive Back    |     0.00 |  0.00 |   1.68 |         0.51 |
| Kicker            |     0.59 |  0.00 |   1.36 |         0.21 |
| Punter            |     1.11 |  0.53 |   1.76 |         0.01 |

Out of season: fit on 2025 (136 teams, weights {'production': 0.9, 'rating': 0.1, 'experience': 0.0}, CV R² 0.68), predicting 2026.

| target                               |   teams |    r2 |   corr |
|:-------------------------------------|--------:|------:|-------:|
| SP+ 2026                             |     138 | 0.621 |  0.791 |
| median of the four published ratings |     138 | 0.647 |  0.813 |

## Program surplus under resampling

| team              | surplus_median   | surplus_low   | surplus_high   |   rank_median |   rank_low |   rank_high | sign_stable   |
|:------------------|:-----------------|:--------------|:---------------|--------------:|-----------:|------------:|:--------------|
| LSU               | $+6.7M           | $+6.0M        | $+7.2M         |             1 |          1 |           3 | True          |
| Alabama           | $+6.2M           | $+5.3M        | $+7.2M         |             2 |          1 |           5 | True          |
| SMU               | $+5.9M           | $+5.1M        | $+6.7M         |             3 |          2 |           5 | True          |
| Kentucky          | $+5.7M           | $+5.0M        | $+6.4M         |             4 |          2 |           7 | True          |
| Missouri          | $+5.1M           | $+4.6M        | $+5.5M         |             6 |          4 |           9 | True          |
| Utah              | $+5.1M           | $+4.4M        | $+5.7M         |             6 |          4 |           9 | True          |
| Miami             | $+4.9M           | $+4.2M        | $+5.7M         |             7 |          4 |          11 | True          |
| Notre Dame        | $+4.6M           | $+3.6M        | $+5.4M         |             9 |          5 |          11 | True          |
| North Carolina    | $+4.5M           | $+3.6M        | $+5.4M         |             9 |          5 |          12 | True          |
| Louisville        | $+4.2M           | $+3.4M        | $+4.9M         |            10 |          7 |          12 | True          |
| Duke              | $+4.0M           | $+2.8M        | $+5.4M         |            10 |          5 |          15 | True          |
| Northwestern      | $+3.6M           | $+2.8M        | $+4.4M         |            12 |          9 |          15 | True          |
| Oklahoma State    | $+3.2M           | $+2.2M        | $+4.2M         |            14 |         10 |          17 | True          |
| Cincinnati        | $+2.9M           | $+2.1M        | $+3.7M         |            15 |         12 |          18 | True          |
| Wake Forest       | $+2.6M           | $+1.7M        | $+3.5M         |            16 |         12 |          21 | True          |
| Virginia Tech     | $+2.6M           | $+1.8M        | $+3.6M         |            16 |         12 |          21 | True          |
| Texas Tech        | $+2.6M           | $+2.1M        | $+3.3M         |            16 |         13 |          19 | True          |
| South Carolina    | $+2.3M           | $+1.5M        | $+3.3M         |            17 |         13 |          22 | True          |
| Houston           | $+1.8M           | $+1.0M        | $+2.6M         |            21 |         16 |          26 | True          |
| Arizona           | $+1.6M           | $+0.7M        | $+2.4M         |            22 |         18 |          28 | True          |
| Indiana           | $+1.4M           | $+0.4M        | $+2.0M         |            23 |         19 |          31 | True          |
| West Virginia     | $+1.4M           | $+0.6M        | $+2.2M         |            23 |         19 |          30 | True          |
| Tennessee         | $+1.3M           | $+0.5M        | $+2.2M         |            24 |         18 |          30 | True          |
| Penn State        | $+1.3M           | $+0.5M        | $+1.9M         |            24 |         19 |          29 | True          |
| Nebraska          | $+1.2M           | $+0.6M        | $+1.8M         |            25 |         20 |          29 | True          |
| Illinois          | $+1.2M           | $+0.4M        | $+2.0M         |            24 |         20 |          31 | True          |
| Syracuse          | $+1.0M           | $-0.0M        | $+1.9M         |            26 |         20 |          33 | False         |
| Georgia Tech      | $+0.9M           | $-0.0M        | $+2.2M         |            27 |         18 |          34 | False         |
| Georgia           | $+0.8M           | $-0.2M        | $+1.8M         |            28 |         21 |          36 | False         |
| Stanford          | $+0.6M           | $+0.1M        | $+1.2M         |            29 |         25 |          33 | True          |
| Wisconsin         | $+0.4M           | $-0.3M        | $+1.1M         |            31 |         25 |          36 | False         |
| Ohio State        | $+0.4M           | $-0.5M        | $+1.2M         |            31 |         25 |          38 | False         |
| TCU               | $+0.1M           | $-0.9M        | $+0.9M         |            33 |         26 |          42 | False         |
| Iowa              | $-0.2M           | $-0.8M        | $+0.5M         |            35 |         30 |          42 | False         |
| Oklahoma          | $-0.3M           | $-0.9M        | $+0.3M         |            36 |         32 |          42 | False         |
| Mississippi State | $-0.3M           | $-0.8M        | $+0.2M         |            36 |         31 |          41 | False         |
| Iowa State        | $-0.3M           | $-0.9M        | $+0.3M         |            37 |         31 |          43 | False         |
| BYU               | $-0.4M           | $-0.9M        | $+0.1M         |            37 |         32 |          42 | False         |
| Washington        | $-0.4M           | $-0.9M        | $+0.2M         |            37 |         32 |          42 | False         |
| USC               | $-0.6M           | $-1.2M        | $-0.1M         |            39 |         34 |          46 | True          |
| Purdue            | $-0.7M           | $-1.1M        | $-0.3M         |            40 |         35 |          44 | True          |
| Pittsburgh        | $-1.0M           | $-1.6M        | $-0.5M         |            43 |         38 |          47 | True          |
| UCLA              | $-1.0M           | $-1.7M        | $-0.4M         |            43 |         37 |          48 | True          |
| Texas             | $-1.1M           | $-1.7M        | $-0.6M         |            44 |         39 |          47 | True          |
| Kansas            | $-1.2M           | $-1.9M        | $-0.4M         |            44 |         37 |          48 | True          |
| Auburn            | $-1.2M           | $-1.9M        | $-0.7M         |            45 |         40 |          48 | True          |
| Florida           | $-1.3M           | $-2.1M        | $-0.4M         |            46 |         37 |          51 | True          |
| Florida State     | $-1.6M           | $-2.2M        | $-1.0M         |            47 |         43 |          50 | True          |
| Kansas State      | $-2.0M           | $-2.4M        | $-1.6M         |            49 |         47 |          52 | True          |
| Baylor            | $-2.1M           | $-2.8M        | $-1.5M         |            50 |         47 |          53 | True          |
| Arizona State     | $-2.5M           | $-3.2M        | $-1.8M         |            52 |         48 |          56 | True          |
| Vanderbilt        | $-2.6M           | $-3.1M        | $-2.1M         |            52 |         50 |          55 | True          |
| Boston College    | $-2.7M           | $-3.7M        | $-1.7M         |            53 |         49 |          59 | True          |
| Oregon            | $-2.7M           | $-3.3M        | $-2.1M         |            53 |         49 |          55 | True          |
| NC State          | $-2.8M           | $-3.3M        | $-2.3M         |            54 |         51 |          57 | True          |
| Clemson           | $-3.4M           | $-3.9M        | $-2.9M         |            57 |         54 |          59 | True          |
| Colorado          | $-3.5M           | $-4.4M        | $-2.7M         |            58 |         54 |          61 | True          |
| Maryland          | $-3.6M           | $-4.1M        | $-3.2M         |            58 |         56 |          60 | True          |
| Michigan State    | $-3.7M           | $-4.2M        | $-3.3M         |            59 |         56 |          61 | True          |
| Ole Miss          | $-3.8M           | $-4.3M        | $-3.4M         |            59 |         57 |          61 | True          |
| Michigan          | $-4.1M           | $-4.8M        | $-3.5M         |            60 |         58 |          62 | True          |
| Minnesota         | $-4.9M           | $-5.4M        | $-4.5M         |            62 |         62 |          65 | True          |
| Virginia          | $-5.2M           | $-5.7M        | $-4.7M         |            63 |         62 |          65 | True          |
| California        | $-5.5M           | $-6.2M        | $-4.9M         |            65 |         62 |          66 | True          |
| Texas A&M         | $-5.5M           | $-6.4M        | $-4.7M         |            64 |         62 |          67 | True          |
| UCF               | $-5.9M           | $-6.6M        | $-4.9M         |            65 |         63 |          67 | True          |
| Rutgers           | $-6.6M           | $-7.3M        | $-5.9M         |            67 |         66 |          68 | True          |
| Arkansas          | $-7.4M           | $-7.9M        | $-6.8M         |            68 |         67 |          68 | True          |
