#!/usr/bin/env python3
"""
NightFlow — Development Server Launcher
Starts the Flask API backend + serves the frontend via Python HTTP server
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ── Paths ──────────────────────────────────────────────────────
ROOT     = os.path.dirname(os.path.abspath(__file__))
BACKEND  = os.path.join(ROOT, 'backend')
FRONTEND = os.path.join(ROOT, 'frontend')

BACKEND_PORT  = 5000
FRONTEND_PORT = 3000

class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress access logs

def serve_frontend():
    os.chdir(FRONTEND)
    server = HTTPServer(('0.0.0.0', FRONTEND_PORT), SilentHandler)
    print(f"  [Frontend] Serving on http://localhost:{FRONTEND_PORT}")
    server.serve_forever()

def start_backend():
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=BACKEND, env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc

def main():
    print()
    print("  ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗███████╗██╗      ██████╗ ██╗    ██╗")
    print("  ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝██╔════╝██║     ██╔═══██╗██║    ██║")
    print("  ██╔██╗ ██║██║██║  ███╗███████║   ██║   █████╗  ██║     ██║   ██║██║ █╗ ██║")
    print("  ██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██╔══╝  ██║     ██║   ██║██║███╗██║")
    print("  ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║     ███████╗╚██████╔╝╚███╔███╔╝")
    print("  ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝")
    print()
    print("  Nightlife Operating System — Rethymno, Crete")
    print("  ─────────────────────────────────────────────────────")
    print()

    # Start backend
    print("  Starting services...")
    backend_proc = start_backend()
    time.sleep(1.5)
    print(f"  [Backend]  Flask API running on http://localhost:{BACKEND_PORT}")

    # Start frontend in thread
    frontend_thread = threading.Thread(target=serve_frontend, daemon=True)
    frontend_thread.start()
    time.sleep(0.5)

    print()
    print("  ─────────────────────────────────────────────────────")
    print(f"  🌙 App ready at:    http://localhost:{FRONTEND_PORT}")
    print(f"  🔧 API ready at:    http://localhost:{BACKEND_PORT}")
    print()
    print("  Press Ctrl+C to stop.")
    print("  ─────────────────────────────────────────────────────")
    print()

    # Open browser
    time.sleep(0.5)
    try:
        webbrowser.open(f'http://localhost:{FRONTEND_PORT}/auth.html')
    except Exception:
        pass

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n  Shutting down NightFlow...")
        backend_proc.terminate()
        print("  Goodbye 🌙")

if __name__ == '__main__':
    main()
