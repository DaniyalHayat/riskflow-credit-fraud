CREATE TABLE IF NOT EXISTS customers (
 customer_id TEXT PRIMARY KEY, monthly_income_cents INTEGER NOT NULL CHECK(monthly_income_cents>0),
 monthly_debt_cents INTEGER NOT NULL CHECK(monthly_debt_cents>=0), revolving_balance_cents INTEGER NOT NULL,
 revolving_limit_cents INTEGER NOT NULL CHECK(revolving_limit_cents>0), home_country TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS loans (
 loan_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(customer_id),
 balance_cents INTEGER NOT NULL, monthly_payment_cents INTEGER NOT NULL, originated_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
 payment_id TEXT PRIMARY KEY, loan_id TEXT NOT NULL REFERENCES loans(loan_id), due_date TEXT NOT NULL,
 paid_date TEXT NOT NULL, amount_due_cents INTEGER NOT NULL, amount_paid_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
 transaction_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(customer_id),
 occurred_at TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents>0), merchant_id TEXT NOT NULL, country TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_transactions_customer_time ON transactions(customer_id,occurred_at);
CREATE TABLE IF NOT EXISTS credit_scores (
 customer_id TEXT PRIMARY KEY REFERENCES customers(customer_id), dti REAL NOT NULL, utilization REAL NOT NULL,
 days_past_due INTEGER NOT NULL, late_payment_rate REAL NOT NULL, exposure_cents INTEGER NOT NULL,
 score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100), band TEXT NOT NULL, evidence TEXT NOT NULL, revision TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fraud_scores (
 transaction_id TEXT PRIMARY KEY REFERENCES transactions(transaction_id), customer_id TEXT NOT NULL,
 occurred_at TEXT NOT NULL, amount_cents INTEGER NOT NULL, baseline_cents REAL, amount_ratio REAL,
 velocity_10m INTEGER NOT NULL, repeat_10m INTEGER NOT NULL, score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
 band TEXT NOT NULL, evidence TEXT NOT NULL, revision TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_fraud_scores_score ON fraud_scores(score);
CREATE TABLE IF NOT EXISTS cases (
 case_id TEXT PRIMARY KEY, kind TEXT NOT NULL, record_id TEXT NOT NULL, customer_id TEXT NOT NULL,
 score INTEGER NOT NULL, band TEXT NOT NULL, amount_cents INTEGER NOT NULL, evidence TEXT NOT NULL, revision TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS case_decisions (
 decision_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, revision TEXT NOT NULL, status TEXT NOT NULL,
 analyst TEXT NOT NULL, notes TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_decisions_case ON case_decisions(case_id,revision,created_at);
CREATE TABLE IF NOT EXISTS audit_events (
 event_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, revision TEXT NOT NULL, event_type TEXT NOT NULL,
 analyst TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS tr_decision_audit AFTER INSERT ON case_decisions
BEGIN
 INSERT INTO audit_events(event_id,case_id,revision,event_type,analyst,status,created_at)
 VALUES(NEW.decision_id,NEW.case_id,NEW.revision,'case_decision',NEW.analyst,NEW.status,NEW.created_at);
END;
CREATE TABLE IF NOT EXISTS pipeline_runs (
 run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, as_of TEXT NOT NULL, rules_hash TEXT NOT NULL,
 input_hash TEXT NOT NULL, duration_seconds REAL NOT NULL, stats_json TEXT NOT NULL
);
CREATE VIEW IF NOT EXISTS v_portfolio_risk AS
 SELECT band, COUNT(*) AS accounts, SUM(exposure_cents) AS exposure_cents, AVG(score) AS average_score
 FROM credit_scores GROUP BY band;
CREATE VIEW IF NOT EXISTS v_daily_monitoring AS
 SELECT substr(occurred_at,1,10) AS day, COUNT(*) AS transactions, SUM(amount_cents) AS amount_cents,
 SUM(CASE WHEN band<>'Low' THEN 1 ELSE 0 END) AS alerts FROM fraud_scores GROUP BY substr(occurred_at,1,10);
