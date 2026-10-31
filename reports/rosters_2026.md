# A4 roster market values, 2026

What each A4 football roster would cost in revenue share if every player were paid his position's A4 market rate at his rank. The rates are the CSC's published distributions (with the cap-calibrated tail); the ranks come from public data. **This is not what a school spends**: it is the market price of the roster, the first half of a surplus-value comparison. Team totals only; individual estimates stay in the local database. Data: CollegeFootballData, 12 API calls. Method: [`docs/ESTIMATION.md`](../docs/ESTIMATION.md).

## Rosters against the CSC

A4 players on 2026 rosters by CSC group, against the CSC's count of everyone on a 2026 roster during the calendar year. They agree within a few percent, except that the CSC leaves 162 players' positions unspecified and counts fewer defensive linemen.

| group                |   rosters_now |   csc_calendar_2026 |
|:---------------------|--------------:|--------------------:|
| Defensive Back       |          1464 |                1444 |
| Defensive Lineman    |          1243 |                1060 |
| Kicker               |           200 |                 194 |
| Linebacker           |           872 |                 858 |
| Long Snapper         |           163 |                 149 |
| Offensive Lineman    |          1337 |                1398 |
| Position Unspecified |             1 |                 162 |
| Punter               |           141 |                 131 |
| Quarterback          |           365 |                 367 |
| Running Back         |           518 |                 495 |
| Tight End            |           511 |                 496 |
| Wide Receiver        |          1029 |                 989 |

## What ranks the players

Within each group: last season's production (usage and expected points added on offense; tackles, sacks, tackles for loss, pass breakups and interceptions on defense) 45%, recruiting or portal rating 35%, class year 20%. Groups without individual production (linemen on offense, specialists) use rating 60% and class year 40%. These weights are a stated prior. A missing rating counts as the group's 10th percentile; no production last season counts as the group's lowest. Ranks are treated as tracking pay at 0.5, inside the simulation's 0.43 to 0.66 range, and that uncertainty gives each program's range.

| group                |   players | rating   | production   | transfers   |
|:---------------------|----------:|:---------|:-------------|:------------|
| Defensive Back       |      1464 | 79%      | 55%          | 19%         |
| Defensive Lineman    |      1243 | 81%      | 55%          | 22%         |
| Kicker               |       200 | 38%      | 0%           | 22%         |
| Linebacker           |       872 | 76%      | 56%          | 16%         |
| Long Snapper         |       163 | 12%      | 0%           | 16%         |
| Offensive Lineman    |      1337 | 78%      | 0%           | 18%         |
| Position Unspecified |         1 | 0%       | 0%           | 0%          |
| Punter               |       141 | 34%      | 0%           | 25%         |
| Quarterback          |       365 | 76%      | 47%          | 24%         |
| Running Back         |       518 | 74%      | 59%          | 21%         |
| Tight End            |       511 | 76%      | 40%          | 19%         |
| Wide Receiver        |      1029 | 73%      | 44%          | 21%         |

## Market value by program

Average $15.9M against a calendar-2026 cap of $21.04M. 7 rosters would cost more than the cap at market rates, so their players must take less than market in revenue share or be paid through NIL.

