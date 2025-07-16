#!/usr/bin/env python3
"""
Micro-site: serves a QR code that links to a Gumroad product.
"""
from flask import Flask, send_file, request, jsonify
import qrcode, io, os

app = Flask(__name__)

@app.route("/")
def qr():
    url = "https://gum.co/tip-001"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/health")
def health():
    return "✅ Agent #001 alive", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)