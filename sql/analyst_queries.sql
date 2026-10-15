-- Portable examples for SQLite/MySQL. Monetary fields are integer USD cents.

-- Exposure distribution: one account contributes one outstanding loan total.
SELECT band, COUNT(*) AS accounts, SUM(exposure_cents) / 100.0 AS loan_exposure_usd
FROM credit_scores GROUP BY band ORDER BY loan_exposure_usd DESC;

-- Daily fraud monitoring workload.
SELECT day, transactions, alerts, amount_cents / 100.0 AS transaction_volume_usd,
       alerts * 1.0 / transactions AS alert_rate
FROM v_daily_monitoring ORDER BY day;

-- Ten highest-priority transaction assessments with merchant detail.
SELECT s.transaction_id,s.customer_id,t.merchant_id,s.score,s.band,s.amount_ratio,s.velocity_10m
FROM fraud_scores s JOIN transactions t ON t.transaction_id=s.transaction_id
WHERE s.score>=40 ORDER BY s.score DESC,s.transaction_id LIMIT 10;

-- Latest decision for each current assessment, preserving revision semantics.
SELECT c.case_id,c.revision,COALESCE(d.status,'Open') AS current_status
FROM cases c LEFT JOIN case_decisions d ON d.decision_id=(
 SELECT d2.decision_id FROM case_decisions d2
 WHERE d2.case_id=c.case_id AND d2.revision=c.revision
 ORDER BY d2.created_at DESC,d2.decision_id DESC LIMIT 1
);

-- SQL window example: prior 10-record mean (NOT the application's 30-day median).
-- Demonstrates temporal SQL feature construction; early rows use shorter history.
SELECT transaction_id,customer_id,occurred_at,amount_cents,
 AVG(amount_cents) OVER (PARTITION BY customer_id ORDER BY occurred_at,transaction_id
 ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS prior_ten_record_mean_cents
FROM transactions;

-- Trigger-generated audit trail.
SELECT case_id,revision,analyst,status,created_at FROM audit_events ORDER BY created_at DESC;
