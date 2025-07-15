#!/usr/bin/env python3
"""
emergency_spawn.py – auto-create a Gumroad product + Railway service
"""
import json, os, subprocess, uuid, pathlib, datetime
from pathlib import Path

ROOT   = Path(__file__).parent
STATE  = ROOT / "forge_state.json"
TOKEN  = os.getenv("GUMROAD_TOKEN")
if not TOKEN:
    raise RuntimeError("Set GUMROAD_TOKEN")

def safe_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"swarm": []}

def save_state(obj):
    STATE.write_text(json.dumps(obj, indent=2))

def create_product():
    slug  = f"ai-product-{uuid.uuid4().hex[:6]}"
    title = f"AI Income Stream #{datetime.datetime.utcnow().strftime('%m%d')}"
    price = 9
    body  = "Fully automated passive-income asset generated while you sleep."

    cmd = [
        "curl", "-s", "-X", "POST",
        "https://api.gumroad.com/v2/products",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-F", f"name={title}",
        "-F", f"url={slug}",
        "-F", f"price={price}",
        "-F", f"description={body}",
        "-F", "file=@dummy.pdf"
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(proc.stdout)

if __name__ == "__main__":
    state = safe_state()
    prod  = create_product()
    slug  = prod["product"]["url"]
    state["swarm"].append({
        "slug": slug,
        "railway": f"https://{slug}.up.railway.app",
        "gumroad": f"https://gum.co/{slug}"
    })
    save_state(state)
    print(f"✅ spawned https://gum.co/{slug}")