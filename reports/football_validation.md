# Football model review

Stress tests for the football models before reading insights off them. Method: [`src/nilmodel/football_validation.py`](../src/nilmodel/football_validation.py). Rerun with `nil validate-football`.

## Verdicts

| output                                                 | status           | evidence                                                                                                                                                                                       |
|:-------------------------------------------------------|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Offer check: revenue share, inside the published range | Ready            | Held-out published values are placed within 1.4 percentile points on average.                                                                                                                  |
| Offer check: NIL Go                                    | Use with caution | Held-out values miss by 12 percentile points: flat payment tiers and wide gaps make NIL percentiles coarse.                                                                                    |
| Anything past the published 90th                       | Use with caution | The A4 quarterback revenue-share 99th is $2.3M at the central assumption and up to $6.4M under the most generous total; NIL $3.2M to $6.7M. Quote ranges.                                      |
| Floor on A4 program spending                           | Ready            | Needs no model: it follows from the published percentiles.                                                                                                                                     |
| Roster market value, program level                     | Ready            | Program rankings hold at a rank correlation of 0.96 or better under other assumptions (median change 5%); each value carries a 29%-wide range.                                                 |
| Roster surplus, program level                          | Ready            | 57 of 68 programs keep their sign in 90% of bootstrap resamples; shuffled rosters explain nothing (placebo R² -0.08 against 0.65).                                                             |
| On-field value across seasons                          | Ready            | Fit on 2025, the model predicts 2026 team ratings at R² 0.62 to 0.65 (correlation 0.81), as well as fitting 2026 itself.                                                                       |
| Position values                                        | Use with caution | Quarterback (4.4 to 7.4 points), offensive line, linebacker and running back are stable; defensive backs get zero in 74% of resamples and wide receivers in 20%, so those two can't be valued. |
| Comparisons within one conference                      | Use with caution | Predicting a held-out conference correlates 0.47 (Big 12) to 0.86 (SEC): rankings across FBS are firmer than within a conference.                                                              |
| Pre-season market value as a guide to results          | Use with caution | Correlates 0.59 with how A4 teams have played: it explains about 35% of it.                                                                                                                    |
| Player-score weights                                   | Not ready        | The 2025 fit weights production 0.9 / rating 0.1 / class year 0.0; the 2026 fit 0.4 / 0.1 / 0.5. Don't read meaning into the weights.                                                          |
| Individual player values                               | Not ready        | No individual contracts exist to test against, so only program totals are shown.                                                                                                               |

## Quality gates

The weekly job stops before publishing when one fails.

| check                                                                              |   value |   threshold | passed   | note                |
|:-----------------------------------------------------------------------------------|--------:|------------:|:---------|:--------------------|
| A4 rosters within 5% of the CSC's rostered count                                   |    0.01 |        0.05 | pass     |                     |
| At least 60% of A4 players have a recruiting or portal rating                      |    0.74 |        0.60 | pass     |                     |
| Every published rating explained out of sample (R² at least 0.45)                  |    0.59 |        0.45 | pass     |                     |
| Shuffled rosters explain nothing (placebo R² at most 0.15)                         |    0.05 |        0.15 | pass     |                     |
| Last season's model predicts this season (R² at least 0.40)                        |    0.62 |        0.40 | pass     |                     |
| At least 75% of programs keep one surplus sign under all four ratings              |    0.91 |        0.75 | pass     |                     |
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
| sp       | SP+      |   0.616 |         -0.080 |        -0.005 |
| fpi      | ESPN FPI |   0.717 |         -0.062 |         0.001 |
| srs      | SRS      |   0.675 |         -0.129 |         0.053 |
| elo      | Elo      |   0.592 |         -0.042 |         0.032 |

Leave one conference out (correlation of predicted and actual ratings):

| held_out   |   elo |   fpi |   sp |   srs |
|:-----------|------:|------:|-----:|------:|
| ACC        |  0.49 |  0.58 | 0.57 |  0.59 |
| Big 12     |  0.42 |  0.52 | 0.49 |  0.46 |
| Big Ten    |  0.70 |  0.83 | 0.76 |  0.69 |
| Non-A4     |  0.61 |  0.62 | 0.59 |  0.57 |
| SEC        |  0.78 |  0.88 | 0.88 |  0.91 |

Position values, bootstrap over teams (200 resamples, four ratings): average points per team from each group, median and 10th to 90th percentile.

