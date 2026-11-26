import unittest,json,datetime,threading,os,tempfile
from pathlib import Path
import server,commerce
import test_runtime
class CommerceTest(unittest.TestCase):
 call=test_runtime.RuntimeTest.call
 tearDownClass=classmethod(test_runtime.RuntimeTest.tearDownClass.__func__)
 @classmethod
 def setUpClass(cls):
  server.RATE.clear();cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.sqlite';os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password';os.environ.pop('SHORELINE_STRIPE_KEY',None);cls.s=server.ThreadingHTTPServer(('127.0.0.1',0),commerce.Handler);cls.base='http://127.0.0.1:'+str(cls.s.server_port);threading.Thread(target=cls.s.serve_forever,daemon=True).start()
 def test_quote_cash(self):
  def call(path,p=None,auth=False):
   c,b=self.call(path,p,auth);return c,json.loads(b) if b else {}
  c,l=call('/api/requests',dict(name='QA ONLY',contact='qa@example.com',service='Benchmark',details='Test isolated',language='en'));self.assertEqual(c,201)
  p=dict(lead_id=l['receipt'],scope='QA scope',deliverables='QA report',terms='Test only',language='en',total=39900,deposit=19900,expires=(datetime.date.today()+datetime.timedelta(days=5)).isoformat())
  self.assertEqual(call('/api/commerce/quote',p)[0],401);self.assertEqual(call('/api/commerce/quote',{**p,'deposit':40000},True)[0],400)
  c,q=call('/api/commerce/quote',p,True);self.assertEqual(c,201);token=q['url'].split('#')[1];c,q=call('/api/quote?token='+token);self.assertEqual(c,200);self.assertNotIn('lead_id',q);self.assertEqual(call('/api/quote?token=bad')[0],404)
  a=dict(token=token,name='QA',agree=True,digest=q['digest']);self.assertEqual(call('/api/quote/accept',{**a,'digest':'bad'})[0],400);self.assertEqual(call('/api/quote/accept',a)[0],201);self.assertEqual(call('/api/quote/accept',a)[0],409)
  c,q=call('/api/quote?token='+token);self.assertEqual(sum(i['amount'] for i in q['invoices']),39900);self.assertEqual(len(q['invoices']),2);i=q['invoices'][0]
  self.assertEqual(call('/api/quote/checkout',dict(token=token,invoice_id=i['id']))[0],400);self.assertEqual(call('/api/commerce/reconcile',dict(invoice_id=i['id']),True)[0],400)
  m=dict(invoice_id=i['id'],amount=i['amount'],reference='QA-REF',evidence='synthetic bank test',confirmed=True);self.assertEqual(call('/api/commerce/manual',{**m,'amount':1},True)[0],400);self.assertEqual(call('/api/commerce/manual',m,True)[0],201);self.assertEqual(call('/api/commerce/manual',m,True)[0],409)
  c,d=call('/api/commerce',auth=True);self.assertEqual(len(d['receipts']),1);self.assertEqual(d['receipts'][0]['method'],'operator_bank_attestation');self.assertEqual(call('/api/commerce')[0],401)
 def test_radar(self):
  p=dict(company='QA',industry='QA',location='QA',url='https://example.com',observation='QA',evidence='QA',service='QA',contact='QA',consent_basis='unknown',owner='QA',next_action='Research',next_date='2026-12-01',status='contacted')
  self.assertEqual(self.call('/api/commerce/opportunity',p,True)[0],400);self.assertEqual(self.call('/api/commerce/opportunity',{**p,'status':'research'},True)[0],201)
if __name__=='__main__':unittest.main(verbosity=2)
