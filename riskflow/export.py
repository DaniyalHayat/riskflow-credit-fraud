"""Portable reporting feeds for Excel and other BI tools."""
import json
from pathlib import Path
from .data import write_csv
from .review import list_cases


def export_reports(db, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    credit = db.rows("""SELECT s.*,c.monthly_income_cents,c.monthly_debt_cents,
    c.revolving_balance_cents,c.revolving_limit_cents FROM credit_scores s
    JOIN customers c ON s.customer_id=c.customer_id ORDER BY s.customer_id""")
    fraud = db.rows("SELECT * FROM fraud_scores ORDER BY occurred_at,transaction_id")
    cases = list_cases(db)
    portfolio = db.rows("SELECT * FROM v_portfolio_risk ORDER BY band")
    daily = db.rows("SELECT * FROM v_daily_monitoring ORDER BY day")
    for r in credit:
        r["exposure_usd"] = r["exposure_cents"] / 100
    for r in fraud:
        r["amount_usd"] = r["amount_cents"] / 100
    for r in cases:
        r["amount_usd"] = r["amount_cents"] / 100
        r["evidence"] = json.dumps(r["evidence"], sort_keys=True)
    for r in daily:
        r["amount_cents"] = int(r["amount_cents"])
        r["alerts"] = int(r["alerts"])
        r["transactions"] = int(r["transactions"])
        r["amount_usd"] = r["amount_cents"] / 100
        r["alert_rate"] = r["alerts"] / r["transactions"]
    for r in portfolio:
        r["exposure_usd"] = int(r["exposure_cents"]) / 100
        r["exposure_cents"] = int(r["exposure_cents"])
        r["average_score"] = float(r["average_score"])
    feeds = {"credit_assessments": credit, "fraud_assessments": fraud, "case_queue": cases, "portfolio": portfolio, "daily_monitoring": daily, "audit_events": db.rows("SELECT * FROM audit_events ORDER BY created_at,event_id")}
    fallback = {"case_queue": ["case_id", "kind", "record_id", "customer_id", "score", "band", "amount_cents", "evidence", "revision", "status", "analyst", "notes", "reviewed_at", "amount_usd"], "audit_events": ["event_id", "case_id", "revision", "event_type", "analyst", "status", "created_at"]}
    for name, rows in feeds.items():
        # CSV formula injection protection for human-entered review notes/names.
        safe = [{k: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v for k, v in row.items()} for row in rows]
        write_csv(folder / f"{name}.csv", safe, list(safe[0]) if safe else fallback.get(name, []))
    (folder / "workbook_data.json").write_text(json.dumps(feeds, indent=2), encoding="utf-8")
    return {name: len(rows) for name, rows in feeds.items()}