| group             |   median |   low |   high |   zero_share |
|:------------------|---------:|------:|-------:|-------------:|
| Quarterback       |     5.95 |  4.43 |   7.45 |         0.00 |
| Running Back      |     2.28 |  1.44 |   3.04 |         0.00 |
| Wide Receiver     |     1.38 |  0.00 |   3.35 |         0.20 |
| Tight End         |     1.40 |  0.44 |   2.24 |         0.04 |
| Offensive Lineman |     2.91 |  1.90 |   3.88 |         0.00 |
| Defensive Lineman |     2.96 |  1.37 |   4.87 |         0.01 |
| Linebacker        |     3.27 |  1.53 |   5.00 |         0.00 |
| Defensive Back    |     0.00 |  0.00 |   0.64 |         0.74 |
| Kicker            |     0.52 |  0.00 |   1.26 |         0.23 |
| Punter            |     1.02 |  0.47 |   1.67 |         0.01 |

Out of season: fit on 2025 (136 teams, weights {'production': 0.9, 'rating': 0.1, 'experience': 0.0}, CV R² 0.68), predicting 2026.

| target                               |   teams |    r2 |   corr |
|:-------------------------------------|--------:|------:|-------:|
| SP+ 2026                             |     138 | 0.621 |  0.791 |
| median of the four published ratings |     138 | 0.647 |  0.813 |

## Program surplus under resampling

