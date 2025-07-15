#!/usr/bin/env python3
"""
commander.py  –  unbreakable swarm dashboard
"""
import json, os, time, threading, subprocess, requests, uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ROOT      = Path(__file__).parent
STATE_F   = ROOT / "forge_state.json"
LOG_F     = ROOT / "commander.log"

app = FastAPI(title="SwarmCommander")

# ---------- robust helpers ----------
def log(msg):
    with LOG_F.open("a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")

def safe_state():
    try:
        return json.loads(STATE_F.read_text()) if STATE_F.exists() else {"funnels": []}
    except json.JSONDecodeError:
        log("⚠️  Malformed JSON; resetting state")
        return {"funnels": []}

def health(url, timeout=3):
    try:
        return requests.get(url, timeout=timeout).ok
    except Exception as e:
        log(f"Health check failed {url}: {e}")
        return False

def redeploy(folder):
    try:
        log(f"Redeploying {folder}")
        subprocess.run("railway up", shell=True, cwd=folder, capture_output=True, check=True)
    except Exception as e:
        log(f"Redeploy error: {e}")

# ---------- watchdog ----------
def watchdog():
    while True:
        st = safe_state()
        for f in st.get("funnels", []):
            if not health(f["railway"]):
                redeploy(f["folder"])
        time.sleep(300)

threading.Thread(target=watchdog, daemon=True).start()

# ---------- web ui ----------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    st = safe_state()
    rows = "\n".join(
        f"<tr><td>{f.get('slug','?')}</td>"
        f"<td><a href='{f['railway']}'>Railway</a></td>"
        f"<td><a href='{f['gumroad']}'>Gumroad</a></td>"
        f"<td>{'🟢' if health(f['railway']) else '🔴'}</td></tr>"
        for f in st.get("funnels", [])
    )
    return f"""
    <html>
    <head><title>SwarmCommander</title></head>
    <body>
        <h1>🧬 Live Swarm</h1>
        <table border=1>
        <tr><th>Slug</th><th>Railway</th><th>Gumroad</th><th>Health</th></tr>
        {rows if rows else "<tr><td colspan=4>🌱 No funnels yet</td></tr>"}
        </table>
        <p>Logs: <a href="/logs">/logs</a></p>
    </body>
    </html>
    """

@app.get("/logs")
def logs():
    return HTMLResponse(f"<pre>{LOG_F.read_text() if LOG_F.exists() else 'No logs yet'}</pre>")

# ---------- startup ----------
if __name__ == "__main__":
    log("Commander started")
    uvicorn.run("commander:app", host="0.0.0.0", port=7777)