"""Independent quote, acceptance, invoice and reconciliation ledger."""
import os, json, secrets, sqlite3, hashlib, datetime as dt, urllib.request, urllib.parse, urllib.error, re
import server as base
from urllib.parse import urlsplit, parse_qs

def db():
 c=base.db(); c.execute('PRAGMA foreign_keys=ON')
 c.executescript('''CREATE TABLE IF NOT EXISTS quotes(id TEXT PRIMARY KEY,lead_id TEXT NOT NULL REFERENCES leads(id),token TEXT UNIQUE NOT NULL,scope TEXT NOT NULL,deliverables TEXT NOT NULL,terms TEXT NOT NULL,language TEXT NOT NULL,total INTEGER NOT NULL,deposit INTEGER NOT NULL,expires TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP,accepted TEXT,accepted_by TEXT,accepted_hash TEXT);
 CREATE TABLE IF NOT EXISTS invoices(id TEXT PRIMARY KEY,quote_id TEXT NOT NULL REFERENCES quotes(id),kind TEXT NOT NULL,amount INTEGER NOT NULL,session_id TEXT UNIQUE,checkout_url TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(quote_id,kind));
 CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,invoice_id TEXT NOT NULL REFERENCES invoices(id),amount INTEGER NOT NULL,method TEXT NOT NULL,reference TEXT NOT NULL UNIQUE,evidence TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(invoice_id));
 CREATE TABLE IF NOT EXISTS opportunities(id TEXT PRIMARY KEY,company TEXT NOT NULL,industry TEXT NOT NULL,location TEXT NOT NULL,url TEXT NOT NULL,observation TEXT NOT NULL,evidence TEXT NOT NULL,service TEXT NOT NULL,contact TEXT NOT NULL,consent_basis TEXT NOT NULL,owner TEXT NOT NULL,next_action TEXT NOT NULL,next_date TEXT NOT NULL,status TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP);''');return c

def uid(prefix):return prefix+'-'+secrets.token_hex(9).upper()
def cents(v):
 if type(v) is not int or not 0<=v<=100000000:raise ValueError('Amount must be integer CAD cents')
 return v
def required(p,k,n=4000):
 v=base.clean(p.get(k),n)
 if not v:raise ValueError('Required: '+k)
 return v
