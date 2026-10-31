"""Local HTTP server for read-only, synthetic MedTech portfolio demos."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
from urllib.parse import urlparse
from .medtech_service_desk.logic import dashboard as dispatch
from .healthcare_data_quality.logic import dashboard as laboratory
from .technical_presales_crm.logic import dashboard as presales

WEB=Path(__file__).parent/"web"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(WEB),**kwargs)
    def do_GET(self):
        name=urlparse(self.path).path
        choices={"/api/dispatch":dispatch,"/api/lab":laboratory,"/api/presales":presales}
        if name not in choices:
            return super().do_GET()
        content=json.dumps(choices[name]()).encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__=="__main__":
    port=int(os.getenv("PORT","8765"))
    print(f"Local synthetic demo at http://127.0.0.1:{port}/showcase.html")
    ThreadingHTTPServer(("127.0.0.1",port),Handler).serve_forever()
