import os, tempfile, unittest, threading, json
from pathlib import Path
from unittest.mock import patch
import server, production, test_runtime
class LaunchV6(unittest.TestCase):
 call=test_runtime.RuntimeTest.call
 tearDownClass=classmethod(test_runtime.RuntimeTest.tearDownClass.__func__)
 @classmethod
 def setUpClass(cls):
  server.RATE.clear();cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.sqlite';os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password';cls.s=production.BoundedHTTPServer(('127.0.0.1',0),production.Handler);cls.base='http://127.0.0.1:'+str(cls.s.server_port);threading.Thread(target=cls.s.serve_forever,daemon=True).start()
 def test_home_and_assets(self):
  for p in ('/','/studio-en.html','/studio-fa.html','/studio.css','/studio.js','/offers-en.html','/offers-fa.html'):
   self.assertEqual(self.call(p)[0],200,p)
  self.assertIn(b'intake-form',self.call('/')[1]);self.assertIn(b'dir="rtl"',self.call('/studio-fa.html')[1]);self.assertEqual(self.call('/api/operator/leads')[0],401)
 def test_persisted_intake(self):
  status,body=self.call('/api/requests',{'name':'QA ONLY','contact':'qa@example.com','service':'Business launch','details':'Synthetic QA','campaign':'launch','source':'studio','language':'en'});self.assertEqual(status,201);receipt=json.loads(body)['receipt'];self.assertFalse(json.loads(body)['payment_received']);
  with server.db() as c:self.assertEqual(c.execute('select campaign from leads where id=?',(receipt,)).fetchone()[0],'launch')
if __name__=='__main__':unittest.main()
