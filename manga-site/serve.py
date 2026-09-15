#!/usr/bin/env python3
"""Мини-сервер МангаЛайф: отдаёт сайт с запретом кэширования,
чтобы новые главы и правки были видны сразу."""
import os
import http.server
import socketserver

BASE = os.path.dirname(os.path.abspath(__file__))
PORT = 8000


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # тише в логах


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    os.chdir(BASE)
    with Server(("0.0.0.0", PORT), NoCacheHandler) as httpd:
        print(f"МангаЛайф: http://0.0.0.0:{PORT}")
        httpd.serve_forever()
