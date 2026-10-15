"""Explainable heuristics. No labels or future observations are used."""
import hashlib
import json
import statistics
from collections import defaultdict, deque
from datetime import date, datetime, timedelta


def revision(score, evidence, rules_hash):
    return hashlib.sha256(json.dumps([score, evidence, rules_hash], sort_keys=True).encode()).hexdigest()[:20]


def band(score, config):
    return "High" if score >= config["high_threshold"] else "Review" if score >= config["review_threshold"] else "Low"


def credit_assessments(customers, loans, payments, config, as_of):
    loan_map, pay_map = defaultdict(list), defaultdict(list)
    for loan in loans:
        loan_map[loan["customer_id"]].append(loan)
    for payment in payments:
        pay_map[payment["loan_id"]].append(payment)
    end = date.fromisoformat(as_of)
    result = []
    for customer in customers:
        cid = customer["customer_id"]
        observations = [p for loan in loan_map[cid] for p in pay_map[loan["loan_id"]] if p["due_date"] <= as_of]
        dpd, late = 0, 0
        for p in observations:
            due = date.fromisoformat(p["due_date"])
            paid = date.fromisoformat(p["paid_date"]) if p["paid_date"] else None
            fully_paid = paid is not None and paid <= end and p["amount_paid_cents"] >= p["amount_due_cents"]
            delay = (paid - due).days if fully_paid else (end - due).days
            late += int(delay > 0)
            if not fully_paid:
                dpd = max(dpd, max(0, delay))
        dti = customer["monthly_debt_cents"] / customer["monthly_income_cents"]
        utilization = customer["revolving_balance_cents"] / customer["revolving_limit_cents"]
        late_rate = late / len(observations) if observations else None
        if late_rate is None:
            raise ValueError(f"No payment history for {cid}")
        signals = []
        for metric, value in [("dti", dti), ("utilization", utilization), ("dpd", dpd)]:
            code = f"{metric}_high" if value >= config[f"{metric}_high"] else f"{metric}_moderate" if value >= config[f"{metric}_moderate"] else None
            if code:
                signals.append({"id": code, "value": round(value, 4), "threshold": config[code], "points": config["points"][code]})
        if late_rate >= config["late_rate"]:
            signals.append({"id": "late_rate", "value": round(late_rate, 4), "threshold": config["late_rate"], "points": config["points"]["late_rate"]})
        score = min(100, sum(s["points"] for s in signals))
        result.append({"customer_id": cid, "dti": round(dti, 6), "utilization": round(utilization, 6), "days_past_due": dpd, "late_payment_rate": round(late_rate, 6), "exposure_cents": sum(l["balance_cents"] for l in loan_map[cid]), "score": score, "band": band(score, config), "evidence": signals})
    return result


def fraud_assessments(transactions, config):
    histories, windows = defaultdict(deque), defaultdict(deque)
    result = []
    for row in sorted(transactions, key=lambda x: (x["occurred_at"], x["transaction_id"])):
        cid = row["customer_id"]
        instant = datetime.fromisoformat(row["occurred_at"])
        history, window = histories[cid], windows[cid]
        while history and history[0][0] < instant - timedelta(days=config["history_days"]):
            history.popleft()
        while window and window[0][0] < instant - timedelta(minutes=config["window_minutes"]):
            window.popleft()
        baseline = statistics.median(x[1]["amount_cents"] for x in history) if len(history) >= config["min_history"] else None
        ratio = row["amount_cents"] / baseline if baseline else None
        velocity = len(window) + 1
        repeats = 1 + sum(x[1]["merchant_id"] == row["merchant_id"] and x[1]["amount_cents"] == row["amount_cents"] for x in window)
        new_country = bool(baseline and row["country"] not in {x[1]["country"] for x in history})
        signals = []
        observations = [("large_amount", row["amount_cents"] >= config["large_amount_cents"], row["amount_cents"], config["large_amount_cents"]), ("amount_spike", ratio is not None and ratio >= config["amount_multiple"], round(ratio, 4) if ratio else None, config["amount_multiple"]), ("velocity", velocity >= config["velocity_count"], velocity, config["velocity_count"]), ("repeated_payment", repeats >= config["repeat_count"], repeats, config["repeat_count"]), ("new_country", new_country, row["country"], "not in prior 30-day history")]
        for code, triggered, value, threshold in observations:
            if triggered:
                signals.append({"id": code, "value": value, "threshold": threshold, "points": config["points"][code]})
        score = min(100, sum(s["points"] for s in signals))
        result.append({"transaction_id": row["transaction_id"], "customer_id": cid, "occurred_at": row["occurred_at"], "amount_cents": row["amount_cents"], "baseline_cents": baseline, "amount_ratio": round(ratio, 6) if ratio else None, "velocity_10m": velocity, "repeat_10m": repeats, "score": score, "band": band(score, config), "evidence": signals})
        # Append after scoring: baseline cannot see the current/future transaction.
        history.append((instant, row))
        window.append((instant, row))
    return result
