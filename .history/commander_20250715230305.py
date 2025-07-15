#!/usr/bin/env python3
"""
commander.py  –  live swarm dashboard + instant spawn
"""
import json, os, time, threading, pathlib, httpx, subprocess, logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

ROOT      = Path(__file__).parent
STATE_F   = ROOT / "forge_state.json"
LOG_F     = ROOT / "commander.log"
GUM_TOKEN = os.getenv("GUMROAD_TOKEN")

logging.basicConfig(filename=LOG_F, level=logging.INFO,
                    format='%(asctime)s %(message)s')

app = FastAPI(title="SwarmCommander")

# ---------- helpers ----------
def safe_state():
    try:
        return json.loads(STATE_F.read_text()) if STATE_F.exists() else {"swarm": []}
    except Exception as e:
        logging.error(f"malformed json: {e}")
        return {"swarm": []}

def health(url, timeout=3):
    try:
        return httpx.get(url, timeout=timeout).is_success
    except Exception:
        return False

# ---------- routes ----------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    st = safe_state()
    rows = "\n".join(
        f"<tr><td>{s['slug']}</td>"
        f"<td><a href='{s['railway']}'>Railway</a></td>"
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
    <form action="/make-one" method="post">
        <button type="submit">🚀 Spawn New Product</button>
    </form>
    <p><a href="/logs">logs</a> | <a href="/metrics">metrics</a></p>
    """
    return html

@app.post("/make-one")
def spawn_one():
    """webhook to trigger emergency_spawn.py"""
    try:
        subprocess.Popen(["python", "emergency_spawn.py"], cwd=ROOT)
        return {"status": "spawn queued"}
    except Exception as e:
        logging.error(f"spawn failed: {e}")
        return {"status": "spawn error", "detail": str(e)}

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
        try:
            r = httpx.get(f"https://api.gumroad.com/v2/products/{slug}/sales",
                          headers={"Authorization": f"Bearer {GUM_TOKEN}"})
            sales = r.json().get("sales", [])
            rev = sum(int(s["variants"][0]["price"]) for s in sales)
            data.append({"slug": slug, "sales": len(sales), "revenue": rev})
        except Exception as e:
            data.append({"slug": slug, "sales": 0, "revenue": 0, "error": str(e)})
    return data

# ---------- start ----------
if __name__ == "__main__":
    uvicorn.run("commander:app", host="0.0.0.0", port=7777)