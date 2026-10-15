"""Transactional batch scoring, reconciliation, and transparent lineage."""
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .data import FIELDS, read_validated, write_csv
from .scoring import credit_assessments, fraud_assessments, revision


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def run(db, raw, reports, rules):
    started = time.perf_counter()
    raw, reports = Path(raw), Path(reports)
    accepted, rejects, stats = read_validated(raw, rules["as_of"])
    rules_hash = hashlib.sha256(json.dumps(rules, sort_keys=True).encode()).hexdigest()
    input_hash = hashlib.sha256(b"".join((raw / f"{name}.csv").read_bytes() for name in FIELDS)).hexdigest()
    credit = credit_assessments(accepted["customers"], accepted["loans"], accepted["payments"], rules["credit"], rules["as_of"])
    fraud = fraud_assessments(accepted["transactions"], rules["fraud"])
    cases = []
    for kind, scores, key in [("credit", credit, "customer_id"), ("fraud", fraud, "transaction_id")]:
        for score in scores:
            # All relevant account/transaction facts invalidate old decisions when changed.
            score["revision"] = revision(score, score["evidence"], [rules_hash, input_hash])
            score["evidence"] = json.dumps(score["evidence"], sort_keys=True)
            if score["score"] >= rules[kind]["review_threshold"]:
                cases.append({"case_id": f"{kind}:{score[key]}", "kind": kind, "record_id": score[key], "customer_id": score["customer_id"], "score": score["score"], "band": score["band"], "amount_cents": score.get("exposure_cents", score.get("amount_cents", 0)), "evidence": score["evidence"], "revision": score["revision"]})
    record = {"run_id": uuid.uuid4().hex, "created_at": now(), "as_of": rules["as_of"], "rules_hash": rules_hash, "input_hash": input_hash, "duration_seconds": round(time.perf_counter() - started, 4), "stats_json": json.dumps(stats, sort_keys=True)}
    db.initialize()
    with db.transaction():
        # Single atomic refresh. Dispositions and historical runs are preserved.
        for table in ["cases", "fraud_scores", "credit_scores", "transactions", "payments", "loans", "customers"]:
            db.execute(f"DELETE FROM {table}").close()
        for table, rows in accepted.items():
            db.insert_many(table, rows)
        db.insert_many("credit_scores", credit)
        db.insert_many("fraud_scores", fraud)
        db.insert_many("cases", cases)
        persisted = db.rows("SELECT COUNT(*) AS rows_loaded, SUM(amount_cents) AS amount_cents FROM transactions")[0]
        if persisted["rows_loaded"] != stats["transactions"]["accepted_rows"] or int(persisted["amount_cents"]) != stats["transactions"]["accepted_amount_cents"]:
            raise RuntimeError("Load reconciliation failed; changes rolled back")
        record["duration_seconds"] = round(time.perf_counter() - started, 4)
        db.insert_many("pipeline_runs", [record])
    reports.mkdir(parents=True, exist_ok=True)
    write_csv(reports / "quarantine.csv", rejects, ["source", "line", "record_id", "reason", "raw_json"])
    report = {**record, "stats": stats, "credit_cases": sum(c["kind"] == "credit" for c in cases), "fraud_cases": sum(c["kind"] == "fraud" for c in cases), "reconciliation": {"transaction_row_difference": 0, "transaction_amount_difference_cents": 0}}
    report.pop("stats_json")
    (reports / "pipeline_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
