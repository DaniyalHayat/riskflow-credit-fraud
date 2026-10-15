-- statement
CREATE TABLE IF NOT EXISTS customers (
 customer_id VARCHAR(64) PRIMARY KEY, monthly_income_cents BIGINT NOT NULL CHECK(monthly_income_cents>0),
 monthly_debt_cents BIGINT NOT NULL CHECK(monthly_debt_cents>=0), revolving_balance_cents BIGINT NOT NULL,
 revolving_limit_cents BIGINT NOT NULL CHECK(revolving_limit_cents>0), home_country VARCHAR(64) NOT NULL
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS loans (
 loan_id VARCHAR(64) PRIMARY KEY, customer_id VARCHAR(64) NOT NULL,
 balance_cents BIGINT NOT NULL, monthly_payment_cents BIGINT NOT NULL, originated_on VARCHAR(64) NOT NULL,
 FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS payments (
 payment_id VARCHAR(64) PRIMARY KEY, loan_id VARCHAR(64) NOT NULL, due_date VARCHAR(64) NOT NULL,
 paid_date VARCHAR(64) NOT NULL, amount_due_cents BIGINT NOT NULL, amount_paid_cents BIGINT NOT NULL,
 FOREIGN KEY(loan_id) REFERENCES loans(loan_id)
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS transactions (
 transaction_id VARCHAR(64) PRIMARY KEY, customer_id VARCHAR(64) NOT NULL, occurred_at VARCHAR(64) NOT NULL,
 amount_cents BIGINT NOT NULL CHECK(amount_cents>0), merchant_id VARCHAR(64) NOT NULL, country VARCHAR(64) NOT NULL,
 INDEX ix_transactions_customer_time(customer_id,occurred_at), FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS credit_scores (
 customer_id VARCHAR(64) PRIMARY KEY, dti DOUBLE NOT NULL, utilization DOUBLE NOT NULL, days_past_due INT NOT NULL,
 late_payment_rate DOUBLE NOT NULL, exposure_cents BIGINT NOT NULL, score INT NOT NULL CHECK(score BETWEEN 0 AND 100),
 band VARCHAR(16) NOT NULL, evidence TEXT NOT NULL, revision VARCHAR(64) NOT NULL,
 FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS fraud_scores (
 transaction_id VARCHAR(64) PRIMARY KEY, customer_id VARCHAR(64) NOT NULL, occurred_at VARCHAR(64) NOT NULL,
 amount_cents BIGINT NOT NULL, baseline_cents DOUBLE, amount_ratio DOUBLE, velocity_10m INT NOT NULL,
 repeat_10m INT NOT NULL, score INT NOT NULL CHECK(score BETWEEN 0 AND 100), band VARCHAR(16) NOT NULL,
 evidence TEXT NOT NULL, revision VARCHAR(64) NOT NULL, INDEX ix_fraud_scores_score(score),
 FOREIGN KEY(transaction_id) REFERENCES transactions(transaction_id)
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS cases (
 case_id VARCHAR(64) PRIMARY KEY, kind VARCHAR(16) NOT NULL, record_id VARCHAR(64) NOT NULL,
 customer_id VARCHAR(64) NOT NULL, score INT NOT NULL, band VARCHAR(16) NOT NULL,
 amount_cents BIGINT NOT NULL, evidence TEXT NOT NULL, revision VARCHAR(64) NOT NULL
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS case_decisions (
 decision_id VARCHAR(64) PRIMARY KEY, case_id VARCHAR(64) NOT NULL, revision VARCHAR(64) NOT NULL,
 status VARCHAR(32) NOT NULL, analyst VARCHAR(64) NOT NULL, notes TEXT NOT NULL, created_at VARCHAR(64) NOT NULL,
 INDEX ix_decisions_case(case_id,revision,created_at)
) ENGINE=InnoDB;
-- statement
CREATE TABLE IF NOT EXISTS audit_events (
 event_id VARCHAR(64) PRIMARY KEY, case_id VARCHAR(64) NOT NULL, revision VARCHAR(64) NOT NULL,
 event_type VARCHAR(32) NOT NULL, analyst VARCHAR(64) NOT NULL, status VARCHAR(32) NOT NULL, created_at VARCHAR(64) NOT NULL
) ENGINE=InnoDB;
-- statement
CREATE TRIGGER IF NOT EXISTS tr_decision_audit AFTER INSERT ON case_decisions FOR EACH ROW
 INSERT INTO audit_events(event_id,case_id,revision,event_type,analyst,status,created_at)
 VALUES(NEW.decision_id,NEW.case_id,NEW.revision,'case_decision',NEW.analyst,NEW.status,NEW.created_at);
-- statement
CREATE TABLE IF NOT EXISTS pipeline_runs (
 run_id VARCHAR(64) PRIMARY KEY, created_at VARCHAR(64) NOT NULL, as_of VARCHAR(64) NOT NULL,
 rules_hash VARCHAR(64) NOT NULL, input_hash VARCHAR(64) NOT NULL, duration_seconds DOUBLE NOT NULL, stats_json TEXT NOT NULL
) ENGINE=InnoDB;
-- statement
CREATE OR REPLACE VIEW v_portfolio_risk AS
 SELECT band, COUNT(*) AS accounts, SUM(exposure_cents) AS exposure_cents, AVG(score) AS average_score
 FROM credit_scores GROUP BY band;
-- statement
CREATE OR REPLACE VIEW v_daily_monitoring AS
 SELECT SUBSTRING(occurred_at,1,10) AS day, COUNT(*) AS transactions, SUM(amount_cents) AS amount_cents,
 SUM(CASE WHEN band<>'Low' THEN 1 ELSE 0 END) AS alerts FROM fraud_scores GROUP BY SUBSTRING(occurred_at,1,10);
