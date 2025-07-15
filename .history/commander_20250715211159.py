#!/usr/bin/env python3
"""
commander.py
FastAPI dashboard + watchdog for the AI swarm
"""
import json, os, time, threading, subprocess, requests, uvicorn
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

STATE   = Path("forge_state.json")
BACKUPS = Path("backups") ; BACKUPS.mkdir(exist_ok=True)

app = FastAPI(title="SwarmCommander")

# ---------- helpers ----------
def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"funnels": []}

def save_state(data):
    STATE.write_text(json.dumps(data, indent=2))

def health(url, timeout=3):
    try:
        return requests.get(url, timeout=timeout).ok
    except:
        return False

def redeploy(folder):
    subprocess.run("railway up", shell=True, cwd=folder, capture_output=True)

# ---------- background watchdog ----------
def watchdog():
    while True:
        state = load_state()
        for f in state["funnels"]:
            if not health(f["railway"]):
                print(f"🔄 Reviving {f['slug']}")
                redeploy(f["folder"])
        time.sleep(300)   # every 5 min

threading.Thread(target=watchdog, daemon=True).start()

# ---------- web UI ----------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    st = load_state()
    rows = "\n".join(
        f"<tr><td>{f['slug']}</td><td><a href='{f['railway']}'>Railway</a></td>"
        f"<td><a href='{f['gumroad']}'>Gumroad</a></td>"
        f"<td>{'🟢' if health(f['railway']) else '🔴'}</td></tr>"
        for f in st["funnels"]
    )
    return f"""
    <html>
    <head><title>SwarmCommander</title></head>
    <body>
        <h1>🧬 Live Swarm</h1>
        <table border=1><tr><th>Slug</th><th>Railway</th><th>Gumroad</th><th>Health</th></tr>{rows}</table>
        <p>Auto-refresh every 5 min.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run("commander:app", host="0.0.0.0", port=7777)