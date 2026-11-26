# Test Cases

Report date for all tests: **2026-11-18**. Data: `data/` folder (made-up).
Result column: outcome of the run on the sample data.

| ID | Story | Scenario | Input (data rows) | Expected result | Result |
|---|---|---|---|---|---|
| TC01 | 1 | Missing details | Account A (C1012) blank name; account B (C1013) email of only spaces; account C (C1014) blank token | Three accounts listed with customer_id and the missing field: name for A, email for B, payment token for C | Pass |
| TC02 | 3 | Similar accounts | C1015 "Priya Shah" and C1016 "PRIYA SHAH " (capitals, trailing space), same token, different emails | Both accounts listed with customer_id and email. Matched fields shown as name and payment token. They match only because values are trimmed and compared ignoring capitals | Pass |
| TC03 | 2 | Duplicate | C1001, TOK-0042, $49.00, Authorized, TX-1001 (2026-10-01) and TX-1002 (2026-10-11) | Both transaction IDs and dates listed under Duplicate. Refund amount $49.00 (later payment). Refund status Actionable | Pass |
| TC04 | 2 | Not a duplicate | C1002, same token and amount, TX-2001 (2026-09-01) and TX-2002 (2026-10-01), 30 days apart | Not listed under Duplicate. Both payments match their CRM invoices. Nothing flagged | Pass |
| TC05 | 4 | Mismatch, overcharged | TX-3001: gateway $55.00, CRM $49.00 | Difference +$6.00 (gateway minus CRM). Category Mismatch. Refund amount $6.00. Refund status Actionable | Pass |
| TC06 | 4 | Mismatch, undercharged | TX-4001: gateway $45.00, CRM $49.00 | Difference -$4.00. Category Mismatch. Customer undercharged. Refund status N/A | Pass |
| TC07 | 4 | Status conflict | TX-5001: Complete in CRM, Rejected in gateway | Listed as Status Conflict with transaction_id and customer_id. Not listed as Mismatch or Missing. Refund status N/A | Pass |
| TC08 | 6 | Catch-up | C1006: TX-6001 Rejected 2026-10-05; TX-6002 Authorized 2026-10-10; invoice due 2026-10-01 | TX-6002 listed as Catch-up with transaction_id, customer_id, subscription_id and due date. Not listed under Duplicate (catch-up runs first). The Rejected attempt is not flagged separately. Refund status N/A | Pass |
| TC09 | 5 | Missing, both directions | CRM only: TX-7001 due 2026-10-10. Gateway only: TX-7002 paid 2026-10-12. Both more than 25 days before the report date | CRM only: external_payment_id, customer_id, amount, due date. Gateway only: transaction_id, customer_id, amount, payment date. Both Missing. Refund N/A | Pass |
| TC10 | 5 | Pending | CRM only: TX-8001 due 2026-11-08 (10 days before report date) | Listed as Pending with external_payment_id, customer_id and due date. Not Missing. Refund N/A | Pass |
| TC11a | 2, 7 | Refund boundary, Actionable | C1010: TX-9001 and TX-9002, $300.00, 5 days apart | Listed under Duplicate. Refund amount $300.00. Refund status Actionable | Pass |
| TC11b | 2, 7 | Refund boundary, Escalation | C1011: TX-9101 and TX-9102, $300.01, 5 days apart | Listed under Duplicate. Refund amount $300.01. Refund status Escalation | Pass |

## Additional checks
- **Summary totals (Story 7):** sample run shows gateway total 1594.02, CRM total 1041.01, unreconciled difference +553.01.
- **Break-it test (DEF-05):** a third C1001 payment (TX-1003, 2026-10-21) was added to a copy of the data. Result: two Duplicate findings (TX-1001/TX-1002 and TX-1002/TX-1003), refund total $98.00. See DEF-05.

## Not tested
Payment after the fifth failed retry (Story 6, second scenario) is not built in this version.
