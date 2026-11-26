# Defect Log

All entries came from a cross-check of the code against my user stories by a second AI tool (Gemini), after the build with Claude and my own review had found nothing. I worked through each one with Claude and decided the resolution. Dated 2026-11-22. All 12 test cases passed on the first run, so none of these are failed tests. DEF-05 was confirmed with a break-it test.

**Cause key:** Story = my requirement was unclear; Code = the script; AI output = the AI's build differs from what I asked; Design = a decision the stories did not cover.

| ID | Severity | Story / area | Issue | Expected vs actual | Cause | Resolution | Status |
|---|---|---|---|---|---|---|---|
| DEF-01 | Low | 6, `find_catch_ups` | Due date is found by matching the gateway transaction ID to the CRM payment ID, not through the subscription ID as Story 6 says | Expected: link through subscription ID. Actual: a catch-up with no CRM invoice for its payment ID is skipped. Works on the sample data because the CRM records every successful payment | AI output / Story | Kept. Listed as a limit in the README | Accepted limit |
| DEF-02 | Low | 6, `RETRY_GAP_DAYS` | Story said "a 5-day gap", the code accepts a gap of 5 days or fewer | Expected: rule stated clearly. Actual: the code was right but the wording was ambiguous | Story | Story 6 now says "within 5 days (inclusive) of the last Rejected attempt". Code comment updated. Results unchanged | Fixed |
| DEF-03a | Low | 5, `GRACE_DAYS` | Exactly 25 days was not defined | Expected: a clear boundary. Actual: code treats 25 as Pending | Story | Story 5 now says "25 days or fewer = Pending, more than 25 = Missing". Code comment updated | Fixed |
| DEF-03b | Low | 5, `find_missing_and_pending` | CRM-only check did not filter by status Complete | Expected: only Complete invoices count as missing. Actual: all invoices checked (all are Complete in the data) | Code | Added a Complete filter. Results unchanged | Fixed |
| DEF-03c | Low | 5 | Gateway-only items have no due date, so age counts from the payment date | Expected: documented rule. Actual: rule existed only in the code | Story | Added to the business rules and README assumptions | Fixed |
| DEF-04a | Medium | 4, `find_mismatches_and_conflicts` | Status Conflict checked only that the gateway was Rejected, not that the CRM was Complete | Expected: both conditions, as Story 4 says. Actual: gateway side only | AI output | Added the CRM Complete check. Results unchanged | Fixed |
| DEF-04b | Medium | 4, 7 | A Status Conflict shows the attempted amount ($49.00), but no money was taken on a Rejected payment | Expected: a decision on what the amount means. Actual: the summary total includes $49.00 for the conflict | Design | Kept the attempted amount, since it identifies the payment under investigation. Not counted as money moved | Accepted limit |
| DEF-05 | Medium | 2, `find_duplicates` | Three payments within 14 days give two duplicate findings with the middle one listed twice | Tested: added TX-1003 (2026-10-21) to C1001. Result: TX-1001/TX-1002 and TX-1002/TX-1003, refund total $98.00 (two refunds, which is correct for three charges), but C1001 shows 2 duplicate items for 3 transactions | Design | Kept. Pairs are counted, not transactions. Dates and IDs are in one text column, not separate columns | Accepted limit |
| DEF-06a | Low | 1, 3, 7 | Account results (missing details, similar accounts) print in the notebook but are not saved to `findings.csv` | Expected: results available after the run. Actual: only on screen | Story / Design | Listed as a limit in the README | Accepted limit |
| DEF-06b | Low | 7, `build_summary` | Mismatch total nets overcharges against undercharges (+6.00 and -4.00 = 2.00), and Duplicate counts one item per pair | Expected: totals meaningful to finance. Actual: net figure only | Story | Story 7 does not say how to total. Listed as a limit in the README | Accepted limit |
| DEF-07 | Low | Stories document | Inclusive or exclusive limits were not stated, and there were typos | Expected: every day window and the $300 limit stated as inclusive or exclusive. Actual: loose wording ("within 14 days") | Story | Rewrote the stories with limits stated (see `user_stories.md`). Typos fixed | Fixed |

## What the log shows
- 6 entries fixed, 5 accepted as documented limits. None are open.
- The code changes were guards and comments only, and the output was identical to the previous run.
- A second AI reviewer caught issues the first one missed. I reviewed each before it was fixed or accepted as a limit.
