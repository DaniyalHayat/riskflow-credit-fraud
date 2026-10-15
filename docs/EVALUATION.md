# Evaluation and interpretation

The benchmark uses 300 accounts and 18,219 valid transactions with a fixed seed of 42. Inputs are entirely synthetic. There are 80 simulated future-default accounts and 170 injected fraud transactions. The rule thresholds were fixed for this demonstration; the sensitivity grid is descriptive. There is no trained model or held-out real-world benchmark.

## Results at threshold 40

| Measure | Credit | Fraud |
|---|---:|---:|
| True positives | 64 | 85 |
| False positives | 90 | 119 |
| False negatives | 16 | 85 |
| True negatives | 130 | 17,930 |
| Precision | 64 / 154 = 41.56% | 85 / 204 = 41.67% |
| Recall | 64 / 80 = 80.00% | 85 / 170 = 50.00% |
| False-positive rate | 90 / 220 = 40.91% | 119 / 18,049 = 0.6593% |
| Alert rate | 154 / 300 = 51.33% | 204 / 18,219 = 1.1197% |

Credit results evaluate a **review-priority heuristic** against stochastic synthetic future defaults. A positive prediction means “above review cutoff,” not “will default.” Fraud results are transaction-level; a burst can contain missed early transactions and detected later transactions. Account-level incident recall would be a different metric and is not reported here.

## Why the results are imperfect

- Normal large purchases can resemble amount anomalies.
- Subtle injected fraud can resemble legitimate spending.
- A velocity rule only fires once enough prior activity exists.
- Sparse histories have no reliable median baseline.
- Future default is stochastic; high-risk indicators are not deterministic outcomes.

## Threshold sensitivity

`reports/threshold_sensitivity.csv` reports cutoffs 20, 30, 40, 50, 60, 70 and 80 separately for credit and fraud. The dashboard slider shows affected record counts and amounts. Excel controls provide editable scenarios. Previewing a threshold does not rewrite saved assessments; edit the configuration and rerun the pipeline to change those.

Undefined rates use null rather than zero. No-alert precision and no-positive recall are unavailable by definition. Quarantined rows are excluded from scoring and evaluation; accepted records must each have exactly one matching label.

## What you can claim

You can report the reproducible record counts, validation checks, synthetic precision/recall, separate risk scoring, prior-only baselines, review persistence and measured local runtime. You cannot claim real fraud prevented, lending losses reduced, improved underwriting accuracy, user time saved, or production scale from this dataset.

## More rigorous next experiment

Select a dataset with permitted use and realistic outcomes, split by time before threshold/model selection, use a validation period for choices, and report once on an untouched future test period. Compare to a simple baseline and include uncertainty, class imbalance, costs and drift. For a credit PD model, evaluate calibration separately from discrimination. Keep that future extension separate from this completed heuristic demo.