def date(v):return dt.date.fromisoformat(v).isoformat()
def today():return dt.datetime.now(dt.timezone.utc).date().isoformat()
def snapshot(q):return {k:q[k] for k in ('id','scope','deliverables','terms','language','total','deposit','expires')}
def digest(q):return hashlib.sha256(json.dumps(snapshot(q),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def stripe_config():
 key=os.getenv('SHORELINE_STRIPE_KEY','');acct=os.getenv('SHORELINE_STRIPE_ACCOUNT','');origin=os.getenv('SHORELINE_PUBLIC_URL','').rstrip('/')
 if not key.startswith('sk_live_') or not acct.startswith('acct_') or not origin.startswith('https://'):raise ValueError('Authorized live Stripe account or public origin not configured')
 if acct!='acct_1SfSseJ03eJkL57J':raise ValueError('Merchant does not match authorized Noetfield account')
 if os.getenv('SHORELINE_TAX_MODE') not in ('stripe_automatic_exclusive','confirmed_no_collection'):raise ValueError('Merchant tax configuration not confirmed')
 if os.getenv('SHORELINE_TAX_MODE')=='stripe_automatic_exclusive' and not re.fullmatch(r'txcd_[0-9]+',os.getenv('SHORELINE_STRIPE_TAX_CODE','')):raise ValueError('Approved Stripe Tax product code required')
 return key,acct,origin

def stripe(path,params=None,idem=None):
 key,acct,_=stripe_config(); headers={'Authorization':'Bearer '+key};data=None
 if params is not None:data=urllib.parse.urlencode(params).encode()
 if idem:headers['Idempotency-Key']=idem
 try:
  with urllib.request.urlopen(urllib.request.Request('https://api.stripe.com/v1/'+path,data=data,headers=headers),timeout=15) as r:return json.load(r)
 except (urllib.error.URLError,TimeoutError):raise ValueError('Stripe request failed; no payment confirmed')
def account_check():
 _,acct,_=stripe_config()
 if stripe('account').get('id')!=acct:raise ValueError('Stripe account mismatch')
def quote_public(c,token):
 q=c.execute('SELECT * FROM quotes WHERE token=?',(token,)).fetchone()
 if not q:raise ValueError('Unknown quote')
 out=snapshot(q);out.update(accepted=q['accepted'],expired=q['expires']<today(),digest=digest(q));
 try:stripe_config();out['checkout_configured']=True
 except ValueError:out['checkout_configured']=False
 out['invoices']=[dict(r) for r in c.execute('SELECT i.id,i.kind,i.amount,CASE WHEN r.id IS NULL THEN 0 ELSE 1 END AS paid,r.method FROM invoices i LEFT JOIN receipts r ON i.id=r.invoice_id WHERE quote_id=? ORDER BY kind DESC',(q['id'],))];return q,out
class Handler(base.Handler):
 def log_message(self,fmt,*args):
  # Avoid exposing bearer proposal tokens in request logs.
  if args and isinstance(args[0],str):args=(re.sub(r"token=[^ &]+","token=[redacted]",args[0]),*args[1:])
  super().log_message(fmt,*args)
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/health':
   with db() as c:c.execute('SELECT 1')
   try:stripe_config();status='configured_not_verified'
   except ValueError:status='not_connected'
   return self.send(200,{'status':'ok','payment':status,'release':'3.0'})
  if path=='/commerce':
   if not self.auth():return
   return self.send(200,(base.ROOT/'commerce.html').read_bytes(),'text/html; charset=utf-8')
  if path=='/api/commerce':
   if not self.auth():return
   with db() as c:
    data={k:[dict(r) for r in c.execute('SELECT * FROM '+k+' ORDER BY created DESC')] for k in ('quotes','invoices','receipts','opportunities','leads')}
   return self.send(200,data)
  if path=='/api/quote':
   token=parse_qs(urlsplit(self.path).query).get('token',[''])[0]
   try:
    with db() as c:_,out=quote_public(c,token)
    return self.send(200,out)
   except ValueError:return self.send(404,{'error':'Unknown quote'})
  return super().do_GET()
 def do_POST(self):
  path=urlsplit(self.path).path
  if not path.startswith('/api/commerce/') and path not in ('/api/quote/accept','/api/quote/checkout'):return super().do_POST()
  if path.startswith('/api/commerce/') and not self.auth():return
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
  try:
   p=self.read_json()
   with db() as c:
    c.execute('BEGIN IMMEDIATE')
    if path=='/api/commerce/quote':
     lead=required(p,'lead_id',100);scope=required(p,'scope');deliver=required(p,'deliverables');terms=required(p,'terms');lang=required(p,'language',2);total=cents(p.get('total'));deposit=cents(p.get('deposit'));expiry=date(required(p,'expires',10))
     if lang not in ('en','fa') or not 0<total or deposit>total or expiry<today():raise ValueError('Invalid quote amounts, language or expiry')
     if not c.execute('SELECT 1 FROM leads WHERE id=?',(lead,)).fetchone():raise ValueError('Unknown lead')
     qid=uid('Q');token=secrets.token_urlsafe(32)
     c.execute('INSERT INTO quotes(id,lead_id,token,scope,deliverables,terms,language,total,deposit,expires) VALUES(?,?,?,?,?,?,?,?,?,?)',(qid,lead,token,scope,deliver,terms,lang,total,deposit,expiry));c.execute("UPDATE leads SET status='proposal',next_action='Share quote and follow up' WHERE id=?",(lead,));out={'id':qid,'url':'/quote.html#'+token}
    elif path=='/api/quote/accept':
     q,out=quote_public(c,required(p,'token',100));name=required(p,'name',120)
     if q['accepted']:return self.send(409,{'error':'Already accepted'})
     if out['expired'] or p.get('digest')!=out['digest'] or p.get('agree') is not True:raise ValueError('Quote expired or agreement missing')
     c.execute('UPDATE quotes SET accepted=CURRENT_TIMESTAMP,accepted_by=?,accepted_hash=? WHERE id=?',(name,out['digest'],q['id']))
     for kind,amount in [('deposit',q['deposit']),('balance',q['total']-q['deposit'])]:
      if amount:c.execute('INSERT INTO invoices(id,quote_id,kind,amount) VALUES(?,?,?,?)',(uid('INV'),q['id'],kind,amount))
     c.execute("UPDATE leads SET status='accepted',next_action='Arrange payment' WHERE id=?",(q['lead_id'],));out={'accepted':True,'quote_id':q['id']}
    elif path=='/api/quote/checkout':
     q,_=quote_public(c,required(p,'token',100));inv=c.execute('SELECT * FROM invoices WHERE id=? AND quote_id=?',(required(p,'invoice_id',100),q['id'])).fetchone()
     if not q['accepted'] or not inv or c.execute('SELECT 1 FROM receipts WHERE invoice_id=?',(inv['id'],)).fetchone():raise ValueError('Invoice not payable')
     account_check();_,_,origin=stripe_config()
     if inv['session_id']:
      s=stripe('checkout/sessions/'+inv['session_id'])
      if s.get('status')!='open' or not s.get('url'):raise ValueError('Existing checkout closed; operator must reconcile')
     else:
      tax_mode=os.getenv('SHORELINE_TAX_MODE');tax_fields={'line_items[0][price_data][product_data][tax_code]':os.environ['SHORELINE_STRIPE_TAX_CODE'],'billing_address_collection':'required'} if tax_mode=='stripe_automatic_exclusive' else {}
      s=stripe('checkout/sessions',{**tax_fields,'mode':'payment','line_items[0][price_data][currency]':'cad','line_items[0][price_data][product_data][name]':'Shoreline Digital '+inv['id'],'line_items[0][price_data][unit_amount]':inv['amount'],'line_items[0][quantity]':1,'metadata[invoice_id]':inv['id'],'metadata[venture]':'shoreline_digital','metadata[quote_id]':q['id'],'payment_intent_data[metadata][venture]':'shoreline_digital','payment_intent_data[metadata][invoice_id]':inv['id'],'line_items[0][price_data][tax_behavior]':'exclusive','automatic_tax[enabled]':str(os.getenv('SHORELINE_TAX_MODE')=='stripe_automatic_exclusive').lower(),'success_url':origin+'/quote.html#'+q['token'],'cancel_url':origin+'/quote.html#'+q['token']},'shoreline-'+inv['id']);c.execute('UPDATE invoices SET session_id=?,checkout_url=? WHERE id=?',(s['id'],s['url'],inv['id']))
     out={'url':s['url']}
    elif path in ('/api/commerce/reconcile','/api/commerce/manual'):
     inv=c.execute('SELECT * FROM invoices WHERE id=?',(required(p,'invoice_id',100),)).fetchone()
     if not inv:raise ValueError('Unknown invoice')
     if c.execute('SELECT 1 FROM receipts WHERE invoice_id=?',(inv['id'],)).fetchone():return self.send(409,{'error':'Already reconciled'})
     if path.endswith('reconcile'):
      if not inv['session_id']:raise ValueError('No Stripe checkout')
      account_check();s=stripe('checkout/sessions/'+inv['session_id'])
      if not(s.get('livemode') is True and s.get('payment_status')=='paid' and s.get('status')=='complete' and s.get('currency')=='cad' and s.get('amount_subtotal')==inv['amount'] and s.get('metadata',{}).get('invoice_id')==inv['id'] and s.get('metadata',{}).get('venture')=='shoreline_digital' and s.get('amount_total')==inv['amount']+s.get('total_details',{}).get('amount_tax',0)):raise ValueError('Payment not verified')
      method='stripe_live_verified';ref=s['id'];evidence=json.dumps({'verification':'Live Stripe API session verification','merchant':'NOETFIELD SYSTEMS INC.','venture':'shoreline_digital','gross_cents':s['amount_total'],'tax_cents':s.get('total_details',{}).get('amount_tax',0),'service_cents':inv['amount']})
     else:
      if inv['session_id']:raise ValueError('Reconcile existing Stripe checkout first')
      if cents(p.get('amount'))!=inv['amount'] or p.get('confirmed') is not True:raise ValueError('Exact amount and bank confirmation required')
      method='operator_bank_attestation';ref=required(p,'reference',180);evidence=required(p,'evidence')
     rid=uid('RCPT');c.execute('INSERT INTO receipts(id,invoice_id,amount,method,reference,evidence) VALUES(?,?,?,?,?,?)',(rid,inv['id'],inv['amount'],method,ref,evidence));out={'receipt':rid,'method':method}
    elif path=='/api/commerce/opportunity':
     keys=('company','industry','location','url','observation','evidence','service','contact','consent_basis','owner','next_action','next_date','status');v=[required(p,k,2000) for k in keys]
     if urlsplit(v[3]).scheme not in ('http','https') or not urlsplit(v[3]).netloc or v[-1] not in ('research','qualified','contacted','responded','lost') or v[-1]=='contacted' and v[8].lower()=='unknown':raise ValueError('Evidence URL, valid status and outreach basis required')
     date(v[-2]);oid=uid('OP');c.execute('INSERT INTO opportunities(id,'+','.join(keys)+') VALUES('+','.join('?' for _ in range(len(keys)+1))+')',(oid,*v));out={'id':oid}
    else:return self.send(404,{'error':'Not found'})
   return self.send(201,out)
  except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return self.send(400,{'error':str(e) if isinstance(e,ValueError) else 'Invalid or duplicate record'})
if __name__=='__main__':
 with db():pass
 base.ThreadingHTTPServer((os.getenv('HOST','127.0.0.1'),int(os.getenv('PORT','8080'))),Handler).serve_forever()
