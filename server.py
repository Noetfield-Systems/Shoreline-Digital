"""Shoreline independent local/persistent lead inbox. Python 3.11+, no third-party dependencies."""
import os, json, sqlite3, secrets, hmac, base64, html, time, re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from collections import defaultdict
from threading import Lock
ROOT=Path(__file__).resolve().parent; PUBLIC=ROOT/'public'; DB=Path(os.getenv('SHORELINE_DB',str(ROOT/'data'/'shoreline.sqlite3')))
STAGES=('new','contacted','qualified','proposal','accepted','deposit_verified','delivery','completed','lost')
CAMPAIGNS=('competition','visibility','automation','direct')
RATE=defaultdict(list); LOCK=Lock()
def db():
 DB.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS leads(id TEXT PRIMARY KEY,created TEXT DEFAULT CURRENT_TIMESTAMP,name TEXT NOT NULL,contact TEXT NOT NULL,service TEXT NOT NULL,details TEXT NOT NULL,language TEXT NOT NULL,campaign TEXT NOT NULL,source TEXT NOT NULL,status TEXT DEFAULT \'new\',owner TEXT DEFAULT \'unassigned\',next_action TEXT DEFAULT \'Review request\',next_date TEXT DEFAULT \'\',evidence TEXT DEFAULT \'\')'); c.commit(); return c

def clean(v,n): return str(v or '').strip()[:n]
def normalize(p):
 name=clean(p.get('name') or p.get('Name'),120); contact=clean(p.get('contact') or p.get('Email'),180); service=clean(p.get('service') or p.get('Service'),160); details=clean(p.get('details') or p.get('Details'),2400); language=clean(p.get('language') or p.get('Language'),60); campaign=clean(p.get('campaign'),30); source=clean(p.get('source'),100)
 if not name or not service or not contact or not details: raise ValueError('Name, contact, service and details are required.')
 if not (re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',contact) or re.fullmatch(r'[+\d\s().-]{7,30}',contact) and sum(x.isdigit() for x in contact)>=7): raise ValueError('Enter an email or phone number.')
 return name,contact,service,details,language,campaign if campaign in CAMPAIGNS else 'direct',source
class Handler(BaseHTTPRequestHandler):
 def send(self,status,body,ctype='application/json; charset=utf-8'):
  if isinstance(body,dict): body=json.dumps(body,ensure_ascii=False)
  if isinstance(body,str): body=body.encode()
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','strict-origin-when-cross-origin');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 def auth(self):
  token=os.getenv('SHORELINE_OPERATOR_PASSWORD',''); expected='Basic '+base64.b64encode(('operator:'+token).encode()).decode()
  if token and hmac.compare_digest(self.headers.get('Authorization',''),expected): return True
  self.send_response(401 if token else 503);self.send_header('WWW-Authenticate','Basic realm="Shoreline Operator"');self.send_header('Cache-Control','no-store');self.end_headers();return False
 def read_json(self):
  n=int(self.headers.get('Content-Length','0')); 
  if n<1 or n>16384: raise ValueError('Invalid request length')
  p=json.loads(self.rfile.read(n));
  if not isinstance(p,dict): raise ValueError('Invalid request')
  return p
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/health':
   with db() as c: c.execute('SELECT 1')
   return self.send(200,{'status':'ok','payment':'not_connected'})
  if path=='/operator':
   if not self.auth():return
   return self.send(200,(ROOT/'operator.html').read_bytes(),'text/html; charset=utf-8')
  if path=='/api/operator/leads':
   if not self.auth():return
   with db() as c: rows=[dict(r) for r in c.execute('SELECT * FROM leads ORDER BY created DESC')]
   return self.send(200,{'leads':rows})
  path='/digital.html' if path in ('/','/index.html') else path
  f=PUBLIC/path.lstrip('/')
  if f.parent!=PUBLIC or not f.is_file():return self.send(404,{'error':'Not found'})
  return self.send(200,f.read_bytes(),'text/html; charset=utf-8' if f.suffix=='.html' else 'text/plain; charset=utf-8')
 def do_POST(self):
  path=urlsplit(self.path).path
  if path=='/api/requests':
   with LOCK:
    ip=self.client_address[0]; now=time.monotonic(); RATE[ip]=[v for v in RATE[ip] if now-v<60];
    if len(RATE[ip])>=10:return self.send(429,{'error':'Try again later'})
    RATE[ip].append(now)
   try:
    p=self.read_json(); values=normalize(p)
   except (ValueError,TypeError):return self.send(400,{'error':'Invalid or incomplete contact information.'})
   receipt='SD-'+secrets.token_hex(8).upper()
   with db() as c: c.execute('INSERT INTO leads(id,name,contact,service,details,language,campaign,source) VALUES(?,?,?,?,?,?,?,?)',(receipt,*values))
   return self.send(201,{'receipt':receipt,'status':'received','booking_confirmed':False,'payment_received':False})
  if path=='/api/operator/update':
   if not self.auth():return
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
   try:
    p=self.read_json(); status=p.get('status'); evidence=clean(p.get('evidence'),2000)
    if status not in STAGES or status=='deposit_verified':raise ValueError()  # payment truth is derived from commerce receipts
    with db() as c:
     row=c.execute('UPDATE leads SET status=?,owner=?,next_action=?,next_date=?,evidence=? WHERE id=?',(status,clean(p.get('owner'),100),clean(p.get('next_action'),240),clean(p.get('next_date'),30),evidence,clean(p.get('id'),50)))
     if row.rowcount!=1:return self.send(404,{'error':'Unknown lead'})
    return self.send(200,{'status':'updated','payment_verification':'operator assertion only; not processor verified'})
   except (ValueError,TypeError):return self.send(400,{'error':'Invalid update'})
  return self.send(404,{'error':'Not found'})
if __name__=='__main__':
 with db():pass
 ThreadingHTTPServer((os.getenv('HOST','127.0.0.1'),int(os.getenv('PORT','8080'))),Handler).serve_forever()
