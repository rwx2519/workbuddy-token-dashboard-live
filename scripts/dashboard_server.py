# -*- coding: utf-8 -*-
"""Token 看板固定端口服务器：http://127.0.0.1:8619/  ->  token-dashboard.html
供任务栏图标（Edge app 模式）访问；live.json 同源可拉，秒表正常。Ctrl+C 停止。"""
import http.server, socketserver, os, functools

DIR = r"C:\Users\MR.SHI\WorkBuddy\2026-09-18-21-33-18"
PORT = 8619

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/token-dashboard.html"
        super().do_GET()

class TSrv(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

with TSrv(("0.0.0.0", PORT), Handler) as httpd:
    print(f"serving {DIR} at http://127.0.0.1:{PORT}/", flush=True)
    httpd.serve_forever()
