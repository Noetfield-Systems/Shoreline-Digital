import os,tempfile,threading,unittest,json,base64,urllib.request,urllib.error
from pathlib import Path
import server
class RuntimeTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  server.RATE.clear();cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.sqlite';os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password';cls.s=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.base='http://127.0.0.1:'+str(cls.s.server_port);threading.Thread(target=cls.s.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.s.shutdown();cls.s.server_close();cls.tmp.cleanup()
 def call(self,path,payload=None,auth=False):
  headers={};body=None
  if payload is not None:headers['Content-Type']='application/json';body=json.dumps(payload).encode()
  if auth:headers['Authorization']='Basic '+base64.b64encode(b'operator:test-only-password').decode()
  try:r=urllib.request.urlopen(urllib.request.Request(self.base+path,data=body,headers=headers))
  except urllib.error.HTTPError as e:r=e
  return r.status,r.read()
 def test_full_flow(self):
  self.assertEqual(self.call('/health')[0],200)
  for key in ('competition','visibility','automation'):
   for lang in ('en','fa'):self.assertEqual(self.call('/'+key+'-'+lang+'.html')[0],200)
  for p in ('/','/digital-fa.html'):self.assertEqual(self.call(p)[0],200)
  self.assertEqual(self.call('/api/operator/leads')[0],401)
  self.assertEqual(self.call('/api/requests',{'name':'test'})[0],400)
  for lang in ('en','fa'):
   code,body=self.call('/api/requests',dict(name='TEST ONLY',contact='test@example.com',service='Review',details='Synthetic QA',language=lang,campaign='competition',source='test'))
   self.assertEqual(code,201);j=json.loads(body);self.assertFalse(j['payment_received']);self.assertFalse(j['booking_confirmed']);receipt=j['receipt']
  code,body=self.call('/api/operator/leads',auth=True);self.assertEqual(code,200);self.assertEqual(len(json.loads(body)['leads']),2)
  self.assertEqual(self.call('/api/operator/update',dict(id=receipt,status='deposit_verified'),True)[0],400)
  self.assertEqual(self.call('/api/operator/update',dict(id=receipt,status='qualified',owner='test',next_action='Call',next_date='2026-11-26'),True)[0],200)
  self.assertEqual(self.call('/operator',auth=True)[0],200)
  with server.db() as c:self.assertEqual(c.execute('SELECT status FROM leads WHERE id=?',(receipt,)).fetchone()[0],'qualified')
if __name__=='__main__':unittest.main(verbosity=2)
