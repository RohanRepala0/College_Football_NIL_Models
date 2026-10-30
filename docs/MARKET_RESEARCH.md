# Market research: NIL intelligence tools

Who already sells intelligence on college-athlete pay, what they leave open, and which tool this
repository's data could become. Researched 2026-10-30.

## Dropback

[Dropback](https://www.dropback.com/) calls itself "the front office software suite for college
sports". It is Y Combinator-backed: founders Luke Bogus and Nick Siscoe raised $1.6M from YC, Reach
Capital and Twenty Two Ventures. It started as FanCave, a fan-donation app, and pivoted
([YC](https://www.ycombinator.com/companies/dropback), [Dealroom](https://app.dealroom.co/companies/dropback_1)).

**Product (2026).** An "AI Teammate" over a program's own data, reachable by chat or iMessage, plus:

- custom statistical player models (a "QB Value Model" that outputs a dollar range per athlete);
- automated market monitoring and boards;
- cap management: roster slots and limits, contract construction, budget pools, multi-year planning,
  scholarships, rules and alerts, and reports;
- contract tracking and roster simulation.

Integrations include Hudl, PFF and Synergy. It covers football, men's and women's basketball,
baseball, softball and volleyball ([dropback.com](https://www.dropback.com/),
[cap management](https://www.dropback.com/workspace/cap-management)).

**Customers.** Georgia, Kentucky, Tennessee Tech and Butler, and "30+ teams" across the ACC, Big Ten,
Big East and SEC. Kentucky runs it as "BLUEprint" for football, both basketballs and volleyball
([Kentucky](https://www.dropback.com/blog/kentucky-dropback-2026)). Its first partner was Northwestern's
TrueNU collective.

**The PFF partnership** (Nov 2024) brings PFF data into Dropback's Valuation Modeler, where "programs
build custom athlete valuation formulas from their own data, metrics, baselines, and weights"
([PFF](https://www.pff.com/news/pff-and-dropback-partnership-powers-winning-decisions-in-college-sports-revenue-sharing-era)).

**What it does not show.**
- **Where the dollars come from.** Its cap-management page shows a sample $1,315,000 contract (revenue
  share, incentives, NIL, scholarship) but names no market rates, comparables or benchmark.
- **The regulator.** It does not mention CSC, CAPS or NIL Go.
- **Pooled data.** Client data is "never shared or sold", so Dropback cannot pool its clients'
  contracts into a market rate. Each program supplies its own dollar anchor.

## The rest of the market

| Player | What it is | Relevance |
|---|---|---|
| **Teamworks GM** | Revenue-share and roster platform with financial modeling against the cap. South Carolina is its 5th SEC school; UTSA plus 7 other AAC schools use it ([UTSA](https://goutsa.com/news/2025/06/24/utsa-selects-teamworks-gm-for-strategic-revenue-sharing-management)). Teamworks is valued around $1.5B and bought **Zelus Analytics** (March 2026) for ML valuations that combine models "with contract and intel information" ([Training Ground](https://archive.trainingground.guru/articles/teamworks-acquires-zelus-analytics)). | The incumbent, with distribution. It is building proprietary valuations. |
| **On3 NIL Valuation** | Consumer-facing player index. It moved from a formula to a **deal-based** model on July 1, 2026 ([On3](https://www.on3.com/nil/news/about-on3-nil-valuation-per-post-value/)). | The public's reference number, but proprietary and per player. |
| **Opendorse** | NIL marketplace and market reports: $4.5B NIL market estimate for 2026-27, Power 4 QBs averaging $1.5M ([FootballScoop](https://footballscoop.com/2026/06/25/opendorse-tabs-nil-market-more-than-4-billion-50-percent-increase)). | Its data covers only its own platform's deals. |
| **Second Wind Pro "Scout Edge"** | An agency's "price index for college football player value" with position bands and market comps (from its own LinkedIn; not independently verified). | The closest idea to a market-rate product, but agency-built. |
| **Cache AI, INFLCR** | Athlete valuation from deal analytics and social reach ([Hypepotamus](https://www.hypepotamus.com/fixing-nil-deals-data-driven-cache-ai/)). | Brand-deal side. |
| **NIL Go (the regulator)** | Deloitte-run clearinghouse. Its range-of-compensation review moved to **prediction intervals** in July 2026, weighing performance obligations, athletic performance, social reach, the local market and the school's reach ([NIL Revolution](https://www.nilrevolution.com/2026/06/college-sports-commission-updates-its-range-of-compensation-analysis/)). Through July 1, 2026: 34,195 deals cleared for $355.24M, 1,812 not cleared for $89.85M ([Business of College Sports](https://businessofcollegesports.com/governance-2/college-sports-commission-releases-july-2026-report-on-nil-deals/)). | A refused deal averages about **$49.6k**, against about **$10.4k** for a cleared one. Big deals carry the clearance risk, and the review thresholds have moved several times in 2026 ([Athletic Business](https://www.athleticbusiness.com/operations/governing-bodies/article/15821795/csc-increases-minimum-nil-deal-value-necessary-for-review-from-600-to-2500)). |

## The gaps this data fits

1. **No one sells an official, population-wide market rate.**
   - Front-office tools leave the dollar anchor to each client.
   - Indexes are proprietary estimates, and the agency index has a conflict of interest.
   - The CSC percentiles are the only numbers that cover every athlete in a cohort, and they are
     official. This repository already turns them into a validated curve per cohort.
2. **No visible clearance pre-check.** Whether a large NIL deal will clear NIL Go is the expensive
   question, and nobody offers a pre-screen.
3. **No history.** This repository is the only archive of CSC releases.
4. **No league-wide map of dollars against results.** Dropback has every team build its own model.
   CollegeFootballRatings2026 already prices team strength in points, which is half of that map.

## Tool concepts

| | Concept | For | Built already | Still needed |
|---|---|---|---|---|
| **A** | **Market Rate API.** CSC-anchored percentiles, curves, revisions and offer lookups as a data feed. This is the PFF-to-Dropback model, with pay data in place of grades. | Front-office platforms (Dropback, Teamworks GM) as integration partners; agents; media | Capture, archive, curves, lookups (N1, N2) | An API surface and docs; the school layer |
| **B** | **Offer and clearance check.** Enter the components of an offer and get its market percentile in each report, plus NIL Go risk flags: review thresholds, and a tail position in the cohort. | Agents, collectives, brands, athletes and families | The percentile engine | A thresholds rules table from the CSC memos, and NIL Data Report capture. Every answer must carry its limit: this is a pre-screen, not a forecast of the CSC's decision, which also weighs social reach and the deal's obligations. |
| **C** | **Roster efficiency board.** Each team's estimated pay against its strength from the rating model: rating points per $M, and spending by position against the market. | General managers, media, bettors | The rating model; the curves | The school layer (`SCHOOL_LAYER.md`) and a CFBD key |
| **D** | **Market monitor.** Alerts on CSC releases and revisions, NIL Data Reports and threshold memos. | All of the above | The daily capture | Notifications |

**Recommendation.** Ship **A and B together as one product: market rates plus a clearance
pre-check**, because the data for both exists today. Position it as a **complement to Dropback and
Teamworks GM**, the market layer their valuation tools lack, not a competitor on front-office
workflow, where they already have distribution and client data. **C** is the flagship analysis
once the school layer exists. It is the piece nobody else can build, because it joins pay to the
spread model.

**Risks.**
- The CSC may update rarely.
- The cohorts are coarse (no star tier), which limits answers at the top end where the money is.
- Teamworks and Zelus have real contract data.
- On3's new deal-based index may become the public's reference number.

## Open questions for the owner

1. Who is the first customer: programs (through a platform partner), agents, or media?
2. Approach Dropback, or Teamworks, as a data partner?
3. CFBD key, for the school and player layers.
