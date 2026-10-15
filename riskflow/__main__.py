import argparse
import json
import sys
from .config import ROOT, rules
from .data import generate
from .db import Database
from .pipeline import run
from .evaluate import evaluate
from .export import export_reports
from .review import get_case, list_cases
from .ai import summarize
from .web import serve


def main():
    parser = argparse.ArgumentParser(description="RiskFlow credit and fraud analytics portfolio demo")
    parser.add_argument("command", choices=["demo", "generate", "pipeline", "evaluate", "export", "serve", "summary"])
    parser.add_argument("--customers", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--backend", choices=["sqlite", "mysql"])
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--provider", choices=["offline", "openai", "ollama"], default="offline")
    args = parser.parse_args()
    config = rules()
    raw, reports = ROOT / "data/raw", ROOT / "reports"
    if args.command == "serve":
        serve(args.port, args.backend)
        return
    if args.command in ("generate", "demo"):
        manifest = generate(raw, args.customers, args.seed, config["as_of"])
        print(f"Synthetic data: {manifest['customers']} customers, {manifest['valid_transactions']:,} valid transactions")
    if args.command == "generate":
        return
    with Database(args.backend) as db:
        if args.command in ("pipeline", "demo"):
            result = run(db, raw, reports, config)
            print(f"Pipeline reconciled; {result['credit_cases']} credit cases and {result['fraud_cases']} fraud cases")
        if args.command in ("evaluate", "demo"):
            result = evaluate(db, raw, reports, config)
            print(json.dumps(result["results"], indent=2))
        if args.command in ("export", "demo"):
            print("Reporting feeds:", json.dumps(export_reports(db, reports)))
        if args.command == "summary":
            cases = list_cases(db)
            if not cases:
                raise ValueError("No cases available; run demo first")
            case_id = args.case_id or cases[0]["case_id"]
            print(json.dumps(summarize(get_case(db, case_id), args.provider, reports), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"RiskFlow: {exc}", file=sys.stderr)
        sys.exit(1)
