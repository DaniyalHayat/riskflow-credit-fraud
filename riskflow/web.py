"""Loopback-only portfolio demo server; no framework or cloud account needed."""
import csv
import io
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .ai import summarize
from .config import ROOT, rules
from .db import Database
from .export import export_reports
from .review import get_case, list_cases, save_decision


def overview(db):
    credit = db.rows("SELECT * FROM v_portfolio_risk ORDER BY band")
    for row in credit:
        row["exposure_cents"] = int(row["exposure_cents"])
        row["average_score"] = float(row["average_score"])
    latest = db.rows("SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT 1")
    cases = list_cases(db)
    totals = db.rows("SELECT COUNT(*) AS transactions,SUM(amount_cents) AS amount_cents FROM transactions")[0]
    totals["amount_cents"] = int(totals["amount_cents"] or 0)
    daily = db.rows("SELECT * FROM v_daily_monitoring ORDER BY day")
    for row in daily:
        row["amount_cents"] = int(row["amount_cents"])
        row["alerts"] = int(row["alerts"])
    return {"portfolio": credit, "daily": daily, "totals": totals, "cases": len(cases), "open_cases": sum(not c["status"].startswith("Closed") for c in cases), "latest_run": latest[0] if latest else None}


def scenario(db, kind, cutoff):
    if kind not in ("credit", "fraud") or not 1 <= cutoff <= 100:
        raise ValueError("Use credit or fraud and a threshold from 1 to 100")
    table = "credit_scores" if kind == "credit" else "fraud_scores"
    value = "exposure_cents" if kind == "credit" else "amount_cents"
    row = db.rows(f"SELECT COUNT(*) AS reviewed_records, SUM({value}) AS reviewed_amount_cents FROM {table} WHERE score>=?", (cutoff,))[0]
    row["reviewed_amount_cents"] = int(row["reviewed_amount_cents"] or 0)
    row.update(kind=kind, threshold=cutoff, changes_saved=False)
    return row


def serve(port=8000, backend=None, db_path=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "RiskFlow/1.0"

        def log_message(self, fmt, *args):
            # Avoid logging potentially sensitive URLs/notes.
            pass

        def send(self, payload, status=200, content_type="application/json"):
            data = json.dumps(payload).encode() if content_type == "application/json" else payload
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def allowed_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

        def do_GET(self):
            if not self.allowed_host():
                self.send({"error": "Use the local dashboard address"}, 403)
                return
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            try:
                static = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
                if parsed.path in static:
                    types = {"/": "text/html; charset=utf-8", "/app.js": "text/javascript; charset=utf-8", "/style.css": "text/css; charset=utf-8"}
                    self.send((ROOT / "web" / static[parsed.path]).read_bytes(), content_type=types[parsed.path])
                elif parsed.path == "/api/session":
                    self.send({"csrf": self.server.csrf})
                elif parsed.path == "/api/evaluation":
                    self.send(json.loads((ROOT / "reports/evaluation.json").read_text(encoding="utf-8")))
                elif parsed.path == "/api/download":
                    name = params.get("name", [""])[0]
                    allowed = {"credit_assessments.csv", "fraud_assessments.csv", "case_queue.csv", "daily_monitoring.csv", "portfolio.csv", "audit_events.csv", "quarantine.csv", "threshold_sensitivity.csv"}
                    if name not in allowed:
                        raise KeyError("Export not found")
                    self.send((ROOT / "reports" / name).read_bytes(), content_type="text/csv; charset=utf-8")
                else:
                    with Database(backend, db_path) as db:
                        if parsed.path == "/api/overview":
                            self.send(overview(db))
                        elif parsed.path == "/api/cases":
                            cases = list_cases(db, params.get("kind", [None])[0], params.get("status", [None])[0])
                            query = params.get("search", [""])[0].lower()
                            self.send([c for c in cases if query in (c["case_id"] + c["customer_id"]).lower()])
                        elif parsed.path == "/api/case":
                            self.send(get_case(db, params.get("id", [""])[0]))
                        elif parsed.path == "/api/scenario":
                            self.send(scenario(db, params.get("kind", ["fraud"])[0], int(params.get("threshold", [40])[0])))
                        else:
                            self.send({"error": "Page not found"}, 404)
            except (KeyError, FileNotFoundError):
                self.send({"error": "Record or report not found. Run the demo pipeline first."}, 404)
            except ValueError as exc:
                self.send({"error": str(exc)}, 400)
            except Exception:
                self.send({"error": "Local database unavailable. Check setup and restart the dashboard."}, 500)

        def do_POST(self):
            expected_origin = f"http://{self.headers.get('Host')}"
            if not self.allowed_host() or self.headers.get("X-RiskFlow-CSRF") != self.server.csrf or self.headers.get("Origin", expected_origin) != expected_origin:
                self.send({"error": "Invalid local dashboard session"}, 403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16000 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("Use a JSON request up to 16 KB")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Expected a JSON object")
                with Database(backend, db_path) as db:
                    route = urlparse(self.path).path
                    if route == "/api/decision":
                        result = save_decision(db, data["case_id"], data["revision"], data["status"], data["analyst"], data["notes"])
                    elif route == "/api/summary":
                        result = summarize(get_case(db, data["case_id"]), data.get("provider", "offline"), ROOT / "reports")
                    elif route == "/api/export":
                        result = export_reports(db, ROOT / "reports")
                    else:
                        raise KeyError("Action not found")
                self.send(result)
            except (ValueError, TypeError) as exc:
                self.send({"error": str(exc)}, 400)
            except KeyError:
                self.send({"error": "Required field or case not found"}, 404)
            except Exception:
                self.send({"error": "Action failed. Check the local database and try again."}, 500)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.csrf = secrets.token_urlsafe(32)
    print(f"RiskFlow is ready: http://127.0.0.1:{server.server_port}", flush=True)
    print("Press Ctrl+C to stop the dashboard.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
