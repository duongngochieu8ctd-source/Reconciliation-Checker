# Payment Reconciliation Checker

**A learning project, not production software. All data is made up.**

## Purpose
Compares payment gateway records with CRM invoices and flags the items a subscription support officer would need to review: duplicate payments, amount mismatches, status conflicts, missing records, late catch-up payments and pending items. It also checks CRM accounts for missing details and similar accounts. It prints a short report and saves `findings.csv`.

## How I built it
- **I wrote:** the user stories and acceptance criteria, the field list, the business rules and parameters, the test cases and the process map. I triaged the defects and decided how each was resolved.
- **Claude (an AI assistant) wrote:** the Python script and the sample data, to my specification, and helped refine my stories, test cases and documents. I directed the build and ran the tests.
- **Gemini (a second AI tool) was used as an independent reviewer** of the code and stories. It raised the issues in the defect log, which I then worked through with Claude.

## Files
| File | What it is |
|---|---|
| `reconcile.py` | The checker (one small function per check) |
| `data/gateway.csv` | Payment attempts, one row per attempt |
| `data/crm_invoices.csv` | Successful payments recorded in the CRM |
| `data/crm_accounts.csv` | Customer accounts |
| `docs/user_stories.md` | User stories, rules, parameters and data fields |
| `docs/test_cases.md` | 12 test cases with results |
| `docs/defect_log.md` | Issues found and how each was resolved |
| `docs/process_map.png` | BPMN overview of the checker's flow |

## How to run (Google Colab)
1. Open a new notebook at colab.research.google.com.
2. Upload `reconcile.py` and the three CSV files into the same folder (left sidebar, folder icon).
3. Run `!python reconcile.py`.

The report prints in the notebook and `findings.csv` is saved beside it. Don't re-save the CSVs in Excel first, as that can remove the blank cells the tests depend on. Needs Python 3 and pandas (both are in Colab).

## Process overview
![Process map](docs/process_map.png)

The officer runs the checker, which reads the files, then runs the account checks and the transaction checks in parallel. The transaction checks run in a fixed order, and each check takes out the transactions it flags, so every transaction ends up in one category only.

**Order:** Catch-up, then Duplicate, then Mismatch / Status Conflict, then Unmatched items (Missing or Pending). Catch-up runs before Duplicate so a late payment isn't mislabelled as a double charge.

## Parameters (top of `reconcile.py`)
| Parameter | Value |
|---|---|
| Duplicate window | 14 days (inclusive) |
| Grace / catch-up window | 25 days (25 or fewer = Pending, more than 25 = Missing) |
| Retry gap | Within 5 days (inclusive) of the last Rejected attempt |
| Refund limit | $300.00 or less = Actionable, above = Escalation |
| Amount tolerance | None |
| Report date | 2026-11-18 (fixed for testing) |

## Assumptions
- The gateway is the source of truth for payment attempts. The CRM records successful payments only.
- Authorized (gateway) and Complete (CRM) both mean the payment succeeded; Rejected means it failed.
- One email links to one CRM account.
- Status Conflict means statuses or timing contradict the expected process and need investigation.
- Gateway-only items count their 25 days from the gateway payment date, because they have no CRM due date.

## Testing
12 test cases (TC01 to TC11b) cover Stories 1 to 6, one scenario each, and all matched the expected results on the sample data. Sample run: 1 catch-up, 3 duplicate pairs, 2 mismatches, 1 status conflict, 2 missing, 1 pending.

A second AI tool (Gemini) then cross-checked the code against my stories and raised 11 issues that my first pass had not found (see `docs/defect_log.md`): 6 fixed, 5 accepted as limits. A break-it test confirmed one of them.

## Limits (what this does not do)
- **Not covered:** payments made after the fifth failed retry (Story 6, second scenario).
- Two different subscriptions at the same price on one card are flagged as duplicates.
- A catch-up needs a matching CRM invoice to find its due date, and catch-ups skip the mismatch check (DEF-01).
- Three payments within 14 days give two duplicate findings, with the middle payment listed twice (DEF-05).
- A Status Conflict shows the attempted amount even though no money was taken (DEF-04b).
- The summary's Mismatch total nets overcharges against undercharges (DEF-06b).
- Account results (missing details, similar accounts) print in the notebook but are not saved to `findings.csv` (DEF-06a).
- Built for small, made-up files with one fixed report date. Not tested on real data or large volumes.
