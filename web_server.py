"""
Simple web server for Render.com
Keeps the service alive and provides health check endpoint
"""
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Firebase APK Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}

def run_web_server():
    """Run Flask server in background"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def start_web_server():
    """Start web server in a separate thread"""
    thread = threading.Thread(target=run_web_server, daemon=True)
    thread.start()
    print(f"✅ Web server started on port {os.environ.get('PORT', 10000)}")
