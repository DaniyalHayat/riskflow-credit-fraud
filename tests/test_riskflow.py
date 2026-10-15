import copy
import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from riskflow.ai import fact_packet, summarize, validate
from riskflow.config import rules
from riskflow.data import generate, read_validated
from riskflow.db import Database
from riskflow.evaluate import evaluate, metrics
from riskflow.export import export_reports
from riskflow.pipeline import run
from riskflow.review import get_case, list_cases, save_decision
from riskflow.scoring import band, credit_assessments, fraud_assessments
from riskflow.web import scenario


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.rules = rules()

    def test_exact_band_boundaries(self):
        config = self.rules['credit']
        self.assertEqual([band(s, config) for s in [39, 40, 64, 65, 100]], ['Low', 'Review', 'Review', 'High', 'High'])

    def test_paid_late_is_not_current_delinquency(self):
        customer = {'customer_id': 'C1', 'monthly_income_cents': 100000, 'monthly_debt_cents': 35000, 'revolving_balance_cents': 50000, 'revolving_limit_cents': 100000}
        loan = {'customer_id': 'C1', 'loan_id': 'L1', 'balance_cents': 10000}
        payment = {'loan_id': 'L1', 'due_date': '2026-07-01', 'paid_date': '2026-07-10', 'amount_due_cents': 1000, 'amount_paid_cents': 1000}
        score = credit_assessments([customer], [loan], [payment], self.rules['credit'], '2026-09-30')[0]
        self.assertEqual(score['days_past_due'], 0)
        self.assertEqual(score['late_payment_rate'], 1)
        self.assertEqual(score['score'], 40)
        self.assertEqual({e['id'] for e in score['evidence']}, {'dti_moderate', 'utilization_moderate', 'late_rate'})

    def test_unpaid_and_partial_payments_remain_past_due(self):
        customer = {'customer_id': 'C1', 'monthly_income_cents': 100000, 'monthly_debt_cents': 10000, 'revolving_balance_cents': 10000, 'revolving_limit_cents': 100000}
        loan = {'customer_id': 'C1', 'loan_id': 'L1', 'balance_cents': 10000}
        for paid_date, paid_amount in [('', 0), ('2026-07-10', 500)]:
            payment = {'loan_id': 'L1', 'due_date': '2026-07-01', 'paid_date': paid_date, 'amount_due_cents': 1000, 'amount_paid_cents': paid_amount}
            score = credit_assessments([customer], [loan], [payment], self.rules['credit'], '2026-09-30')[0]
            self.assertEqual(score['days_past_due'], 91)

    def tx(self, index, at, amount=1000):
        return {'transaction_id': f'T{index:04d}', 'customer_id': 'C1', 'occurred_at': at, 'amount_cents': amount, 'merchant_id': 'M1', 'country': 'US'}

    def test_current_transaction_does_not_contaminate_baseline(self):
        tx = [self.tx(i, f'2026-09-{i+1:02d}T12:00:00') for i in range(10)]
        tx += [self.tx(11, '2026-09-15T12:00:00', 5000)]
        final = fraud_assessments(tx, self.rules['fraud'])[-1]
        self.assertEqual(final['baseline_cents'], 1000)
        self.assertEqual(final['amount_ratio'], 5)
        self.assertIn('amount_spike', {e['id'] for e in final['evidence']})

    def test_appending_future_records_does_not_change_past_scores(self):
        tx = [self.tx(i, f'2026-09-{i+1:02d}T12:00:00') for i in range(10)]
        before = fraud_assessments(tx, self.rules['fraud'])
        after = fraud_assessments(tx + [self.tx(20, '2026-09-30T12:00:00', 900000)], self.rules['fraud'])
        self.assertEqual(before, after[:-1])

    def test_velocity_window_inclusive_then_expires(self):
        tx = [self.tx(1, '2026-09-01T12:00:00'), self.tx(2, '2026-09-01T12:01:00'), self.tx(3, '2026-09-01T12:02:00'), self.tx(4, '2026-09-01T12:10:00'), self.tx(5, '2026-09-01T12:20:01')]
        scored = fraud_assessments(tx, self.rules['fraud'])
        self.assertEqual(scored[3]['velocity_10m'], 4)
        self.assertEqual(scored[4]['velocity_10m'], 1)

    def test_cold_start_has_no_invented_baseline(self):
        result = fraud_assessments([self.tx(1, '2026-09-01T12:00:00')], self.rules['fraud'])[0]
        self.assertIsNone(result['baseline_cents'])
        self.assertIsNone(result['amount_ratio'])

    def test_empty_metrics_expose_undefined_rates(self):
        result = metrics([], 40)
        self.assertIsNone(result['precision'])
        self.assertIsNone(result['recall'])
        self.assertIsNone(result['alert_rate'])

    def test_confusion_matrix(self):
        result = metrics([(50,1),(50,0),(20,1),(20,0)], 40)
        self.assertEqual([result[k] for k in ['true_positive','false_positive','false_negative','true_negative']], [1,1,1,1])
        self.assertEqual(result['precision'], 0.5)


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.raw = cls.root/'raw'
        cls.rules = rules()
        cls.manifest = generate(cls.raw, count=35, seed=42, as_of=cls.rules['as_of'])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.db = Database('sqlite', ':memory:')
        self.report_dir = self.root/self.id().rsplit('.',1)[-1]
        self.report = run(self.db, self.raw, self.report_dir, self.rules)

    def tearDown(self):
        self.db.close()

    def test_quarantine_reconciles_counts_and_cents(self):
        accepted, rejected, stats = read_validated(self.raw, self.rules['as_of'])
        self.assertEqual(len(rejected), 5)
        self.assertEqual(len(accepted['transactions']), self.manifest['valid_transactions'])
        self.assertEqual(stats['transactions']['input_rows'], stats['transactions']['accepted_rows']+5)
        self.assertEqual(self.report['reconciliation']['transaction_amount_difference_cents'], 0)
        self.assertEqual(int(self.db.rows('SELECT SUM(amount_cents) AS amount FROM transactions')[0]['amount']), stats['transactions']['accepted_amount_cents'])

    def test_replay_preserves_case_decisions_and_audit(self):
        case = list_cases(self.db)[0]
        save_decision(self.db, case['case_id'], case['revision'], 'Investigating', 'Demo analyst', 'Verified source records.')
        before = self.db.rows('SELECT * FROM credit_scores ORDER BY customer_id')
        run(self.db, self.raw, self.report_dir, self.rules)
        self.assertEqual(before, self.db.rows('SELECT * FROM credit_scores ORDER BY customer_id'))
        self.assertEqual(get_case(self.db, case['case_id'])['status'], 'Investigating')
        self.assertEqual(len(self.db.rows('SELECT * FROM audit_events')), 1)
        self.assertEqual(len(self.db.rows('SELECT * FROM pipeline_runs')), 2)

    def test_changed_rule_revision_reopens_review(self):
        case = list_cases(self.db)[0]
        save_decision(self.db, case['case_id'], case['revision'], 'Closed - confirmed', 'Analyst', 'Reviewed synthetic issue.')
        changed = copy.deepcopy(self.rules)
        changed['version'] = '1.0.1'
        run(self.db, self.raw, self.report_dir, changed)
        current = get_case(self.db, case['case_id'])
        self.assertEqual(current['status'], 'Open')
        self.assertEqual(len(current['history']), 1)
        with self.assertRaises(ValueError):
            save_decision(self.db, case['case_id'], case['revision'], 'Escalated', 'Analyst', 'Stale review rejected.')

    def test_failed_credit_input_does_not_replace_good_database(self):
        altered = self.root/'altered'
        generate(altered, count=35)
        contents = (altered/'customers.csv').read_text()
        header, first, *rest = contents.splitlines()
        fields = first.split(','); fields[1] = '0'
        (altered/'customers.csv').write_text('\n'.join([header,','.join(fields),*rest])+'\n')
        before = self.db.rows('SELECT * FROM credit_scores ORDER BY customer_id')
        with self.assertRaises(ValueError):
            run(self.db, altered, self.report_dir, self.rules)
        self.assertEqual(before, self.db.rows('SELECT * FROM credit_scores ORDER BY customer_id'))

    def test_database_failure_rolls_back_all_tables(self):
        before = self.db.rows('SELECT * FROM credit_scores ORDER BY customer_id')
        with patch.object(self.db, 'insert_many', side_effect=RuntimeError('injected load failure')):
            with self.assertRaises(RuntimeError):
                run(self.db, self.raw, self.report_dir, self.rules)
        self.assertEqual(before, self.db.rows('SELECT * FROM credit_scores ORDER BY customer_id'))

    def test_labels_never_enter_scoring(self):
        copy_dir = self.root/'no_labels'
        copy_dir.mkdir(exist_ok=True)
        for name in ['customers','loans','payments','transactions']:
            (copy_dir/f'{name}.csv').write_bytes((self.raw/f'{name}.csv').read_bytes())
        before = self.db.rows('SELECT * FROM fraud_scores ORDER BY transaction_id')
        run(self.db, copy_dir, self.report_dir, self.rules)
        self.assertEqual(before, self.db.rows('SELECT * FROM fraud_scores ORDER BY transaction_id'))

    def test_invalid_review_does_not_create_audit(self):
        case = list_cases(self.db)[0]
        with self.assertRaises(ValueError):
            save_decision(self.db, case['case_id'], case['revision'], 'Bad status', 'Analyst', 'Valid notes')
        self.assertFalse(self.db.rows('SELECT * FROM audit_events'))

    def test_multiple_decisions_are_append_only(self):
        case = list_cases(self.db)[0]
        for status in ['Investigating','Escalated','Closed - false positive']:
            save_decision(self.db, case['case_id'], case['revision'], status, 'Analyst', 'Investigated source evidence.')
        current = get_case(self.db, case['case_id'])
        self.assertEqual(current['status'], 'Closed - false positive')
        self.assertEqual(len(current['history']), 3)
        self.assertEqual(len(self.db.rows('SELECT * FROM audit_events')), 3)

    def test_export_protects_formula_like_notes(self):
        case = list_cases(self.db)[0]
        save_decision(self.db, case['case_id'], case['revision'], 'Investigating', '=SUM(A1)', '=HYPERLINK("bad")')
        export_reports(self.db, self.report_dir)
        self.assertIn("'=HYPERLINK", (self.report_dir/'case_queue.csv').read_text())

    def test_evaluation_and_scenarios_cover_all_scores(self):
        result = evaluate(self.db, self.raw, self.report_dir, self.rules)
        self.assertEqual(result['results']['credit']['observations'], 35)
        self.assertEqual(result['results']['fraud']['observations'], self.manifest['valid_transactions'])
        low, high = scenario(self.db, 'fraud', 20), scenario(self.db, 'fraud', 80)
        self.assertGreaterEqual(low['reviewed_records'], high['reviewed_records'])

    def test_source_view_excludes_later_ids_at_same_timestamp(self):
        case=list_cases(self.db,'fraud')[0]
        scored=get_case(self.db,case['case_id'])
        original=self.db.rows('SELECT * FROM transactions WHERE transaction_id=?',(case['record_id'],))[0]
        original['transaction_id']='ZZ-LATER'
        with self.db.transaction():
            self.db.insert_many('transactions',[original])
        source=get_case(self.db,case['case_id'])['source_records']
        self.assertNotIn('ZZ-LATER',{r['transaction_id'] for r in source})

    def test_export_normalizes_mysql_decimal_aggregates(self):
        class AggregateDB:
            def rows(self, statement):
                if 'v_daily_monitoring' in statement:
                    return [{'day':'2026-09-30','transactions':3,'amount_cents':Decimal('301'),'alerts':Decimal('1')}]
                if 'v_portfolio_risk' in statement:
                    return [{'band':'Low','accounts':1,'exposure_cents':Decimal('301'),'average_score':Decimal('25.0')}]
                return []
        with patch('riskflow.export.list_cases', return_value=[]):
            export_reports(AggregateDB(),self.report_dir)
        result=json.loads((self.report_dir/'workbook_data.json').read_text())
        self.assertEqual(result['daily_monitoring'][0]['amount_cents'],301)
        self.assertEqual(result['portfolio'][0]['exposure_usd'],3.01)


