"""Synthetic-label evaluation, separate from pipeline and serving paths."""
import csv
import json
from pathlib import Path
from .data import write_csv


def metrics(pairs, threshold):
    tp = sum(score >= threshold and label == 1 for score, label in pairs)
    fp = sum(score >= threshold and label == 0 for score, label in pairs)
    fn = sum(score < threshold and label == 1 for score, label in pairs)
    tn = sum(score < threshold and label == 0 for score, label in pairs)
    return {"threshold": threshold, "observations": len(pairs), "true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn, "precision": round(tp / (tp + fp), 6) if tp + fp else None, "recall": round(tp / (tp + fn), 6) if tp + fn else None, "false_positive_rate": round(fp / (fp + tn), 6) if fp + tn else None, "alert_rate": round((tp + fp) / len(pairs), 6) if pairs else None}


def evaluate(db, raw, reports, rules):
    truth = {"credit": {}, "fraud": {}}
    with (Path(raw) / "evaluation_labels.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["kind"] not in truth or row["record_id"] in truth[row["kind"]] or row["label"] not in ("0", "1"):
                raise ValueError("Invalid or duplicate evaluation label")
            truth[row["kind"]][row["record_id"]] = int(row["label"])
    results, sensitivity = {}, []
    for kind, key in [("credit", "customer_id"), ("fraud", "transaction_id")]:
        scored = db.rows(f"SELECT {key},score FROM {kind}_scores")
        if any(r[key] not in truth[kind] for r in scored):
            raise ValueError(f"Missing {kind} evaluation labels")
        pairs = [(r["score"], truth[kind][r[key]]) for r in scored]
        results[kind] = metrics(pairs, rules[kind]["review_threshold"])
        for cutoff in [20, 30, 40, 50, 60, 70, 80]:
            sensitivity.append({"kind": kind, **metrics(pairs, cutoff)})
    report = {"dataset": "Synthetic demo; no real-world performance claim", "credit_target": "Simulated default during the 90 days after the as-of date", "fraud_target": "Injected synthetic transaction label", "selection": "Fixed heuristic rules; sensitivity is descriptive, not a held-out tuning experiment", "as_of": rules["as_of"], "results": results}
    Path(reports).mkdir(parents=True, exist_ok=True)
    (Path(reports) / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(Path(reports) / "threshold_sensitivity.csv", sensitivity)
    return report
