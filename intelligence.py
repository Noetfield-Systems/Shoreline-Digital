"""V7: evidence-first service delivery, client access, and durable operator inbox.
No synthetic observations, payments or notifications. Reuses V6 runtime and database.
"""
import os, hashlib, secrets, sqlite3, re
from urllib.parse import urlsplit
import production, growth, commerce, server
from contextlib import closing

def db():
    c=growth.db()
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript("""
    CREATE TABLE IF NOT EXISTS v7_projects(
      id TEXT PRIMARY KEY, quote_id TEXT NOT NULL UNIQUE REFERENCES quotes(id),
      title TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'planned',
      token_hash TEXT NOT NULL UNIQUE, created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS v7_milestones(
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES v7_projects(id),
      title TEXT NOT NULL, due_date TEXT NOT NULL, status TEXT NOT NULL,
      evidence TEXT NOT NULL DEFAULT '', created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS v7_findings(
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES v7_projects(id),
      source_url TEXT NOT NULL, observed_on TEXT NOT NULL, observation TEXT NOT NULL,
      interpretation TEXT NOT NULL, recommendation TEXT NOT NULL,
      confidence TEXT NOT NULL, shared INTEGER NOT NULL DEFAULT 0,
      created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS v7_inbox_ack(
      lead_id TEXT PRIMARY KEY REFERENCES leads(id), seen_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS v7_feedback(
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES v7_projects(id),
      message TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    return c

def need(p,k,n=1000): return commerce.required(p,k,n)
def hash_token(t): return hashlib.sha256(t.encode()).hexdigest()
def project_for_token(c,p):
    t=need(p,'token',128)
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}',t): raise ValueError('Unknown project')
    row=c.execute('SELECT id,title,status,created,quote_id FROM v7_projects WHERE token_hash=?',(hash_token(t),)).fetchone()
    if not row: raise ValueError('Unknown project')
    return row
def rows(c,sql,args=()): return [dict(r) for r in c.execute(sql,args)]
def project_exists(c,pid):
    if not c.execute('SELECT 1 FROM v7_projects WHERE id=?',(pid,)).fetchone(): raise ValueError('Unknown project')
def public_project(c,project):
    pid=project['id']
    return {'project':dict(project),'milestones':rows(c,'SELECT title,due_date,status,evidence FROM v7_milestones WHERE project_id=? ORDER BY due_date,created',(pid,)),
            'findings':rows(c,'SELECT source_url,observed_on,observation,interpretation,recommendation,confidence FROM v7_findings WHERE project_id=? AND shared=1 ORDER BY created',(pid,)),
            'invoices':rows(c,"SELECT i.kind,i.amount,CASE WHEN r.id IS NULL THEN 'unconfirmed' ELSE r.method END AS payment_status FROM invoices i LEFT JOIN receipts r ON r.invoice_id=i.id WHERE i.quote_id=?",(project['quote_id'],))}
class Handler(production.Handler):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/health':
            with closing(db()) as c: c.execute('SELECT 1')
            try: commerce.stripe_config(); payment='configured_not_verified'
            except ValueError: payment='not_connected'
            return self.send(200,{'status':'ok','release':'7.0','payment':payment,'delivery_workspace':'available'})
        if path=='/api/v7/operator':
            if not self.auth(): return
            with closing(db()) as c:
                return self.send(200,{'unread':rows(c,'SELECT l.id,l.name,l.service,l.created FROM leads l LEFT JOIN v7_inbox_ack a ON a.lead_id=l.id WHERE a.lead_id IS NULL ORDER BY l.created DESC LIMIT 100'),
                    'accepted_quotes':rows(c,'SELECT q.id,l.name,q.scope FROM quotes q JOIN leads l ON l.id=q.lead_id WHERE q.accepted IS NOT NULL AND NOT EXISTS (SELECT 1 FROM v7_projects p WHERE p.quote_id=q.id) ORDER BY q.created DESC'),
                    'projects':rows(c,'SELECT id,quote_id,title,owner,status,created FROM v7_projects ORDER BY created DESC'),
                    'milestones':rows(c,'SELECT * FROM v7_milestones ORDER BY due_date'),
                    'findings':rows(c,'SELECT * FROM v7_findings ORDER BY created DESC'),
                    'feedback':rows(c,'SELECT * FROM v7_feedback ORDER BY created DESC LIMIT 100')})
        return super().do_GET()
    def do_POST(self):
        path=urlsplit(self.path).path
        if not path.startswith('/api/v7/'): return super().do_POST()
        if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type','').split(';')[0].strip()!='application/json': return self.send(415,{'error':'JSON required'})
        origin=self.headers.get('Origin'); configured=os.getenv('SHORELINE_PUBLIC_URL','').rstrip('/')
        if origin and configured and origin!=configured: return self.send(403,{'error':'Cross-origin submission refused'})
        client=path in ('/api/v7/client','/api/v7/feedback')
        if not client and not self.auth(): return
        try:
            p=self.read_json()
            with closing(db()) as c, c:
                if client:
                    project=project_for_token(c,p)
                    if path.endswith('/client'): return self.send(200,public_project(c,project))
                    count=c.execute("SELECT count(*) FROM v7_feedback WHERE project_id=? AND created >= datetime('now','-1 hour')",(project['id'],)).fetchone()[0]
                    if count>=10:return self.send(429,{'error':'Try later'})
                    c.execute('INSERT INTO v7_feedback(id,project_id,message) VALUES(?,?,?)',(commerce.uid('FB'),project['id'],need(p,'message',2000)))
                    return self.send(201,{'status':'received'})
                c.execute('BEGIN IMMEDIATE')
                if path=='/api/v7/project':
                    q=need(p,'quote_id',100)
                    if not c.execute('SELECT 1 FROM quotes WHERE id=? AND accepted IS NOT NULL',(q,)).fetchone(): raise ValueError('Accepted quote required')
                    pid=commerce.uid('PRJ');token=secrets.token_urlsafe(32)
                    c.execute('INSERT INTO v7_projects(id,quote_id,title,owner,token_hash) VALUES(?,?,?,?,?)',(pid,q,need(p,'title',180),need(p,'owner',120),hash_token(token)))
                    result={'id':pid,'client_path':'/client-studio.html#'+token}
                elif path=='/api/v7/rotate':
                    pid=need(p,'project_id',100);project_exists(c,pid);token=secrets.token_urlsafe(32)
                    c.execute('UPDATE v7_projects SET token_hash=? WHERE id=?',(hash_token(token),pid))
                    result={'client_path':'/client-studio.html#'+token}
                elif path=='/api/v7/project-status':
                    pid=need(p,'project_id',100);project_exists(c,pid)
                    status=need(p,'status',30)
                    if status not in ('planned','active','review','delivered','support','paused'):raise ValueError('Invalid status')
                    if status=='delivered' and not c.execute("SELECT 1 FROM v7_milestones WHERE project_id=? AND status='complete' AND evidence<>''",(pid,)).fetchone():raise ValueError('Document delivery evidence first')
                    c.execute('UPDATE v7_projects SET status=? WHERE id=?',(status,pid));result={'status':status}
                elif path=='/api/v7/milestone':
                    pid=need(p,'project_id',100);project_exists(c,pid)
                    status=need(p,'status',30); evidence=server.clean(p.get('evidence'),2000)
                    if status not in ('planned','active','complete') or status=='complete' and not evidence:raise ValueError('Completed milestones require evidence')
                    mid=server.clean(p.get('id'),100) or commerce.uid('MS')
                    v=(need(p,'title',180),commerce.date(need(p,'due_date',10)),status,evidence)
                    if p.get('id'):
                        if c.execute('UPDATE v7_milestones SET title=?,due_date=?,status=?,evidence=? WHERE id=? AND project_id=?',(*v,mid,pid)).rowcount!=1:raise ValueError('Unknown milestone')
                    else:c.execute('INSERT INTO v7_milestones(id,project_id,title,due_date,status,evidence) VALUES(?,?,?,?,?,?)',(mid,pid,*v))
                    result={'id':mid}
                elif path=='/api/v7/finding':
                    pid=need(p,'project_id',100);project_exists(c,pid);url=need(p,'source_url',1000);u=urlsplit(url)
                    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:raise ValueError('Public evidence URL required')
                    observed=commerce.date(need(p,'observed_on',10))
                    if observed>commerce.today():raise ValueError('Future observation not allowed')
                    confidence=need(p,'confidence',20)
                    if confidence not in ('low','medium','high'):raise ValueError('Choose confidence')
                    fid=commerce.uid('FIND')
                    c.execute('INSERT INTO v7_findings(id,project_id,source_url,observed_on,observation,interpretation,recommendation,confidence,shared) VALUES(?,?,?,?,?,?,?,?,?)',(fid,pid,url,observed,need(p,'observation',2000),need(p,'interpretation',2000),need(p,'recommendation',2000),confidence,int(p.get('shared') is True)))
                    result={'id':fid}
                elif path=='/api/v7/finding-share':
                    if c.execute('UPDATE v7_findings SET shared=? WHERE id=?',(int(p.get('shared') is True),need(p,'id',100))).rowcount!=1:raise ValueError('Unknown finding')
                    result={'status':'updated'}
                elif path=='/api/v7/ack':
                    lid=need(p,'lead_id',100)
                    if not c.execute('SELECT 1 FROM leads WHERE id=?',(lid,)).fetchone():raise ValueError('Unknown request')
                    c.execute('INSERT OR IGNORE INTO v7_inbox_ack(lead_id) VALUES(?)',(lid,));result={'status':'seen'}
                else:return self.send(404,{'error':'Not found'})
            return self.send(201,result)
        except (ValueError,TypeError,KeyError,sqlite3.IntegrityError,OverflowError) as e:
            return self.send(400,{'error':str(e) if isinstance(e,ValueError) else 'Invalid or duplicate record'})
if __name__=='__main__':
    if os.getenv('RAILWAY_ENVIRONMENT_ID') and os.getenv('RAILWAY_VOLUME_MOUNT_PATH')!='/data':raise SystemExit('Persistent /data volume required')
    if os.getenv('RAILWAY_ENVIRONMENT_ID') and len(os.getenv('SHORELINE_OPERATOR_PASSWORD',''))<20:raise SystemExit('Unique operator password required')
    with closing(db()):pass
    production.BoundedHTTPServer((os.getenv('HOST','0.0.0.0'),int(os.getenv('PORT','8080'))),Handler).serve_forever()
