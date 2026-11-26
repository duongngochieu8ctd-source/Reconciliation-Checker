"""
Payment reconciliation checker  (learning project, made-up data only)

Compares gateway payments with CRM invoices and flags:
catch-up payments, duplicates, mismatches, status conflicts,
missing records and pending items. Also checks CRM accounts for
missing details and similar accounts.

Order of transaction checks (each transaction ends in ONE category):
catch-up -> duplicate -> mismatch / status conflict -> missing / pending
"""

from itertools import combinations
import pandas as pd

# ---------------------------------------------------------------
# PARAMETERS - change numbers here, nowhere else
# ---------------------------------------------------------------
DATA_FOLDER = "."                      # folder holding the three CSV files
REPORT_DATE = pd.Timestamp("2026-11-18")
DUPLICATE_WINDOW_DAYS = 14             # identical payments 14 days apart or fewer (inclusive) = duplicate
GRACE_DAYS = 25                        # catch-up: 1 to 25 days late. Unmatched: 25 days or fewer = Pending, more than 25 = Missing
RETRY_GAP_DAYS = 5                     # catch-up must come within 5 days (inclusive) of the last Rejected attempt
REFUND_LIMIT = 300.00                  # $300.00 or less = Actionable, above = Escalation

CATEGORIES = ["Catch-up", "Duplicate", "Mismatch",
              "Status Conflict", "Missing", "Pending"]


# ---------------------------------------------------------------
# 1. LOADING AND TIDYING
# ---------------------------------------------------------------
def load_data(folder):
    """Read the three CSV files. Everything is read as text first so that
    blank cells stay blank and cells containing only spaces are kept."""
    def read(name):
        return pd.read_csv(f"{folder}/{name}", dtype=str, keep_default_na=False)

    gateway = read("gateway.csv")
    invoices = read("crm_invoices.csv")
    accounts = read("crm_accounts.csv")

    gateway["amount"] = gateway["amount"].astype(float)
    gateway["payment_date"] = pd.to_datetime(gateway["payment_date"])
    invoices["amount"] = invoices["amount"].astype(float)
    invoices["due_date"] = pd.to_datetime(invoices["due_date"])
    return gateway, invoices, accounts


def clean(text):
    """Trim spaces and ignore capital letters, so ' PRIYA SHAH ' == 'priya shah'."""
    return text.strip().lower()


def refund_status(refund_amount):
    """N/A if no refund applies, otherwise Actionable (<= limit) or Escalation."""
    if refund_amount is None:
        return "N/A"
    return "Actionable" if refund_amount <= REFUND_LIMIT else "Escalation"


def make_finding(category, ids, customer_id, amount, label="", refund=None, note=""):
    """Build one report row. 'amount' is the money involved in the finding."""
    return {
        "category": category,
        "label": label,
        "transaction_ids": ids,
        "customer_id": customer_id,
        "amount": round(amount, 2),
        "refund_status": refund_status(refund),
        "note": note,
    }


# ---------------------------------------------------------------
# 2. ACCOUNT-LEVEL CHECKS (CRM accounts file only)
# ---------------------------------------------------------------
def check_missing_details(accounts):
    """Story 1: list accounts with a blank name, email or payment token."""
    fields = ["user_name", "email", "payment_token"]
    rows = []
    for acc in accounts.to_dict("records"):
        missing = [f for f in fields if clean(acc[f]) == ""]
        if missing:
            rows.append({"customer_id": acc["customer_id"],
                         "missing_fields": ", ".join(missing)})
    return rows


def check_similar_accounts(accounts):
    """Story 3: same name and token but different emails = possible duplicate account."""
    rows = []
    for a, b in combinations(accounts.to_dict("records"), 2):
        same_name = clean(a["user_name"]) == clean(b["user_name"]) != ""
        same_token = clean(a["payment_token"]) == clean(b["payment_token"]) != ""
        different_email = clean(a["email"]) != clean(b["email"])
        if same_name and same_token and different_email:
            rows.append({
                "customer_ids": f'{a["customer_id"]} / {b["customer_id"]}',
                "emails": f'{a["email"]} / {b["email"]}',
                "matched_fields": "name, payment_token",
            })
    return rows


