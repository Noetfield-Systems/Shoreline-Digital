"""V4 authenticated acquisition evidence ledger, read-only seed research and revenue metrics."""
import os,json,csv,sqlite3,re,hashlib
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import commerce as com
import server as base
ROOT=Path(__file__).parent; MARKET=ROOT/'market'
CAMPAIGNS=json.loads((MARKET/'campaigns.json').read_text()); ALIASES={x['alias'] for x in CAMPAIGNS}; base.CAMPAIGNS=tuple(sorted(ALIASES|{'direct'}))
STAGES=('DRAFT','PUBLISHED','SENT','REPLIED','QUALIFIED','QUOTED','DELIVERED')
def db():
 c=com.db();c.executescript('''CREATE TABLE IF NOT EXISTS acquisition_events(id TEXT PRIMARY KEY,subject TEXT NOT NULL,campaign TEXT NOT NULL,channel TEXT NOT NULL,stage TEXT NOT NULL,evidence TEXT NOT NULL,consent_basis TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(subject,campaign,channel,stage,evidence)); CREATE TABLE IF NOT EXISTS campaign_costs(id TEXT PRIMARY KEY,campaign TEXT NOT NULL,channel TEXT NOT NULL,kind TEXT NOT NULL,cents INTEGER NOT NULL CHECK(cents>0),reference TEXT NOT NULL UNIQUE,evidence TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP);''');return c
def read_csv(name):
 with (MARKET/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def metrics(c):
 result=[]
 for campaign in sorted(ALIASES|{'direct'}):
  r={'campaign':campaign};r['requests']=c.execute('SELECT count(*) FROM leads WHERE campaign=?',(campaign,)).fetchone()[0]
  for stage in STAGES:r[stage.lower()]=c.execute('SELECT count(DISTINCT subject) FROM acquisition_events WHERE campaign=? AND stage=?',(campaign,stage)).fetchone()[0]
  r['quotes']=c.execute('SELECT count(*) FROM quotes q JOIN leads l ON l.id=q.lead_id WHERE l.campaign=?',(campaign,)).fetchone()[0]
  r['accepted_quotes']=c.execute('SELECT count(*) FROM quotes q JOIN leads l ON l.id=q.lead_id WHERE l.campaign=? AND q.accepted IS NOT NULL',(campaign,)).fetchone()[0]
  r['quoted_cents']=c.execute('SELECT coalesce(sum(q.total),0) FROM quotes q JOIN leads l ON l.id=q.lead_id WHERE l.campaign=?',(campaign,)).fetchone()[0]
  for method,field in [('stripe_live_verified','stripe_cents'),('operator_bank_attestation','bank_attested_cents')]:r[field]=c.execute('SELECT coalesce(sum(r.amount),0) FROM receipts r JOIN invoices i ON r.invoice_id=i.id JOIN quotes q ON q.id=i.quote_id JOIN leads l ON l.id=q.lead_id WHERE l.campaign=? AND r.method=?',(campaign,method)).fetchone()[0]
  r['processor_customers']=c.execute("SELECT count(DISTINCT l.id) FROM receipts r JOIN invoices i ON r.invoice_id=i.id JOIN quotes q ON q.id=i.quote_id JOIN leads l ON l.id=q.lead_id WHERE l.campaign=? AND r.method='stripe_live_verified'",(campaign,)).fetchone()[0]
  for kind in ('ad','delivery'):r[kind+'_cents']=c.execute('SELECT coalesce(sum(cents),0) FROM campaign_costs WHERE campaign=? AND kind=?',(campaign,kind)).fetchone()[0]
  r['stripe_roas']=round(r['stripe_cents']/r['ad_cents'],2) if r['ad_cents'] else None
  r['stripe_cac_cents']=round(r['ad_cents']/r['processor_customers']) if r['processor_customers'] else None
  r['cost_per_conversation_cents']=round(r['ad_cents']/r['replied']) if r['replied'] else None
  r['cost_per_qualified_cents']=round(r['ad_cents']/r['qualified']) if r['qualified'] else None
  r['recorded_contribution_cents']=r['stripe_cents']+r['bank_attested_cents']-r['ad_cents']-r['delivery_cents'];result.append(r)
 return result
class Handler(com.Handler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/health':
   with db() as c:c.execute('SELECT 1')
   try:com.stripe_config();payment='configured_not_verified'
   except ValueError:payment='not_connected'
   return self.send(200,{'status':'ok','release':'6.0','payment':payment})
  if path=='/growth' or path.startswith('/api/growth/'):
   if not self.auth():return
   if path=='/growth':return self.send(200,(ROOT/'growth.html').read_bytes(),'text/html; charset=utf-8')
   if path=='/api/growth/research':return self.send(200,{'signals':read_csv('buying_signals.csv'),'competitors':read_csv('competitors.csv'),'channels':read_csv('channels.csv'),'campaigns':CAMPAIGNS})
   if path=='/api/growth/metrics':
    with db() as c:return self.send(200,{'metrics':metrics(c),'events':[dict(x) for x in c.execute('SELECT * FROM acquisition_events ORDER BY created DESC')],'costs':[dict(x) for x in c.execute('SELECT * FROM campaign_costs ORDER BY created DESC')],'note':'Bank attestations separate; costs are operator-recorded. Research signals are not sales.'})
   return self.send(404,{'error':'Unknown path'})
  return super().do_GET()
 def do_POST(self):
  path=urlsplit(self.path).path
  if not path.startswith('/api/growth/'):return super().do_POST()
  if not self.auth():return
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
  try:
   p=self.read_json();camp=com.required(p,'campaign',40);channel=com.required(p,'channel',80);evidence=com.required(p,'evidence',2000)
   if camp not in ALIASES|{'direct'}:raise ValueError('Unknown campaign')
   with db() as c:
    if path=='/api/growth/event':
     subject=com.required(p,'subject',160);stage=com.required(p,'stage',20);consent=base.clean(p.get('consent_basis'),500)
     if stage not in STAGES:raise ValueError('Invalid stage; PAID derives from receipts only')
     if stage=='SENT' and (not consent or consent.lower() in ('unknown','not verified','n/a')):raise ValueError('Document lawful outreach basis before recording SENT')
     if stage!='DRAFT' and len(evidence)<10:raise ValueError('Provide actual evidence')
     uid=com.uid('EV');c.execute('INSERT INTO acquisition_events(id,subject,campaign,channel,stage,evidence,consent_basis) VALUES(?,?,?,?,?,?,?)',(uid,subject,camp,channel,stage,evidence,consent))
    elif path=='/api/growth/cost':
     kind=com.required(p,'kind',20);amount=com.cents(p.get('cents'));reference=com.required(p,'reference',180)
     if kind not in ('ad','delivery') or not amount:raise ValueError('Positive actual recorded cost required')
     uid=com.uid('COST');c.execute('INSERT INTO campaign_costs(id,campaign,channel,kind,cents,reference,evidence) VALUES(?,?,?,?,?,?,?)',(uid,camp,channel,kind,amount,reference,evidence))
    else:return self.send(404,{'error':'Unknown path'})
   return self.send(201,{'id':uid,'status':'operator_recorded'})
  except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return self.send(400,{'error':str(e) if isinstance(e,ValueError) else 'Invalid or duplicate record'})
if __name__=='__main__':
 with db():pass
 base.ThreadingHTTPServer((os.getenv('HOST','127.0.0.1'),int(os.getenv('PORT','8080'))),Handler).serve_forever()
