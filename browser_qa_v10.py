"""Real Chromium layout and intake checks, isolated temporary database."""
import os, socket, subprocess, sys, tempfile, time, urllib.request, json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
def run():
    subprocess.run([sys.executable,'build_excellence_v10.py'],check=True)
    out=ROOT/'browser-receipts';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env=dict(os.environ,HOST='127.0.0.1',PORT=str(port),SHORELINE_DB=str(Path(tmp)/'qa.sqlite'),SHORELINE_OPERATOR_PASSWORD='browser-test-only')
        for k in ('SHORELINE_PUBLIC_URL','RAILWAY_ENVIRONMENT_ID','SHORELINE_STRIPE_KEY'):env.pop(k,None)
        proc=subprocess.Popen([sys.executable,'intelligence.py'],env=env,cwd=ROOT)
        origin=f'http://127.0.0.1:{port}'
        try:
            for _ in range(60):
                try:
                    with urllib.request.urlopen(origin+'/health',timeout=1):break
                except OSError:time.sleep(.25)
            else:raise RuntimeError('Server did not start')
            receipts=[]
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True)
                paths=['/','/studio-fa.html','/services-en.html','/services-fa.html','/c01-en.html','/c04-fa.html','/industry-03-en.html','/industry-04-fa.html','/sample-research-en.html','/sample-handover-fa.html','/offers-en.html','/privacy-fa.html']
                for width,height in [(390,844),(768,1024),(1440,900)]:
                    context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                    # External fonts are nonessential to this structural QA; avoid blocking on network.
                    context.route('https://**/*',lambda route:route.abort())
                    page=context.new_page()
                    errors=[]
                    page.on('pageerror',lambda err:errors.append(str(err)))
                    for path in paths:
                        errors.clear()
                        response=page.goto(origin+path,wait_until='domcontentloaded')
                        assert response and response.status==200,(path,width)
                        page.locator('h1').first.wait_for(state='visible')
                        assert not errors,(path,width,errors)
                        overflow=page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
                        assert overflow<=2,(path,width,overflow)
                        if width==390:
                            page.locator('#menu').click()
                            assert page.locator('#mobilelinks').is_visible(),path
                            page.locator('#menu').click()
                            assert not page.locator('#mobilelinks').is_visible(),path
                        if path in ('/','/studio-fa.html','/c01-en.html','/c04-fa.html'):
                            page.screenshot(path=str(out/f'{path.strip("/").replace(".html","") or "home"}-{width}.png'),full_page=True)
                        receipts.append({'path':path,'width':width,'overflow_px':overflow,'status':response.status})
                    context.close()
                page=browser.new_page(viewport={'width':390,'height':844})
                for lang,path in [('en','/c01-en.html'),('fa','/c04-fa.html')]:
                    page.goto(origin+path,wait_until='domcontentloaded')
                    page.locator('input[name=name]').fill('QA synthetic')
                    page.locator('input[name=contact]').fill('qa@example.com')
                    page.locator('textarea[name=details]').fill('Isolated browser verification only')
                    with page.expect_response(lambda r:r.url.endswith('/api/requests') and r.request.method=='POST') as rr:
                        page.locator('#submit').click()
                    response=rr.value;data=response.json()
                    assert response.status==201 and data['receipt'] and not data['payment_received'],data
                    page.locator('#request-status').wait_for(state='visible')
                    assert data['receipt'] in page.locator('#request-status').inner_text()
                    receipts.append({'lang':lang,'synthetic_receipt':data['receipt'],'payment_received':False})
                browser.close()
            (out/'results.json').write_text(json.dumps(receipts,indent=2))
            print(f'PASS: {len(paths)*3} browser route/viewport checks and 2 isolated inquiry submissions')
        finally:
            proc.terminate();proc.wait(timeout=10)
if __name__=='__main__':run()
