#!/usr/bin/env python3
"""Local dev server: build site, serve at http://localhost:5500,
and rebuild + auto-refresh the browser on any source change.

Usage: python scripts/dev.py
"""
import os, subprocess, sys

try:
    from livereload import Server
except ImportError:
    sys.exit("livereload required: pip install -r requirements-dev.txt")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = [sys.executable, os.path.join(ROOT, "scripts", "build_site.py")]

def rebuild():
    subprocess.run(BUILD, check=False)

rebuild()
server = Server()
server.watch(os.path.join(ROOT, "framework.yaml"), rebuild)
server.watch(os.path.join(ROOT, "songs/"), rebuild)
server.watch(os.path.join(ROOT, "scripts/build_site.py"), rebuild)
server.serve(root=os.path.join(ROOT, "site"), port=5500, open_url_delay=1)
