# Data dictionary and input contract

All amounts are **USD**. Raw monetary values use nonnegative integer cents; income/limits and transaction amounts must be positive. One source row is one customer, loan, installment or transaction. CSV headers must match the supplied order exactly. IDs and text are limited to 64 characters.

## Raw inputs

| File | Key / relationships | Fields and interpretation |
|---|---|---|
| customers.csv | customer_id | monthly_income_cents: gross monthly income; monthly_debt_cents: total monthly debt obligations **including** loan installments; revolving_balance_cents; revolving_limit_cents; home_country |
| loans.csv | loan_id → customer_id | balance_cents: outstanding loan exposure; monthly_payment_cents; originated_on |
| payments.csv | payment_id → loan_id | due_date; paid_date blank for unpaid; amount_due_cents; amount_paid_cents. Partial payments have a paid date and remain outstanding. Overpayments/prepayments are outside the simplified contract. |
| transactions.csv | transaction_id → customer_id | occurred_at in `YYYY-MM-DDTHH:MM:SS`, all interpreted as UTC; positive amount_cents; merchant_id; country |
| evaluation_labels.csv | kind + record_id | label 0/1; outcome_window. **Evaluation only**. Credit: simulated next-90-day default; fraud: injected synthetic transaction truth. |
| manifest.json | seed/as_of | Dataset provenance, account/transaction counts, intentional defects, currency and snapshot definition |

Every account must have a loan and every loan must have at least one payment observation. Dates/timestamps must be no later than the configured as-of date. This is a demonstration input contract, not a general banking ingestion specification.

## Derived fields

| Field | Definition |
|---|---|
| dti | monthly debt / monthly income; loan payment not added twice |
| utilization | revolving balance / revolving limit; values above 1 are permitted |
| days_past_due | Maximum days overdue across currently unpaid/partly unpaid installments |
| late_payment_rate | Number of historical obligations paid late or still overdue / observed obligations |
| exposure_cents | Sum of outstanding loan balances per account; revolving balance is **not** added |
| baseline_cents | Median transaction amount in preceding 30-day history, if at least 10 prior observations exist |
| amount_ratio | Current transaction amount / prior median; missing for insufficient history |
| velocity_10m | Current and preceding transactions in an inclusive 10-minute window |
| repeat_10m | Same merchant and integer-cent amount in that window, including current |
| score | Sum of triggered rule weights, capped at 100 |
| band | Low below 40; Review at 40–64; High at 65–100 by default |
| evidence | JSON array of signal ID, observed value, trigger and point contribution |
| revision | Assessment/rules/input snapshot fingerprint for matching a review to its facts |

## Review and lineage tables

`cases` contains only scores at or above each review threshold. `case_decisions` stores append-only analyst status/notes with an assessment revision. `audit_events` is inserted by a native database trigger. `pipeline_runs` retains batch IDs, timestamps, hashes, counts and runtime.

Default states: Open → Investigating / Escalated → Closed - confirmed / Closed - false positive. Analysts can reopen a case. “Confirmed” is a documented analyst conclusion for the case type, not model ground truth.

Reporting feeds add `*_usd` numeric columns for Excel. `daily_monitoring` measures **transaction activity**, not loan exposure trends. `portfolio` is a single as-of loan-exposure snapshot. Review exports escape formula-like text before writing CSVs.
