"""Persisted analyst decisions with revisions and database-triggered audit events."""
import json
import uuid
from datetime import datetime, timedelta
from .pipeline import now

STATUSES = ("Open", "Investigating", "Escalated", "Closed - confirmed", "Closed - false positive")


def list_cases(db, kind=None, status=None):
    query = """SELECT c.*, COALESCE(d.status,'Open') AS status, COALESCE(d.analyst,'') AS analyst,
    COALESCE(d.notes,'') AS notes, COALESCE(d.created_at,'') AS reviewed_at
    FROM cases c LEFT JOIN case_decisions d ON d.decision_id=(
    SELECT d2.decision_id FROM case_decisions d2 WHERE d2.case_id=c.case_id AND d2.revision=c.revision
    ORDER BY d2.created_at DESC,d2.decision_id DESC LIMIT 1) ORDER BY c.score DESC,c.case_id"""
    cases = db.rows(query)
    for case in cases:
        case["evidence"] = json.loads(case["evidence"])
    return [c for c in cases if (not kind or c["kind"] == kind) and (not status or c["status"] == status)]


def get_case(db, case_id):
    records = [c for c in list_cases(db) if c["case_id"] == case_id]
    if not records:
        raise KeyError("Case not found")
    case = records[0]
    if case["kind"] == "credit":
        case["assessment"] = db.rows("SELECT * FROM credit_scores WHERE customer_id=?", (case["record_id"],))[0]
        case["source_records"] = db.rows("SELECT p.* FROM payments p JOIN loans l ON p.loan_id=l.loan_id WHERE l.customer_id=? ORDER BY p.due_date", (case["customer_id"],))
        case["financial_profile"] = db.rows("SELECT * FROM customers WHERE customer_id=?", (case["customer_id"],))[0]
    else:
        case["assessment"] = db.rows("SELECT * FROM fraud_scores WHERE transaction_id=?", (case["record_id"],))[0]
        case["source_records"] = db.rows("""SELECT * FROM transactions WHERE customer_id=?
        AND (occurred_at < ? OR (occurred_at=? AND transaction_id<=?))
        ORDER BY occurred_at DESC,transaction_id DESC LIMIT 15""", (case["customer_id"], case["assessment"]["occurred_at"], case["assessment"]["occurred_at"], case["record_id"]))
    case["history"] = db.rows("SELECT * FROM case_decisions WHERE case_id=? ORDER BY created_at DESC,decision_id DESC", (case_id,))
    return case


def save_decision(db, case_id, revision, status, analyst, notes):
    if status not in STATUSES:
        raise ValueError("Invalid case status")
    if not isinstance(analyst, str) or not 1 <= len(analyst.strip()) <= 64:
        raise ValueError("Enter an analyst name (1-64 characters)")
    if not isinstance(notes, str) or not 5 <= len(notes.strip()) <= 2000:
        raise ValueError("Enter review notes (5-2,000 characters)")
    with db.transaction():
        lock = " FOR UPDATE" if db.backend == "mysql" else ""
        if db.backend == "sqlite":
            db.execute("BEGIN IMMEDIATE").close()
        case = db.rows("SELECT revision FROM cases WHERE case_id=?" + lock, (case_id,))
        if not case:
            raise KeyError("Case not found")
        if case[0]["revision"] != revision:
            raise ValueError("This assessment changed. Reload it before saving a decision.")
        created_at = now()
        latest = db.rows("SELECT MAX(created_at) AS latest FROM case_decisions WHERE case_id=?", (case_id,))[0]['latest']
        if latest and created_at <= latest:
            created_at = (datetime.fromisoformat(latest) + timedelta(microseconds=1)).isoformat(timespec='microseconds')
        record = {"decision_id": uuid.uuid4().hex, "case_id": case_id, "revision": revision, "status": status, "analyst": analyst.strip(), "notes": notes.strip(), "created_at": created_at}
        db.insert_many("case_decisions", [record])
    return record
