import unittest, json, tempfile, threading, os
from pathlib import Path
from html.parser import HTMLParser
import build_excellence_v10 as build
import intelligence, production, server, test_runtime
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set(); self.links=[]; self.campaign=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids,a['id'];self.ids.add(a['id'])
        if tag in ('a','script','link'):self.links.append(a.get('href',a.get('src','')))
        if tag=='input' and a.get('name')=='service':self.campaign=a.get('value','').split('|')[0]

class ExcellenceV10(unittest.TestCase):
    call=test_runtime.RuntimeTest.call
    tearDownClass=classmethod(test_runtime.RuntimeTest.tearDownClass.__func__)
    @classmethod
    def setUpClass(cls):
        for lang in ('en','fa'):build.gen(lang)
        server.RATE.clear();cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.sqlite'
        os.environ['SHORELINE_OPERATOR_PASSWORD']='test-only-password'
        os.environ.pop('SHORELINE_PUBLIC_URL',None)
        cls.s=production.BoundedHTTPServer(('127.0.0.1',0),intelligence.Handler)
        cls.base='http://127.0.0.1:'+str(cls.s.server_port)
        threading.Thread(target=cls.s.serve_forever,daemon=True).start()
    def test_all_generated_routes(self):
        names=[f'c{i:02d}' for i in range(1,9)]+[f'bi-{i:02d}' for i in range(1,13)]+[f'industry-{i:02d}' for i in range(1,13)]+['services','campaigns','bi','industry','offers','work','sample-research','sample-handover','about','privacy','competition','visibility','automation']
        for lang in ('en','fa'):
            for slug in names:
                path=f'/{slug}-{lang}.html';code,body=self.call(path);self.assertEqual(code,200,path)
                s=body.decode();self.assertIn(f'lang="{lang}"',s);self.assertIn('/excellence.css',s)
                p=Page();p.feed(s)
                if slug!='privacy':
                    self.assertIn('intake-form',p.ids);self.assertIn(p.campaign,server.CAMPAIGNS)
                for h in p.links:
                    if h.startswith('#'):self.assertIn(h[1:],p.ids,(path,h))
                    elif h.startswith('/') and h!='/':
                        target=h.split('#')[0]
                        if target!='/':self.assertTrue((build.PUBLIC/target.lstrip('/')).is_file(),(path,h))
        for path in ('/excellence.css','/excellence.js','/digital.html','/digital-fa.html'):
            self.assertEqual(self.call(path)[0],200)
    def test_intake_campaign_attribution(self):
        for i,s in enumerate(build.S):
            page=Page();page.feed(self.call(f'/c{i+1:02d}-en.html')[1].decode())
            self.assertEqual(page.campaign,s[0])
            code,b=self.call('/api/requests',dict(name='QA ONLY',contact='qa@example.com',service=s[1],details='Synthetic CI test',language='en',campaign=page.campaign,source='test'))
            self.assertEqual(code,201);self.assertFalse(json.loads(b)['payment_received'])
        with server.db() as c:
            self.assertEqual(c.execute('SELECT count(distinct campaign) FROM leads').fetchone()[0],8)
