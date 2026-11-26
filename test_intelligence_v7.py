import os, tempfile, threading, unittest, json, datetime
from pathlib import Path
import server, intelligence, production, test_runtime

class IntelligenceV7(unittest.TestCase):
    call=test_runtime.RuntimeTest.call
    tearDownClass=classmethod(test_runtime.RuntimeTest.tearDownClass.__func__)
    @classmethod
    def setUpClass(cls):
        server.RATE.clear()
        cls.tmp=tempfile.TemporaryDirectory()
        server.DB=Path(cls.tmp.name)/'test.sqlite'
        os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password'
        os.environ.pop('SHORELINE_STRIPE_KEY',None)
        os.environ.pop('SHORELINE_PUBLIC_URL',None)
        cls.s=production.BoundedHTTPServer(('127.0.0.1',0),intelligence.Handler)
        cls.base='http://127.0.0.1:'+str(cls.s.server_port)
        threading.Thread(target=cls.s.serve_forever,daemon=True).start()

    def test_pages(self):
        for path in ('/','/studio-fa.html','/assessment-en.html','/assessment-fa.html','/client-studio.html','/v7.css'):
            self.assertEqual(self.call(path)[0],200,path)
        self.assertEqual(self.call('/delivery-studio.html')[0],401)
        self.assertEqual(self.call('/delivery-studio.html',auth=True)[0],200)
        self.assertIn(b'dir="rtl"',self.call('/assessment-fa.html')[1])
        self.assertEqual(json.loads(self.call('/health')[1])['release'],'7.0')

    def test_full_delivery(self):
        def call(path,p=None,auth=False):
            code,body=self.call(path,p,auth)
            return code,json.loads(body) if body else {}
        self.assertEqual(call('/api/v7/operator')[0],401)
        self.assertEqual(call('/api/v7/project',{})[0],401)
        self.assertEqual(call('/api/v7/client',{'token':'a'*43})[0],400)
        code,l=call('/api/requests',dict(name='QA ONLY',contact='qa@example.com',service='Assessment',details='Synthetic test',language='en',campaign='competition',source='assessment'))
        self.assertEqual(code,201)
        lid=l['receipt']
        self.assertTrue(any(x['id']==lid for x in call('/api/v7/operator',auth=True)[1]['unread']))
        self.assertEqual(call('/api/v7/ack',{'lead_id':lid},True)[0],201)
        self.assertFalse(any(x['id']==lid for x in call('/api/v7/operator',auth=True)[1]['unread']))
        def quote():
            c,q=call('/api/commerce/quote',dict(lead_id=lid,scope='QA scope',deliverables='QA report',terms='QA terms',language='en',total=29900,deposit=10000,expires=(datetime.date.today()+datetime.timedelta(days=3)).isoformat()),True)
            self.assertEqual(c,201)
            token=q['url'].split('#')[1]
            return q['id'],token
        def accept(qtoken):
            q=call('/api/quote?token='+qtoken)[1]
            self.assertEqual(call('/api/quote/accept',dict(token=qtoken,name='QA',agree=True,digest=q['digest']))[0],201)
        qid,qt=quote()
        p={'quote_id':qid,'title':'QA project','owner':'QA'}
        self.assertEqual(call('/api/v7/project',p,True)[0],400)
        accept(qt)
        code,j=call('/api/v7/project',p,True)
        self.assertEqual(code,201)
        pid=j['id'];token=j['client_path'].split('#')[1]
        self.assertEqual(call('/api/v7/project',p,True)[0],400)
        otherq,otherqt=quote();accept(otherqt)
        code,other=call('/api/v7/project',{**p,'quote_id':otherq,'title':'Other QA'},True)
        self.assertEqual(code,201)
        other_token=other['client_path'].split('#')[1]
        self.assertEqual(call('/api/v7/project-status',{'project_id':pid,'status':'delivered'},True)[0],400)
        m={'project_id':pid,'title':'Research','due_date':'2030-01-01','status':'complete'}
        self.assertEqual(call('/api/v7/milestone',m,True)[0],400)
        code,ms=call('/api/v7/milestone',{**m,'evidence':'Synthetic receipt'},True);self.assertEqual(code,201)
        code,second=call('/api/v7/milestone',{**m,'title':'QA delivery','status':'planned'},True);self.assertEqual(code,201)
        self.assertEqual(call('/api/v7/project-status',{'project_id':pid,'status':'delivered'},True)[0],400)
        self.assertEqual(call('/api/v7/milestone',{**m,'id':second['id'],'title':'QA delivery','evidence':'Synthetic acceptance'},True)[0],201)
        f={'project_id':pid,'source_url':'https://example.com','observed_on':datetime.date.today().isoformat(),'observation':'QA observation','interpretation':'QA interpretation','recommendation':'QA recommendation','confidence':'medium'}
        self.assertEqual(call('/api/v7/finding',{**f,'source_url':'javascript:alert(1)'},True)[0],400)
        code,private=call('/api/v7/finding',f,True);self.assertEqual(code,201)
        code,shared=call('/api/v7/finding',{**f,'shared':True},True);self.assertEqual(code,201)
        c,view=call('/api/v7/client',{'token':token});self.assertEqual(c,200)
        self.assertEqual(len(view['findings']),1);self.assertEqual(len(view['milestones']),2)
        self.assertTrue(all(i['payment_status']=='unconfirmed' for i in view['invoices']))
        self.assertNotIn('token_hash',str(view))
        self.assertEqual(call('/api/v7/client',{'token':other_token})[1]['findings'],[])
        self.assertEqual(call('/api/v7/finding-share',{'id':private['id'],'shared':True},True)[0],201)
        self.assertEqual(len(call('/api/v7/client',{'token':token})[1]['findings']),2)
        self.assertEqual(call('/api/v7/feedback',{'token':token,'message':'QA feedback'})[0],201)
        self.assertTrue(any(x['project_id']==pid for x in call('/api/v7/operator',auth=True)[1]['feedback']))
        self.assertEqual(call('/api/v7/project-status',{'project_id':pid,'status':'delivered'},True)[0],201)
        code,rot=call('/api/v7/rotate',{'project_id':pid},True);self.assertEqual(code,201)
        self.assertEqual(call('/api/v7/client',{'token':token})[0],400)
        self.assertEqual(call('/api/v7/client',{'token':rot['client_path'].split('#')[1]})[0],200)
