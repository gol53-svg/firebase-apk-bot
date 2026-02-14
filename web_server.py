"""
Web server for Render.com
Keeps the service alive with HTTP endpoints
"""
from flask import Flask, jsonify
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Firebase APK Bot</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #1a1a2e; color: #eee; }
            h1 { color: #0f3460; }
            .status { color: #16c79a; font-size: 24px; }
        </style>
    </head>
    <body>
        <h1>🔥 Firebase APK Bot</h1>
        <p class="status">✅ Bot is Running!</p>
        <p>Status: Active</p>
        <p><a href="/health" style="color: #16c79a;">Health Check</a></p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot": "firebase-apk-bot",
        "service": "active",
        "features": ["extract", "inject"]
    })

@app.route('/ping')
def ping():
    return "pong"

def run_server():
    """Run Flask server"""
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

def start_web_server():
    """Start web server in background thread"""
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"✅ Web server started on port {os.environ.get('PORT', 10000)}")