# ---------------------------------------------------------------
# 3. TRANSACTION-LEVEL CHECKS (run in this order)
# ---------------------------------------------------------------
def find_catch_ups(gateway, invoices):
    """Story 6: an Authorized payment made 1-25 days after its due date, preceded
    by a Rejected attempt on the same subscription within 5 days."""
    due_dates = dict(zip(invoices["external_payment_id"], invoices["due_date"]))
    rejected = gateway[gateway["status"] == "Rejected"]
    findings, claimed = [], set()

    for pay in gateway[gateway["status"] == "Authorized"].itertuples():
        if pay.transaction_id not in due_dates:
            continue                                   # no due date, cannot judge
        days_late = (pay.payment_date - due_dates[pay.transaction_id]).days
        if not 1 <= days_late <= GRACE_DAYS:
            continue

        earlier = rejected[(rejected["subscription_id"] == pay.subscription_id)
                           & (rejected["customer_id"] == pay.customer_id)
                           & (rejected["payment_token"] == pay.payment_token)
                           & (rejected["payment_date"] < pay.payment_date)]
        if earlier.empty:
            continue
        last_rejected = earlier.sort_values("payment_date").iloc[-1]
        gap = (pay.payment_date - last_rejected["payment_date"]).days
        if gap <= RETRY_GAP_DAYS:
            findings.append(make_finding(
                "Catch-up", pay.transaction_id, pay.customer_id, pay.amount,
                note=(f"subscription {pay.subscription_id}, due "
                      f"{due_dates[pay.transaction_id].date()}, paid {pay.payment_date.date()}")))
            claimed.add(pay.transaction_id)
            claimed.update(earlier["transaction_id"])   # the Rejected attempts belong to it
    return findings, claimed


def find_duplicates(gateway, claimed):
    """Story 2: two Authorized payments, same customer + token + amount,
    within 14 days. Refund = the later payment's amount."""
    pool = gateway[(gateway["status"] == "Authorized")
                   & (~gateway["transaction_id"].isin(claimed))]
    findings, flagged = [], set()

    for _, group in pool.groupby(["customer_id", "payment_token", "amount"]):
        rows = list(group.sort_values("payment_date").itertuples())
        for first, second in zip(rows, rows[1:]):
            if (second.payment_date - first.payment_date).days <= DUPLICATE_WINDOW_DAYS:
                findings.append(make_finding(
                    "Duplicate", f"{first.transaction_id} / {second.transaction_id}",
                    first.customer_id, second.amount, refund=second.amount,
                    note=f"{first.payment_date.date()} and {second.payment_date.date()}"))
                flagged.update([first.transaction_id, second.transaction_id])
    return findings, flagged


def find_mismatches_and_conflicts(gateway, invoices, claimed):
    """Story 4: match on payment ID. Authorized + different amount = Mismatch.
    Rejected in gateway but Complete in CRM = Status Conflict."""
    merged = gateway.merge(invoices, left_on="transaction_id",
                           right_on="external_payment_id", suffixes=("_gw", "_crm"))
    merged = merged[~merged["transaction_id"].isin(claimed)]
    findings = []

    for row in merged.itertuples():
        if row.status_gw == "Rejected" and row.status_crm == "Complete":
            findings.append(make_finding(
                "Status Conflict", row.transaction_id, row.customer_id_gw, row.amount_gw,
                note="Rejected in gateway, Complete in CRM"))
        elif row.status_gw == "Authorized":
            difference = round(row.amount_gw - row.amount_crm, 2)   # gateway minus CRM
            if difference != 0:
                refund = difference if difference > 0 else None
                label = "overcharged" if difference > 0 else "undercharged"
                findings.append(make_finding(
                    "Mismatch", row.transaction_id, row.customer_id_gw, difference,
                    label=label, refund=refund,
                    note=f"gateway {row.amount_gw:.2f}, CRM {row.amount_crm:.2f}, "
                         f"difference {difference:+.2f}"))
    return findings


