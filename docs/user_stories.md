# User Stories and Rules

Project: Payment Reconciliation Checker (learning project, made-up data only).
Role for all stories: **subscription support officer**.

## Parameters
| Parameter | Value |
|---|---|
| Duplicate window | 14 days (inclusive: 14 days apart or fewer) |
| Grace / catch-up window | 25 days (catch-up: 1 to 25 days late; unmatched: 25 days or fewer = Pending, more than 25 = Missing) |
| Retry gap | 5 days (inclusive) between the last Rejected attempt and the Authorized payment |
| Refund limit | $300.00 or less = Actionable; above $300.00 = Escalation |
| Amount tolerance | None (any difference counts) |
| Report date | 2026-11-18 (fixed for testing) |

## Statuses
| Status | File | Meaning |
|---|---|---|
| Authorized | Gateway | Transaction processed successfully |
| Rejected | Gateway | Transaction failed to process |
| Complete | CRM | Transaction processed successfully |

## Business rules and assumptions
- The gateway is the source of truth for payment attempts. The CRM records successful payments only.
- One email links to one CRM account.
- The grace period is 25 days: 5 re-payment attempts, one every 5 days after each failed payment. When the retry limit passes and the payment still fails, the subscription is cancelled automatically.
- **Status Conflict** means a record whose statuses or timing contradict the expected process and need investigation.
- Gateway-only items count their 25 days from the gateway payment date, because they have no CRM due date.
- Known limit: two different subscriptions at the same price on one card are flagged as duplicates.
- Duplicate = two Authorized payments. Catch-up = a Rejected attempt followed by an Authorized payment.

## Order of checks
Account-level (CRM accounts file only): Story 1, then Story 3.
Transaction-level, each transaction ends in one category only:
1. Catch-up (Story 6)
2. Duplicate (Story 2)
3. Mismatch and Status Conflict (Story 4)
4. Missing and Pending (Story 5)

## Data fields
**Gateway file** (one row per payment attempt)
| Field | Contains | Example |
|---|---|---|
| transaction_id (link key) | Unique attempt number | TX-100234 |
| customer_id | Customer number | C1001 |
| subscription_id | Subscription the attempt belongs to | SU-5001 |
| payment_token | Card or PayPal reference | TOK-0042 |
| amount | Amount charged | 49.00 |
| status | Authorized or Rejected | Authorized |
| payment_date | Date processed | 2026-11-12 |
| attempt_number | Attempt count | 2 |

**CRM accounts** (one row per customer): customer_id, user_name, email, payment_token.

**CRM invoices** (one row per successful payment): external_payment_id (link key, matches gateway transaction_id), customer_id, subscription_id, amount, status (always Complete), due_date.

## Stories

### Story 1: Missing account details
As a subscription support officer, I want accounts in the CRM with missing details flagged in the report so that I can follow up and complete the record.
- **Given** a CRM account where name, email or payment token is blank (a cell containing only spaces counts as blank)
- **When** the checker runs
- **Then** the report lists the customer ID and the name of each missing field.

### Story 2: Duplicate payments
As a subscription support officer, I want duplicated payments in the gateway flagged so that a refund can be reviewed.
- **Given** two Authorized payments with the same customer ID, payment token and amount
- **And** payment dates within 14 days of each other
- **When** the checker runs
- **Then** the report lists both transaction IDs and dates, and the refund amount is the later transaction's amount.

### Story 3: Similar accounts
As a subscription support officer, I want different CRM accounts with similar details flagged so that potential duplication can be reviewed.
- **Given** accounts with the same name and payment token (values trimmed and compared ignoring capitals) but different emails
- **When** the checker runs
- **Then** the accounts are listed as potential duplicates, showing both accounts and which fields matched.

### Story 4: Mismatches and status conflicts
As a subscription support officer, I want mismatches between the payment gateway and the CRM flagged so that transactions can be reviewed.

*Scenario A: amount mismatch*
- **Given** a CRM invoice (Complete) and a gateway transaction (Authorized) with the same payment ID but different amounts
- **When** the checker runs
- **Then** the item is flagged as Mismatch, with the difference (gateway minus CRM) shown. No tolerance applies.

*Scenario B: status conflict*
- **Given** a CRM invoice with status Complete and a gateway transaction with the same payment ID and status Rejected
- **When** the checker runs
- **Then** the item is flagged as Status Conflict for investigation.

### Story 5: Missing and pending records
As a subscription support officer, I want transaction records missing from either the CRM or the gateway flagged so that reconciliation is more effective.
- **Given** a payment ID that exists in the CRM only (status Complete) or in the gateway only (status Authorized), with no match on the other side
- **When** the checker runs
- **Then** if the item is more than 25 days old at the report date, it is listed as Missing with the amount and the label "CRM only" or "Gateway only"; if it is 25 days or fewer old, it is listed as Pending.
- Age counts from the CRM due date (CRM only) or the gateway payment date (gateway only). A Rejected gateway payment is not a missing record.

### Story 6: Catch-up payments
As a subscription support officer, I want catch-up payments in the gateway flagged so that they are not mixed up with duplicate payments.
- **Given** an Authorized payment dated 1 to 25 days after its invoice due date
- **And** an earlier Rejected attempt with the same customer ID, payment token and subscription ID, within 5 days before the Authorized payment
- **When** the checker runs
- **Then** the Authorized payment is listed as Catch-up. The Rejected attempts are not flagged separately, and the payment is excluded from the duplicate check (catch-up runs first).
- **Not covered in this version:** payments processed after the fifth failure (would be a Status Conflict).

### Story 7: Summary report
As a subscription support officer, I want a summary report of all transactions so that I can assess counts and totals per category, gateway versus CRM totals, and the unreconciled difference.
- **Given** the checks have run
- **When** the report is produced
- **Then** it shows the count and total per category (Catch-up, Duplicate, Mismatch, Status Conflict, Missing, Pending), the total gateway amount (Authorized only), the total CRM amount, and the unreconciled difference (gateway minus CRM).
- Refund status applies to Duplicate (refund amount = later transaction's amount) and to Mismatch where gateway > CRM (refund amount = the difference). A refund amount of $300.00 or less is Actionable; above that is Escalation.
- Catch-up, Missing, Pending, Status Conflict, and Mismatch where gateway < CRM show N/A.
- Each transaction is listed under one category only. Stories 1 and 3 are account-level and appear in their own section.
