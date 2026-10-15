# Five-minute interview demonstration

Start with `python -m riskflow demo` then `python -m riskflow serve`. Open the dashboard and example workbook before the interview.

1. **Problem and user (30 seconds).** “I built a synthetic analyst workspace to prioritize credit reviews and suspicious transactions, show the evidence, and capture review decisions.” Explain that a credit review priority and a fraud alert are different outcomes.
2. **Portfolio view (45 seconds).** Show 300 accounts, outstanding loan exposure, 18,219 monitored transactions and the separate queues. Explain why transaction volume is not loan exposure and why a snapshot cannot show loan-exposure growth.
3. **Credit case (60 seconds).** Open `credit:C0005`. Inspect DTI, utilization, days past due and late history. Show the repayment records. Discuss why fully paid but late installments are not currently overdue. Save a clearly identified demonstration note with status Investigating.
4. **Fraud case (60 seconds).** In the queue filter Type to Fraud monitoring. Open a case with amount/velocity/repeated-payment evidence. Explain how the baseline excludes the current transaction and later records. An alert means “review,” not proven fraud.
5. **AI and review history (30 seconds).** Generate the offline template, or a live AI summary if configured and already tested. Show evidence IDs and explain the checks and limitations. Demonstrate that a saved decision creates an audit event and that unchanged reruns preserve status.
6. **Measurement and Excel (60 seconds).** Show synthetic precision/recall and move a review-threshold slider. Discuss review workload versus misses. Open Excel, change the credit review threshold in Controls, and show the count/credit bands update. Reset it to 40. Explain the optional CSV/Power Query refresh.
7. **Close with a tradeoff (15 seconds).** “I chose a reproducible batch workflow and transparent heuristics first. The next evidence-gathering step would be a permitted dataset and a temporal holdout, plus analyst usability testing.”

## Questions to prepare for

- Why are the scores not default probabilities? Because weights are illustrative; there is no fitted/calibrated model.
- How do you prevent leakage? Separate label file; cutoff validation; prior-only transaction baselines; append-after-score processing.
- What if the job fails halfway? Current database data is replaced in one transaction; failures roll back. Filesystem report export is a separate post-commit step.
- What happens to old reviews? Batch input/rules revision changes reopen current cases while history remains.
- Why SQL and Python? SQL manages keys, indexes, views and audit triggers; Python handles strict ingestion and temporal feature/scoring logic.
- What proves AI quality? Structural/reference/numeric checks and test fixtures; no claim that they fully verify semantics.
- What did you learn or change yourself? Be specific about your own work; review the supplied code, run it and make an improvement you can defend.
