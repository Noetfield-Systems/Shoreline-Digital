import unittest,os,json,threading,tempfile,datetime
from unittest.mock import patch
from pathlib import Path
import server,commerce,growth,test_runtime
class RevenueV5(unittest.TestCase):
 call=test_runtime.RuntimeTest.call
 tearDownClass=classmethod(test_runtime.RuntimeTest.tearDownClass.__func__)
 @classmethod
 def setUpClass(cls):
  server.RATE.clear();cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.sqlite';os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password';cls.s=server.ThreadingHTTPServer(('127.0.0.1',0),growth.Handler);cls.base='http://127.0.0.1:'+str(cls.s.server_port);threading.Thread(target=cls.s.serve_forever,daemon=True).start()
 def test_offer_pages(self):
  offers=json.loads((Path(__file__).parent/'market/launch_offers.json').read_text());self.assertEqual(len(offers),4)
  for lang in ('en','fa'):
   status,body=self.call('/offers-'+lang+'.html');self.assertEqual(status,200);self.assertIn(b'Noetfield Systems Inc.',body)
  for o in offers:
   code,b=self.call('/api/requests',{'name':'QA ONLY','contact':'qa@example.com','service':o['id'],'details':'QA only','campaign':o['campaign'],'source':'offers'});self.assertEqual(code,201);self.assertFalse(json.loads(b)['payment_received'])
 def test_merchant_config(self):
  cfg={'SHORELINE_STRIPE_KEY':'sk_live_QA_NOT_A_REAL_KEY','SHORELINE_STRIPE_ACCOUNT':'acct_1SfSseJ03eJkL57J','SHORELINE_PUBLIC_URL':'https://example.com','SHORELINE_TAX_MODE':''}
  with patch.dict(os.environ,cfg):
   with self.assertRaises(ValueError):commerce.stripe_config()
   with patch.dict(os.environ,{'SHORELINE_TAX_MODE':'stripe_automatic_exclusive','SHORELINE_STRIPE_TAX_CODE':''}):
    with self.assertRaises(ValueError):commerce.stripe_config()
   with patch.dict(os.environ,{'SHORELINE_TAX_MODE':'confirmed_no_collection'}):
    self.assertEqual(commerce.stripe_config()[1],cfg['SHORELINE_STRIPE_ACCOUNT'])
    with patch.object(commerce,'stripe',return_value={'id':'acct_WRONG'}):
     with self.assertRaises(ValueError):commerce.account_check()
    with patch.object(commerce,'stripe',return_value={'id':cfg['SHORELINE_STRIPE_ACCOUNT']}):commerce.account_check()
 def test_deposit_status_cannot_be_fabricated(self):
  c,b=self.call('/api/requests',dict(name='QA',contact='qa@example.com',service='QA',details='QA'));self.assertEqual(c,201)
  self.assertEqual(self.call('/api/operator/update',dict(id=json.loads(b)['receipt'],status='deposit_verified',evidence='fabricated assertion'),True)[0],400)
if __name__=='__main__':unittest.main()
