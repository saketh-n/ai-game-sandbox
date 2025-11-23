#!/usr/bin/env python3
"""
Simple HTTP server to run the game
This avoids CORS issues when loading local files
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8080

# Change to the directory containing this script
os.chdir(Path(__file__).parent)

Handler = http.server.SimpleHTTPRequestHandler

print("=" * 70)
print("🎮 Platformer Game")
print("=" * 70)
print(f"\n🌐 Starting server at http://localhost:{PORT}")
print(f"📁 Serving files from: {Path.cwd()}")
print(f"\n🎯 Opening game in your browser...")
print(f"\n⚠️  Press Ctrl+C to stop the server when you're done")
print("=" * 70 + "\n")

# Open browser after a short delay
import threading
def open_browser():
    import time
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}/game.html')

threading.Thread(target=open_browser, daemon=True).start()

# Start server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped. Thanks for playing!")