|   rank | program           | conference       |   players | market value   | 80% range        | vs cap   | top-5 share   |
|-------:|:------------------|:-----------------|----------:|:---------------|:-----------------|:---------|:--------------|
|      1 | Georgia           | SEC              |       128 | $24.3M         | $21.8M to $26.9M | 115%     | 18%           |
|      2 | Texas             | SEC              |       111 | $22.7M         | $20.4M to $25.0M | 108%     | 21%           |
|      3 | LSU               | SEC              |       119 | $22.1M         | $19.7M to $24.6M | 105%     | 19%           |
|      4 | Ohio State        | Big Ten          |       119 | $21.9M         | $19.4M to $24.5M | 104%     | 21%           |
|      5 | Texas A&M         | SEC              |       122 | $21.7M         | $19.4M to $24.4M | 103%     | 18%           |
|      6 | Notre Dame        | FBS Independents |       111 | $21.7M         | $19.7M to $24.0M | 103%     | 18%           |
|      7 | Alabama           | SEC              |       128 | $21.1M         | $18.7M to $23.6M | 100%     | 18%           |
|      8 | Ole Miss          | SEC              |       121 | $20.3M         | $18.1M to $22.9M | 97%      | 22%           |
|      9 | USC               | Big Ten          |       128 | $19.7M         | $17.3M to $22.1M | 94%      | 20%           |
|     10 | Miami             | ACC              |       117 | $19.7M         | $17.3M to $22.3M | 93%      | 18%           |
|     11 | Oregon            | Big Ten          |       113 | $19.5M         | $17.2M to $22.0M | 93%      | 25%           |
|     12 | Michigan          | Big Ten          |       118 | $19.2M         | $16.6M to $21.6M | 91%      | 21%           |
|     13 | Tennessee         | SEC              |       112 | $18.8M         | $16.8M to $21.0M | 89%      | 18%           |
|     14 | Clemson           | ACC              |       121 | $18.6M         | $16.5M to $20.8M | 89%      | 18%           |
|     15 | Florida           | SEC              |       117 | $18.3M         | $16.2M to $20.6M | 87%      | 17%           |
|     16 | Oklahoma          | SEC              |       114 | $17.7M         | $15.8M to $20.3M | 84%      | 19%           |
|     17 | South Carolina    | SEC              |       112 | $17.5M         | $15.5M to $19.9M | 83%      | 21%           |
|     18 | Auburn            | SEC              |       116 | $17.0M         | $15.0M to $19.8M | 81%      | 22%           |
|     19 | Texas Tech        | Big 12           |       110 | $16.8M         | $14.7M to $19.1M | 80%      | 22%           |
|     20 | UCLA              | Big Ten          |       120 | $16.8M         | $14.5M to $18.9M | 80%      | 24%           |
|     21 | Penn State        | Big Ten          |       112 | $16.7M         | $14.5M to $19.1M | 79%      | 21%           |
|     22 | Nebraska          | Big Ten          |       115 | $16.6M         | $14.6M to $19.2M | 79%      | 22%           |
|     23 | Mississippi State | SEC              |       116 | $16.2M         | $14.1M to $18.6M | 77%      | 22%           |
|     24 | Virginia Tech     | ACC              |       120 | $16.0M         | $13.8M to $18.9M | 76%      | 21%           |
|     25 | Missouri          | SEC              |       113 | $15.8M         | $13.6M to $18.0M | 75%      | 22%           |
|     26 | NC State          | ACC              |       128 | $15.5M         | $13.4M to $17.9M | 74%      | 22%           |
|     27 | Syracuse          | ACC              |       112 | $15.5M         | $13.1M to $18.0M | 74%      | 26%           |
|     28 | SMU               | ACC              |       107 | $15.4M         | $13.4M to $17.9M | 73%      | 22%           |
|     29 | Minnesota         | Big Ten          |       113 | $15.3M         | $13.2M to $17.5M | 73%      | 21%           |
|     30 | Rutgers           | Big Ten          |       134 | $15.3M         | $13.1M to $17.6M | 73%      | 21%           |
|     31 | Oklahoma State    | Big 12           |       115 | $15.3M         | $13.1M to $17.3M | 73%      | 26%           |
|     32 | Virginia          | ACC              |       122 | $15.1M         | $13.2M to $17.5M | 72%      | 23%           |
|     33 | West Virginia     | Big 12           |       126 | $15.1M         | $12.7M to $17.6M | 72%      | 21%           |
|     34 | Florida State     | ACC              |       108 | $15.1M         | $12.9M to $17.4M | 72%      | 21%           |
|     35 | Arkansas          | SEC              |       122 | $15.0M         | $12.8M to $17.3M | 71%      | 20%           |
|     36 | Colorado          | Big 12           |       106 | $14.9M         | $12.6M to $17.1M | 71%      | 22%           |
|     37 | Northwestern      | Big Ten          |       124 | $14.8M         | $12.6M to $17.0M | 70%      | 25%           |
|     38 | Wisconsin         | Big Ten          |       113 | $14.7M         | $12.8M to $17.3M | 70%      | 23%           |
|     39 | Vanderbilt        | SEC              |       117 | $14.7M         | $12.7M to $16.6M | 70%      | 21%           |
|     40 | Kansas State      | Big 12           |       112 | $14.6M         | $12.7M to $16.9M | 69%      | 24%           |
|     41 | Kentucky          | SEC              |       111 | $14.6M         | $12.8M to $16.8M | 69%      | 22%           |
|     42 | Indiana           | Big Ten          |       106 | $14.5M         | $12.7M to $16.6M | 69%      | 23%           |
|     43 | Arizona State     | Big 12           |       107 | $14.4M         | $12.2M to $16.3M | 69%      | 23%           |
|     44 | Houston           | Big 12           |       115 | $14.4M         | $12.2M to $16.5M | 68%      | 28%           |
|     45 | Baylor            | Big 12           |       115 | $14.3M         | $12.3M to $16.5M | 68%      | 25%           |
|     46 | Utah              | Big 12           |       112 | $14.3M         | $12.2M to $16.6M | 68%      | 24%           |
|     47 | Georgia Tech      | ACC              |       108 | $14.2M         | $12.4M to $16.2M | 68%      | 20%           |
|     48 | Kansas            | Big 12           |       116 | $14.2M         | $12.2M to $16.3M | 68%      | 20%           |
|     49 | Louisville        | ACC              |       108 | $14.2M         | $12.3M to $16.4M | 67%      | 22%           |
|     50 | Washington        | Big Ten          |       104 | $14.2M         | $12.0M to $16.5M | 67%      | 24%           |
|     51 | North Carolina    | ACC              |       111 | $14.0M         | $12.0M to $16.0M | 67%      | 21%           |
|     52 | Maryland          | Big Ten          |       110 | $13.6M         | $11.6M to $15.9M | 65%      | 26%           |
|     53 | California        | ACC              |       112 | $13.6M         | $11.8M to $16.2M | 65%      | 23%           |
|     54 | Iowa State        | Big 12           |       126 | $13.6M         | $11.6M to $15.9M | 65%      | 24%           |
|     55 | Illinois          | Big Ten          |       117 | $13.5M         | $11.5M to $15.8M | 64%      | 24%           |
|     56 | TCU               | Big 12           |       114 | $13.5M         | $11.5M to $15.5M | 64%      | 23%           |
|     57 | Boston College    | ACC              |       123 | $13.4M         | $11.3M to $15.6M | 64%      | 22%           |
|     58 | UCF               | Big 12           |       109 | $13.3M         | $11.5M to $15.3M | 63%      | 23%           |
|     59 | Purdue            | Big Ten          |       118 | $13.2M         | $11.3M to $15.4M | 63%      | 21%           |
|     60 | Duke              | ACC              |       105 | $13.1M         | $11.4M to $15.3M | 62%      | 24%           |
|     61 | Cincinnati        | Big 12           |       112 | $13.0M         | $11.0M to $15.4M | 62%      | 26%           |
|     62 | Iowa              | Big Ten          |       111 | $13.0M         | $11.5M to $15.3M | 62%      | 22%           |
|     63 | Wake Forest       | ACC              |       118 | $13.0M         | $11.2M to $15.1M | 62%      | 23%           |
|     64 | Pittsburgh        | ACC              |       113 | $12.9M         | $11.0M to $15.3M | 62%      | 24%           |
|     65 | Arizona           | Big 12           |       109 | $12.7M         | $10.9M to $14.8M | 60%      | 24%           |
|     66 | BYU               | Big 12           |       119 | $12.4M         | $10.5M to $14.4M | 59%      | 24%           |
|     67 | Stanford          | ACC              |       113 | $12.4M         | $10.7M to $14.7M | 59%      | 22%           |
|     68 | Michigan State    | Big Ten          |       110 | $12.2M         | $10.2M to $14.3M | 58%      | 25%           |

## By conference

| conference       |   programs | mean   | low    | high   |
|:-----------------|-----------:|:-------|:-------|:-------|
| ACC              |         17 | $14.8M | $12.4M | $19.7M |
| Big 12           |         16 | $14.2M | $12.4M | $16.8M |
| Big Ten          |         18 | $15.8M | $12.2M | $21.9M |
| FBS Independents |          1 | $21.7M | $21.7M | $21.7M |
| SEC              |         16 | $18.6M | $14.6M | $24.3M |

## Limits

- Ranks come from public features with prior weights, not from contracts.
- Transfers are matched to the portal by name and school; transfers from outside FBS have no production here.
- Linemen on offense and specialists rank on rating and class year alone.
- Rosters include walk-ons; they rank low and mostly add $0, as the CSC's unpaid share says they should.