import unittest,json,threading,os,tempfile,datetime
from pathlib import Path
import server,growth,test_runtime
class GrowthTest(unittest.TestCase):
 call=test_runtime.RuntimeTest.call
 tearDownClass=classmethod(test_runtime.RuntimeTest.tearDownClass.__func__)
 @classmethod
 def setUpClass(cls):
  server.RATE.clear();cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.sqlite';os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password';cls.s=server.ThreadingHTTPServer(('127.0.0.1',0),growth.Handler);cls.base='http://127.0.0.1:'+str(cls.s.server_port);threading.Thread(target=cls.s.serve_forever,daemon=True).start()
 def test_growth_pipeline(self):
  def call(path,p=None,auth=False):
   c,b=self.call(path,p,auth);return c,json.loads(b) if b else {}
  self.assertEqual(call('/api/growth/research')[0],401);c,r=call('/api/growth/research',auth=True);self.assertEqual(c,200);self.assertEqual((len(r['signals']),len(r['competitors']),len(r['channels']),len(r['campaigns'])),(50,30,10,8));self.assertTrue(all(x['status']=='RESEARCH' for x in r['signals']))
  for campaign in r['campaigns']:
   for lang in ('en','fa'):self.assertEqual(self.call(campaign[lang]['landing'])[0],200)
   c,l=call('/api/requests',dict(name='QA ONLY',contact='qa@example.com',service='QA',details='Synthetic QA',language='en',campaign=campaign['alias'],source='test'));self.assertEqual(c,201);self.assertFalse(l['payment_received'])
  for path in (Path(__file__).parent/'public').glob('*.html'):self.assertEqual(self.call('/'+path.name)[0],200)
  c,m=call('/api/growth/metrics',auth=True);self.assertEqual(sum(x['requests'] for x in m['metrics']),8);self.assertEqual(sum(x['stripe_cents']+x['bank_attested_cents'] for x in m['metrics']),0)
  ev=dict(subject='QA ONLY',campaign='competition',channel='test',stage='SENT',evidence='synthetic QA evidence',consent_basis='unknown');self.assertEqual(call('/api/growth/event',ev,True)[0],400);self.assertEqual(call('/api/growth/event',{**ev,'stage':'PAID'},True)[0],400);self.assertEqual(call('/api/growth/event',{**ev,'stage':'DRAFT'},True)[0],201);self.assertEqual(call('/api/growth/event',{**ev,'stage':'DRAFT'},True)[0],400)
  cost=dict(campaign='competition',channel='test',kind='ad',cents=1000,reference='QA ONLY',evidence='synthetic test only');self.assertEqual(call('/api/growth/cost',{**cost,'cents':0},True)[0],400);self.assertEqual(call('/api/growth/cost',cost,True)[0],201);self.assertEqual(call('/api/growth/cost',cost,True)[0],400);c,m=call('/api/growth/metrics',auth=True);self.assertEqual(sum(x['ad_cents'] for x in m['metrics']),1000);self.assertEqual(sum(x['stripe_cents'] for x in m['metrics']),0)
  self.assertEqual(self.call('/growth',auth=True)[0],200);self.assertEqual(self.call('/growth')[0],401)
if __name__=='__main__':unittest.main(verbosity=2)
