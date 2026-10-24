# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = []
# ///
"""Local-only preview and Sveltia server, with fixed SiteGround contact forwarding."""
import argparse,http.server,json,mimetypes,threading,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,unquote
SITE=Path(__file__).resolve().parents[1];ROOT=SITE/'.local';PUBLIC=SITE/'public'
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(PUBLIC),**kwargs)
    def do_GET(self):
        u=urlsplit(self.path);qs=parse_qs(u.query)
        compatibility=ROOT/'site/data/compatibility.json'
        if not compatibility.exists():compatibility=ROOT.parent/'data/compatibility.json'
        if compatibility.exists():
            for row in json.loads(compatibility.read_text(encoding='utf-8')):
                original=urlsplit(row['url'])
                if unquote(original.path or '/')!=unquote(u.path or '/') or original.query!=u.query:continue
                if row.get('redirects'):
                    hop=row['redirects'][0];target=urlsplit(hop['to'])
                    location=target.path+('?' + target.query if target.query else '')+('#'+target.fragment if target.fragment else '') if target.hostname=='draymanamer.com' else hop['to']
                    self.send_response(hop['status']);self.send_header('Location',location);self.end_headers();return
                if row.get('final_status')==404:self.send_error(404);return
                break
        return super().do_GET()
    def guess_type(self,path):
        if '/feed/' in str(path).replace('\\','/'):return 'application/rss+xml; charset=utf-8'
        return super().guess_type(path)
    def do_POST(self):
        if urlsplit(self.path).path!='/api/contact':self.send_error(404);return
        if self.headers.get('Origin') not in (None,'http://localhost:'+str(self.server.server_address[1]),'http://127.0.0.1:'+str(self.server.server_address[1])):self.send_error(403);return
        try:size=int(self.headers.get('Content-Length','0'))
        except ValueError:self.send_error(400);return
        if size<0:self.send_error(400);return
        if size>2*1024*1024:self.send_error(413);return
        request=urllib.request.Request('https://draymanamer.com/wp-json/contact-form-7/v1/contact-forms/32/feedback',data=self.rfile.read(size),headers={'Content-Type':self.headers.get('Content-Type','')},method='POST')
        try:
            with urllib.request.urlopen(request,timeout=25) as response:body=response.read();code=response.status
        except urllib.error.HTTPError as e:body=e.read();code=e.code
        except (urllib.error.URLError,OSError):body=b'{"message":"Delivery service unavailable. Please try again."}';code=502
        self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=1111);a=p.parse_args()
    if not (PUBLIC/'index.html').exists():raise SystemExit('Run scripts/build.py with uv first.')
    print('Local preview: http://localhost:'+str(a.port)+'/',flush=True);print('Local editor: http://localhost:'+str(a.port)+'/admin/',flush=True)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
if __name__=='__main__':main()