| team              | surplus_median   | surplus_low   | surplus_high   |   rank_median |   rank_low |   rank_high | sign_stable   |
|:------------------|:-----------------|:--------------|:---------------|--------------:|-----------:|------------:|:--------------|
| LSU               | $+6.7M           | $+6.1M        | $+7.5M         |             1 |          1 |           3 | True          |
| Alabama           | $+6.4M           | $+5.3M        | $+7.3M         |             2 |          1 |           4 | True          |
| Kentucky          | $+6.1M           | $+5.3M        | $+6.8M         |             3 |          2 |           4 | True          |
| Louisville        | $+5.5M           | $+4.7M        | $+6.2M         |             4 |          2 |           8 | True          |
| Missouri          | $+4.8M           | $+4.4M        | $+5.3M         |             7 |          5 |           9 | True          |
| Notre Dame        | $+4.8M           | $+4.0M        | $+5.6M         |             6 |          4 |          10 | True          |
| SMU               | $+4.6M           | $+3.7M        | $+5.3M         |             8 |          5 |          12 | True          |
| Duke              | $+4.4M           | $+3.2M        | $+5.8M         |             9 |          4 |          13 | True          |
| North Carolina    | $+4.3M           | $+3.3M        | $+5.2M         |             9 |          5 |          13 | True          |
| Miami             | $+4.1M           | $+3.3M        | $+5.0M         |            10 |          7 |          14 | True          |
| Utah              | $+4.1M           | $+3.5M        | $+4.9M         |            10 |          7 |          12 | True          |
| Oklahoma State    | $+3.7M           | $+2.7M        | $+4.7M         |            12 |          7 |          15 | True          |
| Northwestern      | $+3.7M           | $+2.9M        | $+4.6M         |            12 |          7 |          14 | True          |
| Virginia Tech     | $+3.3M           | $+2.4M        | $+4.3M         |            13 |          9 |          18 | True          |
| Cincinnati        | $+2.5M           | $+1.8M        | $+3.3M         |            17 |         14 |          20 | True          |
| Texas Tech        | $+2.5M           | $+1.9M        | $+3.1M         |            17 |         14 |          20 | True          |
| Houston           | $+2.3M           | $+1.5M        | $+3.1M         |            18 |         14 |          22 | True          |
| South Carolina    | $+2.0M           | $+1.3M        | $+3.0M         |            19 |         14 |          23 | True          |
| Tennessee         | $+1.9M           | $+1.2M        | $+2.9M         |            20 |         15 |          25 | True          |
| Wake Forest       | $+1.9M           | $+0.9M        | $+2.8M         |            20 |         15 |          26 | True          |
| Ohio State        | $+1.6M           | $+0.8M        | $+2.3M         |            21 |         17 |          26 | True          |
| Arizona           | $+1.5M           | $+0.5M        | $+2.3M         |            23 |         17 |          28 | True          |
| Georgia           | $+1.4M           | $+0.4M        | $+2.3M         |            23 |         18 |          29 | True          |
| Georgia Tech      | $+1.1M           | $+0.1M        | $+2.3M         |            24 |         17 |          31 | True          |
| Syracuse          | $+1.0M           | $+0.0M        | $+1.8M         |            26 |         20 |          32 | True          |
| Indiana           | $+1.0M           | $+0.0M        | $+1.7M         |            26 |         21 |          32 | True          |
| Illinois          | $+0.9M           | $+0.1M        | $+1.7M         |            26 |         22 |          31 | True          |
| Penn State        | $+0.8M           | $-0.1M        | $+1.4M         |            27 |         22 |          33 | False         |
| West Virginia     | $+0.7M           | $-0.1M        | $+1.7M         |            27 |         21 |          34 | False         |
| Nebraska          | $+0.1M           | $-0.5M        | $+0.8M         |            31 |         26 |          37 | False         |
| Stanford          | $+0.1M           | $-0.4M        | $+0.7M         |            31 |         27 |          35 | False         |
| TCU               | $-0.2M           | $-1.1M        | $+0.7M         |            33 |         27 |          43 | False         |
| UCLA              | $-0.2M           | $-0.9M        | $+0.4M         |            34 |         30 |          41 | False         |
| Mississippi State | $-0.3M           | $-0.8M        | $+0.2M         |            34 |         30 |          39 | False         |
| BYU               | $-0.3M           | $-0.8M        | $+0.3M         |            34 |         30 |          40 | False         |
| Texas             | $-0.6M           | $-1.1M        | $+0.0M         |            37 |         31 |          43 | False         |
| Pittsburgh        | $-0.7M           | $-1.4M        | $-0.2M         |            39 |         33 |          46 | True          |
| Florida           | $-0.7M           | $-1.6M        | $+0.1M         |            39 |         31 |          49 | False         |
| Wisconsin         | $-0.7M           | $-1.6M        | $+0.1M         |            39 |         31 |          48 | False         |
| Oregon            | $-0.8M           | $-1.4M        | $-0.2M         |            40 |         33 |          46 | True          |
| USC               | $-0.9M           | $-1.5M        | $-0.2M         |            40 |         34 |          49 | True          |
| Iowa              | $-1.1M           | $-1.6M        | $-0.4M         |            43 |         35 |          50 | True          |
| Washington        | $-1.1M           | $-1.6M        | $-0.7M         |            44 |         37 |          48 | True          |
| Auburn            | $-1.2M           | $-1.8M        | $-0.4M         |            44 |         36 |          50 | True          |
| Purdue            | $-1.2M           | $-1.6M        | $-0.8M         |            44 |         39 |          49 | True          |
| Kansas            | $-1.2M           | $-1.9M        | $-0.5M         |            45 |         37 |          51 | True          |
| Iowa State        | $-1.2M           | $-1.8M        | $-0.6M         |            44 |         37 |          51 | True          |
| Oklahoma          | $-1.4M           | $-2.1M        | $-0.8M         |            47 |         40 |          52 | True          |
| Baylor            | $-1.4M           | $-2.0M        | $-0.7M         |            46 |         38 |          51 | True          |
| Florida State     | $-1.5M           | $-2.2M        | $-1.0M         |            48 |         41 |          52 | True          |
| Kansas State      | $-1.7M           | $-2.1M        | $-1.2M         |            49 |         45 |          52 | True          |
| Arizona State     | $-2.0M           | $-2.8M        | $-1.3M         |            52 |         45 |          54 | True          |
| Vanderbilt        | $-2.3M           | $-2.9M        | $-1.9M         |            53 |         51 |          55 | True          |
| NC State          | $-3.0M           | $-3.5M        | $-2.5M         |            55 |         53 |          58 | True          |
| Clemson           | $-3.1M           | $-3.6M        | $-2.5M         |            56 |         53 |          59 | True          |
| Maryland          | $-3.3M           | $-3.9M        | $-2.8M         |            57 |         55 |          60 | True          |
| Ole Miss          | $-3.3M           | $-3.8M        | $-2.9M         |            57 |         55 |          60 | True          |
| Michigan          | $-3.3M           | $-4.0M        | $-2.7M         |            57 |         54 |          60 | True          |
| Colorado          | $-3.4M           | $-4.4M        | $-2.7M         |            58 |         54 |          61 | True          |
| Boston College    | $-3.6M           | $-4.5M        | $-2.6M         |            59 |         54 |          61 | True          |
| Michigan State    | $-4.1M           | $-4.6M        | $-3.6M         |            61 |         58 |          61 | True          |
| California        | $-5.2M           | $-5.9M        | $-4.5M         |            63 |         62 |          65 | True          |
| Texas A&M         | $-5.5M           | $-6.3M        | $-4.7M         |            65 |         62 |          67 | True          |
| UCF               | $-5.5M           | $-6.2M        | $-4.6M         |            64 |         62 |          67 | True          |
| Virginia          | $-5.6M           | $-6.1M        | $-5.1M         |            64 |         63 |          67 | True          |
| Minnesota         | $-5.7M           | $-6.0M        | $-5.2M         |            65 |         63 |          67 | True          |
| Rutgers           | $-5.9M           | $-6.5M        | $-5.1M         |            66 |         63 |          67 | True          |
| Arkansas          | $-6.8M           | $-7.4M        | $-6.4M         |            68 |         67 |          68 | True          |
