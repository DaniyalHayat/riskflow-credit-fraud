"""Real loopback HTTP checks with an isolated synthetic database."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from riskflow.config import ROOT, rules
from riskflow.data import generate
from riskflow.db import Database
from riskflow.pipeline import run


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temp.name)
        cls.database = cls.folder/'http.db'
        config = rules()
        cls.manifest = generate(cls.folder/'raw',35,as_of=config['as_of'])
        with Database('sqlite',cls.database) as db:
            run(db,cls.folder/'raw',cls.folder/'reports',config)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0))
            cls.port = probe.getsockname()[1]
        cls.url = f'http://127.0.0.1:{cls.port}'
        code = f"from riskflow.web import serve; serve({cls.port},'sqlite',{str(cls.database)!r})"
        cls.process = subprocess.Popen([sys.executable,'-c',code],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                with urllib.request.urlopen(cls.url+'/api/session',timeout=1) as response:
                    cls.csrf=json.load(response)['csrf']
                break
            except (urllib.error.URLError,TimeoutError):
                if cls.process.poll() is not None:
                    raise RuntimeError('Test HTTP server failed to start')
                time.sleep(0.05)
        else:
            cls.process.terminate()
            cls.process.wait(timeout=5)
            raise RuntimeError('Test HTTP server did not become ready')

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.temp.cleanup()

    def request(self,path,body=None,headers=None):
        actual={'Content-Type':'application/json'}
        if body is not None:
            actual['X-RiskFlow-CSRF']=self.csrf
        actual.update(headers or {})
        request=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=actual)
        with urllib.request.urlopen(request,timeout=5) as response:
            return json.load(response)

    def test_overview_uses_isolated_database(self):
        result=self.request('/api/overview')
        self.assertEqual(result['totals']['transactions'],self.manifest['valid_transactions'])
        self.assertEqual(sum(r['accounts'] for r in result['portfolio']),35)

    def test_host_and_csrf_reject_cross_origin_actions(self):
        with self.assertRaises(urllib.error.HTTPError) as bad_host:
            self.request('/api/overview',headers={'Host':'evil.example'})
        self.assertEqual(bad_host.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as bad_csrf:
            self.request('/api/decision',{},headers={'X-RiskFlow-CSRF':'wrong'})
        self.assertEqual(bad_csrf.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as bad_origin:
            self.request('/api/decision',{},headers={'Origin':'http://evil.example'})
        self.assertEqual(bad_origin.exception.code,403)

    def test_save_decision_and_history_through_http(self):
        case=self.request('/api/cases')[0]
        self.request('/api/decision',{'case_id':case['case_id'],'revision':case['revision'],'status':'Investigating','analyst':'HTTP test','notes':'Checked the isolated synthetic evidence.'})
        result=self.request('/api/case?id='+case['case_id'])
        self.assertEqual(result['status'],'Investigating')
        self.assertTrue(result['source_records'])
        with Database('sqlite',self.database) as db:
            self.assertTrue(db.rows('SELECT * FROM audit_events WHERE case_id=?',(case['case_id'],)))

    def test_summary_and_scenario_are_accessible(self):
        case=self.request('/api/cases')[0]
        result=self.request('/api/summary',{'case_id':case['case_id'],'provider':'offline'})
        self.assertEqual(result['provider'],'offline-template')
        preview=self.request('/api/scenario?kind=fraud&threshold=80')
        self.assertFalse(preview['changes_saved'])

    def test_export_allowlist_rejects_paths(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/download?name=../.env')
        self.assertEqual(error.exception.code,404)


if __name__ == '__main__':
    unittest.main()