class AITests(unittest.TestCase):
    def setUp(self):
        self.case = {'case_id':'credit:C1','customer_id':'C1','kind':'credit','score':65,'band':'High','revision':'rev1','evidence':[{'id':'dti_high','value':0.65,'threshold':0.50,'points':30}]}
        self.valid = {'summary':'Debt-to-income exceeded the configured threshold.', 'observations':[{'evidence_id':'dti_high','explanation':'The supplied debt-to-income flag contributed 30 points.'}], 'next_steps':['Inspect source records']}

    def test_offline_is_labeled_not_ai(self):
        result = summarize(self.case)
        self.assertEqual(result['provider'], 'offline-template')
        self.assertIsNone(result['warning'])

    def test_unknown_evidence_is_rejected(self):
        result = copy.deepcopy(self.valid)
        result['observations'][0]['evidence_id'] = 'invented'
        with self.assertRaises(ValueError):
            validate(result, fact_packet(self.case))

    def test_invented_number_is_rejected(self):
        result = copy.deepcopy(self.valid)
        result['summary'] = 'Risk is 97 percent.'
        with self.assertRaises(ValueError):
            validate(result, fact_packet(self.case))

    def test_openai_request_and_response_contract(self):
        response = {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.valid)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test-key','OPENAI_MODEL':'test-model'}), patch('riskflow.ai.request_json', return_value=response) as request:
            result = summarize(self.case, 'openai')
        self.assertEqual(result['provider'], 'openai')
        self.assertFalse(request.call_args.args[1]['store'])
        self.assertTrue(request.call_args.args[1]['text']['format']['strict'])
        self.assertNotIn('notes', request.call_args.args[1]['input'])

    def test_provider_failure_falls_back_visibly(self):
        with patch('riskflow.ai.request_json', side_effect=OSError('offline')):
            result = summarize(self.case, 'ollama')
        self.assertEqual(result['provider'], 'offline-template')
        self.assertIsNotNone(result['warning'])

    def test_refusal_falls_back(self):
        response={'status':'completed','output':[{'content':[{'type':'refusal','refusal':'No'}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test','OPENAI_MODEL':'test'}), patch('riskflow.ai.request_json', return_value=response):
            result=summarize(self.case,'openai')
        self.assertEqual(result['provider'],'offline-template')
        self.assertIsNotNone(result['warning'])

    def test_ollama_schema_contract(self):
        with patch('riskflow.ai.request_json', return_value={'done':True,'response':json.dumps(self.valid)}) as request:
            result=summarize(self.case,'ollama')
        self.assertEqual(result['provider'],'ollama')
        self.assertFalse(request.call_args.args[1]['stream'])


@unittest.skipUnless(os.getenv('RISKFLOW_TEST_MYSQL') == '1', 'Optional live MySQL integration; enabled in GitHub CI')
class MySQLIntegration(unittest.TestCase):
    def test_live_backend_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder, Database('mysql') as db:
            config=rules(); raw=Path(folder)/'raw'; reports=Path(folder)/'reports'
            generate(raw, 35, as_of=config['as_of'])
            run(db, raw, reports, config)
            case=list_cases(db)[0]
            save_decision(db, case['case_id'],case['revision'],'Investigating','CI analyst','Verified live MySQL trigger.')
            self.assertTrue(db.rows('SELECT * FROM audit_events WHERE case_id=?',(case['case_id'],)))
            run(db, raw, reports, config)
            self.assertEqual(get_case(db,case['case_id'])['status'],'Investigating')
            self.assertEqual(evaluate(db,raw,reports,config)['results']['credit']['observations'],35)
            export_reports(db,reports)


if __name__ == '__main__':
    unittest.main()
