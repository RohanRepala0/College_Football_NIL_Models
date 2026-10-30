# School layer: research

**Question.** The CSC reports are cohort percentiles. Its own release says "no individual
student-athlete, school or individual deal is identified" (CSC, Oct 30, 2026). What is the best way to
get to school-level pay?

**Short answer.** No single source gives it. The best school layer is assembled from four kinds of
source, from hardest to softest:

1. Official structure: who participates, and in which cohort.
2. Official aggregate constraints: totals and cap counts.
3. Partial school-level ground truth: financial filings and public records.
4. A model: roster × the cohort curves already built here, fitted to those constraints and checked
   against that ground truth.

Third-party estimates are useful only as a validation target. Researched 2026-10-30.

## What the CSC itself publishes at school level

| Source | What it gives | Use |
|---|---|---|
| [Participating schools](https://www.collegesportscommission.org/about/participating-schools/) | 340 entries, each with its conference. 11 are sport-specific affiliates (for example "Colorado College (Men's Hockey)") of 7 institutions, so **336 distinct institutions**. Clean JSON at `/wp-json/wp/v2/participating-school` (taxonomy `participating-schools-conference`). | **The school dimension.** Maps every participant to its conference and so to A4 / Non-A4, which is the cohort key of every CSC table. |
| [First-year revenue-share release](https://www.collegesportscommission.org/college-sports-commission-tracks-1-8-billion-in-payments-to-student-athletes-during-first-year-of-revenue-sharing/) (Oct 1, 2026) | 2025-26: $1,770,453,776 revenue share (plus $42.0M Alston, $163.5M new scholarships) to 34,915 athletes; **319 schools opted in, 307 paid, 68 at the $20.5M cap or within 5% of it**. 2026-27 cap: **$21.58M**. The CSC "will publish aggregate year-end revenue-sharing data from CAPS after each year." | **Constraints** any school-level estimate has to add up to. |
| [NIL Data Reports](https://www.collegesportscommission.org/news/nil-data-reports/) (8 so far, roughly every two months) | Deal counts and dollars cleared through NIL Go. Through Aug 31, 2026: 46,478 deals, $582.49M. | Aggregate NIL constraints, and a time series. Not school-level. |

The participant list (336 institutions) is larger than the 319 opted-in schools of 2025-26. It was
refreshed in September 2026, so it most likely lists 2026-27 participants; that is not confirmed.
Either way, opt-ins and conferences change, so the list should be versioned like the reports.

**What the constraints already say.** If the 68 near-cap schools paid about $20.5M each, that is about
$1.39B. That leaves roughly $0.38B for the other 239 paying schools, about $1.6M each. School
revenue share is close to two-valued: **at the cap** or **a small budget**. The CSC does not say
which 68 schools are near the cap; that they are mostly the A4 is an inference to test. If it holds,
revenue-share totals barely vary among A4 schools. What does vary is football's
share of the cap and the third-party NIL on top of it.

## Partial school-level ground truth

| Source | Coverage | Timing | Limits |
|---|---|---|---|
| **NCAA Membership Financial Reporting System (MFRS)**, compiled in the [Knight-Newhouse College Athletics Database](https://www.knightcommission.org/finances-college-sports/) | Public D-I schools (230+). The NCAA added an expense category for institutional revenue sharing. | FY2025 is out. FY2026, the first full revenue-share year, should follow in 2027. | No required sport or gender split (one Power 4 school gave one for FY2025, per the [Knight Commission](https://www.knightcommission.org/2026/04/response-to-u-s-senate-health-education-labor-and-pensions-help-committee-request-for-information-on-how-to-address-college-sports-issues/)). Private schools are absent. |
| **Equity in Athletics (EADA)**, [ope.ed.gov/athletics](https://ope.ed.gov/athletics/) | Every Title IV school, **by sport**, public and private | 2025-26 reports due around the end of October 2026; the database around March–April 2027 (per a [secondary source](https://www.thedrakegroup.org/wp-content/uploads/2026/08/FINL-APPENDIX-B-08.21.26.pdf); unconfirmed) | Unknown whether revenue-share payments show up in football's expense lines. **Check when the 2025-26 data lands**; if they do, this is the best football-specific school source. |
| **Public-records disclosures** | Whatever reporters obtain. For example, [CalMatters](https://calmatters.org/education/higher-education/2026/08/student-athlete-payments-california/): UCLA $20.5M to 229 athletes, UC Berkeley $20.5M to 147, San Diego State $8.66M with more than 60% to football. | As they happen | Biased toward public schools in open-records states. UCLA and Berkeley refused a sport breakdown, and CalMatters sued. A growing list of states shields NIL or revenue-share records: Utah, Wisconsin (2026) and, by one undated count, Connecticut, Kentucky, Louisiana, Missouri, Nebraska, Ohio and Texas, with bills in North Carolina, South Carolina and Colorado ([CBS Sports](https://www.cbssports.com/college-football/news/colleges-withholding-revenue-sharing-contract-details-how-schools-can-remain-tight-lipped-on-player-payments), [Athletic Business](https://www.athleticbusiness.com/operations/governing-bodies/article/15817177/wisconsin-moves-to-make-athlete-nil-contracts-exempt-from-public-records-law)). |

## Third-party estimates

- **The Athletic, roster budgets (Sept 2026).** Ranges for 68 Power Four teams plus Notre Dame, from
  70+ sources. They count money the football program controls (revenue share plus school-directed
  NIL), not national endorsements. The top is Ohio State at $49–54M and Oregon at $48–54M, and they
  report a strong link between spending and winning
  ([Bleacher Report summary](https://bleacherreport.com/articles/25499892-ohio-state-texas-oregon-top-athletics-cfb-roster-spending-estimates-new-report),
  [Boston Globe](https://www.bostonglobe.com/2026/09/17/sports/boston-college-roster-spending-bill-obrien/)).
  This is the most careful school-level football number available, but it is paywalled, given as
  ranges, and sourced anonymously. Use it to **validate**, not as an input.
- **Aggregators** (Legion Report, sticktothemodel, Opendorse's "Power 4 average $24.8M"). These are
  mostly re-statements of The Athletic, or undocumented. Low weight.
- **Player NIL valuations** (On3 and others). Proprietary; not used here.

## Recommended proxy: roster × cohort curves, constrained

This repository already has, for every football position × A4 / Non-A4 cohort, the full pay
distribution (`benchmark_curves`). A school's football pay is approximately the sum, over its roster,
of each player's pay. The CSC marginals pin the dollar scale, so the model only has to get **who
ranks where** within a cohort.

1. **School dimension.** CSC participants → conference → A4 / Non-A4, joined to CFBD team ids.
2. **Rank within cohort.** For each rostered player (CFBD roster), rank inside his position cohort
   using recruiting rating, transfer-portal rating, usage and snaps, starter status and draft outlook.
3. **Rank → dollars** through the cohort's `all_rostered` curve. The zeros (30% of A4 quarterbacks
   are unpaid) come for free.
4. **Fit to the constraints.** Summing across all A4 rosters must reproduce the CSC cohort
   percentiles. Each school's total has to respect the cap and the near-cap count. Adjust the ranks
   by raking until both hold.
5. **Validate.** Check against public-records totals (UCLA, Cal, SDSU, and more as they appear),
   MFRS revenue-share totals once FY2026 is out, and The Athletic's ranges. Report coverage of those
   ranges, not a single error number.

What this proxy cannot see: third-party NIL beyond the cap, which is where The Athletic's $8M vs
$50M spread comes from. NIL Go percentiles give that distribution by cohort but not by school, so the
NIL side of a school estimate stays wide until a school-level NIL source exists.

## Next steps

| Step | Needs | Notes |
|---|---|---|
| Capture the participant list in the daily pipeline (`csc_schools`), versioned like the reports | nothing | REST JSON, 4 pages of 100 |
| Capture the CSC year-end CAPS release and the NIL Data Reports as constraint tables | nothing | WordPress posts, `nil-data-report` type |
| Map participants to CFBD teams | CFBD key (or the team list in CollegeFootballRatings2026) | 336 names; disambiguators such as "(Ohio)" |
| Curate public disclosures into `data/reference/school_disclosures.csv`, one row per figure with its source URL | manual | ground truth, small and growing |
| Pull Knight-Newhouse FY2025 now and FY2026 when out; check EADA 2025-26 football lines in spring 2027 | check each site's terms | the school totals to validate against |
| Roster × curves model (steps 2–5 above) | CFBD key | the school layer itself |