def find_missing_and_pending(gateway, invoices, claimed):
    """Story 5: records that exist on one side only. More than 25 days old = Missing,
    otherwise Pending. CRM-only age counts from due date; gateway-only from payment date."""
    gateway_ids = set(gateway["transaction_id"])
    crm_ids = set(invoices["external_payment_id"])
    findings = []

    for inv in invoices[invoices["status"] == "Complete"].itertuples():
        if inv.external_payment_id in gateway_ids or inv.external_payment_id in claimed:
            continue
        age = (REPORT_DATE - inv.due_date).days
        category = "Missing" if age > GRACE_DAYS else "Pending"
        findings.append(make_finding(
            category, inv.external_payment_id, inv.customer_id, inv.amount,
            label="CRM only", note=f"due {inv.due_date.date()}, {age} days ago"))

    for pay in gateway[gateway["status"] == "Authorized"].itertuples():
        if pay.transaction_id in crm_ids or pay.transaction_id in claimed:
            continue
        age = (REPORT_DATE - pay.payment_date).days
        category = "Missing" if age > GRACE_DAYS else "Pending"
        findings.append(make_finding(
            category, pay.transaction_id, pay.customer_id, pay.amount,
            label="Gateway only", note=f"paid {pay.payment_date.date()}, {age} days ago"))
    return findings


# ---------------------------------------------------------------
# 4. SUMMARY AND REPORT (Story 7)
# ---------------------------------------------------------------
def build_summary(findings, gateway, invoices):
    """Count and total per category, plus gateway vs CRM totals.
    Gateway total counts Authorized payments only (Rejected = no money taken)."""
    df = pd.DataFrame(findings, columns=["category", "amount", "refund_status"])
    by_category = []
    for cat in CATEGORIES:
        part = df[df["category"] == cat]
        by_category.append((cat, len(part), round(part["amount"].sum(), 2)))

    gateway_total = round(gateway.loc[gateway["status"] == "Authorized", "amount"].sum(), 2)
    crm_total = round(invoices["amount"].sum(), 2)
    return {
        "by_category": by_category,
        "gateway_total": gateway_total,
        "crm_total": crm_total,
        "difference": round(gateway_total - crm_total, 2),
        "actionable": int((df["refund_status"] == "Actionable").sum()),
        "escalation": int((df["refund_status"] == "Escalation").sum()),
    }


def print_report(missing_details, similar, findings, summary):
    """Print a short, readable report."""
    print(f"PAYMENT RECONCILIATION REPORT  (report date {REPORT_DATE.date()})")

    print("\n== ACCOUNT CHECKS ==")
    print("Missing details:")
    for r in missing_details:
        print(f"  {r['customer_id']}: missing {r['missing_fields']}")
    print("Similar accounts (possible duplicates):")
    for r in similar:
        print(f"  {r['customer_ids']} | {r['emails']} | matched: {r['matched_fields']}")

    print("\n== TRANSACTION FINDINGS ==")
    for cat in CATEGORIES:
        rows = [f for f in findings if f["category"] == cat]
        print(f"\n{cat} ({len(rows)})")
        for f in rows:
            label = f" [{f['label']}]" if f["label"] else ""
            print(f"  {f['transaction_ids']}{label} | {f['customer_id']} | "
                  f"{f['amount']:.2f} | refund: {f['refund_status']} | {f['note']}")

    print("\n== SUMMARY ==")
    for cat, count, total in summary["by_category"]:
        print(f"  {cat:<16}{count:>3} items   {total:>10.2f}")
    print(f"  Gateway total (Authorized): {summary['gateway_total']:.2f}")
    print(f"  CRM total:                  {summary['crm_total']:.2f}")
    print(f"  Unreconciled difference:    {summary['difference']:+.2f}  (gateway minus CRM)")
    print(f"  Refunds: {summary['actionable']} Actionable, {summary['escalation']} Escalation")


# ---------------------------------------------------------------
# 5. MAIN - runs everything in the agreed order
# ---------------------------------------------------------------
def main():
    gateway, invoices, accounts = load_data(DATA_FOLDER)

    missing_details = check_missing_details(accounts)
    similar = check_similar_accounts(accounts)

    findings = []
    catch_ups, claimed = find_catch_ups(gateway, invoices)
    duplicates, flagged = find_duplicates(gateway, claimed)
    claimed |= flagged
    mismatches = find_mismatches_and_conflicts(gateway, invoices, claimed)
    leftovers = find_missing_and_pending(gateway, invoices, claimed)
    findings = catch_ups + duplicates + mismatches + leftovers

    summary = build_summary(findings, gateway, invoices)
    print_report(missing_details, similar, findings, summary)
    pd.DataFrame(findings).to_csv("findings.csv", index=False)


if __name__ == "__main__":
    main()
