"""Bounded origin server behind Railway's managed HTTPS proxy. Local smoke tests use temporary DBs."""
import os, socket, threading, re
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit
import server as base
import growth
class Handler(growth.Handler):
    def setup(self):
        self.request.settimeout(15)
        super().setup()
    def log_message(self, fmt, *args):
        # Never write request path, bearer quote token or customer contact to stdout.
        pass
    def do_POST(self):
        if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type','').split(';')[0].strip() != 'application/json':
            return self.send(415,{'error':'JSON requests only'})
        origin=self.headers.get('Origin')
        configured=os.getenv('SHORELINE_PUBLIC_URL','').rstrip('/')
        if origin and configured and origin!=configured:
            return self.send(403,{'error':'Cross-origin submission refused'})
        return super().do_POST()
class BoundedHTTPServer(ThreadingHTTPServer):
    daemon_threads=True
    request_queue_size=64
    slots=threading.BoundedSemaphore(24)
    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            try:request.sendall(b'HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            except OSError:pass
            self.shutdown_request(request);return
        try:super().process_request(request,client_address)
        except BaseException:self.slots.release();raise
    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.slots.release()
if __name__=='__main__':
    if os.getenv('RAILWAY_ENVIRONMENT_ID') and os.getenv('RAILWAY_VOLUME_MOUNT_PATH')!='/data':
        raise SystemExit('Persistent /data volume required before serving customer requests')
    if os.getenv('RAILWAY_ENVIRONMENT_ID') and len(os.getenv('SHORELINE_OPERATOR_PASSWORD',''))<20:
        raise SystemExit('Configure a unique operator password in the secret manager')
    with growth.db():pass
    BoundedHTTPServer((os.getenv('HOST','0.0.0.0'),int(os.getenv('PORT','8080'))),Handler).serve_forever()
