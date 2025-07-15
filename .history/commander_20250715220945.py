#!/usr/bin/env python3
"""
commander.py  –  live swarm dashboard
"""
import json, os, time, threading, pathlib, httpx
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

ROOT      = Path(__file__).parent
STATE_F   = ROOT / "forge_state.json"
LOG_F     = ROOT / "commander.log"
GUM_TOKEN = os.getenv("GUMROAD_TOKEN")

def log(msg):
    LOG_F.open("a").write(f"{time.strftime('%H:%M:%S')} {msg}\n")

def safe_state():
    try:
        return json.loads(STATE_F.read_text()) if STATE_F.exists() else {"swarm": []}
    except:
        return {"swarm": []}

def health(url, timeout=3):
    try:
        return httpx.get(url, timeout=timeout).is_success
    except:
        return False

def redeploy(folder):
    log(f"redeploy {folder}")
    try:
        import subprocess
        subprocess.run("railway up", shell=True, cwd=folder, capture_output=True, check=True)
    except Exception as e:
        log(f"redeploy fail {e}")

# watchdog
def watchdog():
    while True:
        for f in safe_state().get("swarm", []):
            if not health(f["railway"]):
                redeploy(pathlib.Path(f"swarm/{f['slug']}"))
        time.sleep(300)

threading.Thread(target=watchdog, daemon=True).start()

# web ui
app = FastAPI(title="SwarmCommander")

@app.get("/", response_class=HTMLResponse)
def dash():
    st = safe_state()
    rows = "\n".join(
        f"<tr><td>{s['slug']}</td><td><a href='{s['railway']}'>Railway</a></td>"
        f"<td><a href='{s['gumroad']}'>Gumroad</a></td>"
        f"<td>{'🟢' if health(s['railway']) else '🔴'}</td></tr>"
        for s in st.get("swarm", [])
    )
    html = f"""
    <h1>🧬 Live Swarm</h1>
    <table border=1>
    <tr><th>Slug</th><th>Railway</th><th>Gumroad</th><th>Health</th></tr>
    {rows or "<tr><td colspan=4>🌱 No funnels yet</td></tr>"}
    </table>
    <p><a href="/logs">logs</a> | <a href="/metrics">metrics</a></p>
    """
    return html

@app.get("/logs")
def logs():
    return HTMLResponse(f"<pre>{LOG_F.read_text() if LOG_F.exists() else 'No logs'}</pre>")

@app.get("/metrics")
def metrics():
    if not GUM_TOKEN:
        return {"error": "no GUMROAD_TOKEN"}
    data = []
    for p in safe_state().get("swarm", []):
        slug = p["slug"]
        r = httpx.get(f"https://api.gumroad.com/v2/products/{slug}/sales",
                      headers={"Authorization": f"Bearer {GUM_TOKEN}"}).json()
        sales = r.get("sales", [])
        rev = sum(int(s["variants"][0]["price"]) for s in sales)
        data.append({"slug": slug, "sales": len(sales), "revenue": rev})
    return data

if __name__ == "__main__":
    uvicorn.run("commander:app", host="0.0.0.0", port=7777)