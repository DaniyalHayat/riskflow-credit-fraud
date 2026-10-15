"""Synthetic inputs and a strict CSV contract. Monetary values use integer cents."""
import calendar
import csv
import json
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

FIELDS = {
    "customers": ["customer_id", "monthly_income_cents", "monthly_debt_cents", "revolving_balance_cents", "revolving_limit_cents", "home_country"],
    "loans": ["loan_id", "customer_id", "balance_cents", "monthly_payment_cents", "originated_on"],
    "payments": ["payment_id", "loan_id", "due_date", "paid_date", "amount_due_cents", "amount_paid_cents"],
    "transactions": ["transaction_id", "customer_id", "occurred_at", "amount_cents", "merchant_id", "country"],
}


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def generate(folder, count=300, seed=42, as_of="2026-09-30"):
    """Fixed-seed example with ambiguous normal cases and evaluation-only labels."""
    if count < 10 or count > 10000:
        raise ValueError("Customer count must be between 10 and 10,000")
    rng = random.Random(seed)
    end = date.fromisoformat(as_of)
    start = end - timedelta(days=91)
    customers, loans, payments, tx, labels = [], [], [], [], []
    for i in range(1, count + 1):
        cid, lid = f"C{i:04d}", f"L{i:04d}"
        stress = rng.random()
        income = rng.randint(250000, 1400000)
        debt = round(income * (0.12 + 0.55 * stress + rng.uniform(-0.07, 0.10)))
        limit = rng.randint(300000, 2500000)
        balance = round(limit * min(1.20, max(0, stress + rng.uniform(-0.25, 0.25))))
        customers.append(dict(zip(FIELDS["customers"], [cid, income, debt, balance, limit, "US"])))
        installment = rng.randint(12000, min(95000, debt))
        loans.append(dict(zip(FIELDS["loans"], [lid, cid, rng.randint(200000, 5500000), installment, (start - timedelta(days=365)).isoformat()])))
        # Three historical monthly obligations, observed only through the as-of date.
        for m in range(3):
            month_index = end.year * 12 + end.month - 1 - (2 - m)
            year, zero_month = divmod(month_index, 12)
            due = date(year, zero_month + 1, min(5, calendar.monthrange(year, zero_month + 1)[1]))
            unpaid = rng.random() < max(0, stress - 0.45) * 0.60
            delay = rng.choice([0, 0, 0, 5, 15, 35]) if stress > 0.35 else rng.choice([0, 0, 1])
            paid = due + timedelta(days=delay)
            if unpaid or paid > end:
                paid = None
            payments.append(dict(zip(FIELDS["payments"], [f"P{i:04d}-{m}", lid, due.isoformat(), paid.isoformat() if paid else "", installment, installment if paid else 0])))
        # Future default is a stochastic simulated outcome, never a score input.
        probability = 1 / (1 + math.exp(-(-4.2 + 5.1 * stress)))
        labels.append({"kind": "credit", "record_id": cid, "label": int(rng.random() < probability), "outcome_window": f"{end + timedelta(days=1)} to {end + timedelta(days=90)}"})
        typical = rng.randint(1500, 20000)
        for _ in range(rng.randint(45, 75)):
            instant = datetime.combine(start + timedelta(days=rng.randrange(92)), datetime.min.time()) + timedelta(seconds=rng.randrange(86400))
            amount = max(100, round(rng.lognormvariate(math.log(typical), 0.8)))
            # Normal large purchases provide non-fraud anomalies.
            if rng.random() < 0.012:
                amount = rng.randint(200000, 1000000)
            tx.append({"customer_id": cid, "occurred_at": instant.isoformat(timespec="seconds"), "amount_cents": amount, "merchant_id": f"M{rng.randrange(1, 35):03d}", "country": rng.choice(["US"] * 98 + ["CA", "GB"]), "_label": 0})
        if rng.random() < 0.16:
            base = datetime.combine(end - timedelta(days=rng.randint(1, 20)), datetime.min.time()) + timedelta(hours=14)
            kind = rng.choice(["burst", "large", "subtle"])
            for k in range(6 if kind == "burst" else 2):
                tx.append({"customer_id": cid, "occurred_at": (base + timedelta(minutes=k)).isoformat(timespec="seconds"), "amount_cents": 35000 if kind == "burst" else rng.randint(500000, 950000) if kind == "large" else typical, "merchant_id": "M099", "country": "US" if kind == "subtle" else "ZZ", "_label": 1})
    tx.sort(key=lambda x: (x["occurred_at"], x["customer_id"]))
    for i, row in enumerate(tx, 1):
        row["transaction_id"] = f"T{i:07d}"
        labels.append({"kind": "fraud", "record_id": row["transaction_id"], "label": row.pop("_label"), "outcome_window": "synthetic transaction truth"})
    # Intentional bad rows exercise quarantine; original rows remain untouched.
    dirty = [dict(tx[0]), {**tx[1], "transaction_id": "BAD-MISSING", "amount_cents": ""}, {**tx[2], "transaction_id": "BAD-ORPHAN", "customer_id": "C99999"}, {**tx[3], "transaction_id": "BAD-NEGATIVE", "amount_cents": -100}, {**tx[4], "transaction_id": "BAD-FUTURE", "occurred_at": f"{end + timedelta(days=1)}T12:00:00"}]
    for name, rows in [("customers", customers), ("loans", loans), ("payments", payments), ("transactions", tx + dirty)]:
        write_csv(Path(folder) / f"{name}.csv", rows, FIELDS[name])
    write_csv(Path(folder) / "evaluation_labels.csv", labels)
    manifest = {"seed": seed, "as_of": as_of, "customers": count, "valid_transactions": len(tx), "intentional_invalid_rows": len(dirty), "source": "Entirely synthetic; generated by riskflow/data.py", "currency": "USD", "snapshot": "Customer and loan attributes observed as of reporting date; transactions/payments bounded by that date."}
    (Path(folder) / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def read_validated(folder, as_of):
    accepted, rejected, stats = {}, [], {}
    end = date.fromisoformat(as_of)
    customer_ids, loan_ids = set(), set()
    for name, fields in FIELDS.items():
        rows, seen, input_count, input_cents = [], set(), 0, 0
        with (Path(folder) / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != fields:
                raise ValueError(f"{name}.csv headers must exactly match {fields}")
            for line, raw in enumerate(reader, 2):
                input_count += 1
                if name == "transactions":
                    try:
                        input_cents += int(raw["amount_cents"])
                    except (ValueError, TypeError):
                        pass
                try:
                    if None in raw:
                        raise ValueError("Unexpected extra columns")
                    row = dict(raw)
                    for key in fields:
                        if key != "paid_date" and (row[key] is None or not row[key].strip()):
                            raise ValueError(f"Missing {key}")
                        if row[key] is not None and len(row[key]) > 64:
                            raise ValueError(f"Value too long: {key}")
                        if key.endswith("_cents"):
                            row[key] = int(row[key])
                            if row[key] < 0 or row[key] > 2_000_000_000:
                                raise ValueError(f"Out-of-range {key}")
                    primary = row[fields[0]]
                    if primary in seen:
                        raise ValueError("Duplicate primary key")
                    if name in ("loans", "transactions") and row["customer_id"] not in customer_ids:
                        raise ValueError("Unknown customer_id")
                    if name == "payments" and row["loan_id"] not in loan_ids:
                        raise ValueError("Unknown loan_id")
                    for key in ("originated_on", "due_date", "paid_date"):
                        if key in row and row[key]:
                            parsed = date.fromisoformat(row[key])
                            if parsed > end:
                                raise ValueError(f"Future {key}")
                    if name == "customers" and (row["monthly_income_cents"] <= 0 or row["revolving_limit_cents"] <= 0):
                        raise ValueError("Income and revolving limit must be positive")
                    if name == "loans" and row["monthly_payment_cents"] <= 0:
                        raise ValueError("Monthly payment must be positive")
                    if name == "payments":
                        if row["amount_due_cents"] <= 0 or row["amount_paid_cents"] > row["amount_due_cents"]:
                            raise ValueError("Invalid payment amounts")
                        if bool(row["paid_date"]) != (row["amount_paid_cents"] > 0):
                            raise ValueError("Paid date and paid amount disagree")
                        if row["paid_date"] and row["paid_date"] < row["due_date"]:
                            raise ValueError("Prepayments outside this installment contract")
                    if name == "transactions":
                        moment = datetime.fromisoformat(row["occurred_at"])
                        if moment.tzinfo is not None or len(row["occurred_at"]) != 19:
                            raise ValueError("Use YYYY-MM-DDTHH:MM:SS in UTC without offset")
                        if moment.date() > end or row["amount_cents"] <= 0:
                            raise ValueError("Future timestamp or nonpositive amount")
                    seen.add(primary)
                    rows.append(row)
                except (ValueError, TypeError) as exc:
                    rejected.append({"source": name, "line": line, "record_id": raw.get(fields[0], ""), "reason": str(exc), "raw_json": json.dumps(raw, sort_keys=True)})
        accepted[name] = rows
        stats[name] = {"input_rows": input_count, "accepted_rows": len(rows), "rejected_rows": input_count - len(rows)}
        if name == "transactions":
            stats[name].update(input_parseable_amount_cents=input_cents, accepted_amount_cents=sum(x["amount_cents"] for x in rows))
        if name == "customers":
            customer_ids = seen
        elif name == "loans":
            loan_ids = seen
    if not accepted["customers"] or not accepted["transactions"]:
        raise ValueError("No usable customers or transactions; database has not been replaced")
    # Prevent partial credit assessments when any required customer/loan/payment data failed.
    if any(stats[name]["rejected_rows"] for name in ("customers", "loans", "payments")):
        raise ValueError("Credit source failed validation; correct customer/loan/payment records before publishing")
    if any(not any(l["customer_id"] == c["customer_id"] for l in accepted["loans"]) for c in accepted["customers"]):
        raise ValueError("Every customer must have a loan under this demo contract")
    if any(not any(p["loan_id"] == l["loan_id"] for p in accepted["payments"]) for l in accepted["loans"]):
        raise ValueError("Every loan must have at least one payment observation")
    return accepted, rejected, stats
