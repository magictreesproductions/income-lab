#!/usr/bin/env python3
"""
forge.py  –  Infinite Product Forge
Usage
-----
python forge.py --bootstrap   # start the swarm
python forge.py --status      # show live products
python forge.py --halt        # graceful shutdown
"""
import json, os, time, requests, subprocess, uuid, textwrap, threading
from pathlib import Path

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY") or "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"
HEADERS = {"Authorization": f"Bearer {OPENROUTER_KEY}", "HTTP-Referer": "https://income-lab.up.railway.app"}

STATE = Path("forge_state.json")
state = json.loads(STATE.read_text()) if STATE.exists() else {"swarm": []}

def ask(prompt, model="gpt-4o-mini"):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json={"model": model, "messages": [{"role": "user", "content": prompt}]}
    )
    return r.json()["choices"][0]["message"]["content"].strip()

def spawn_product():
    # 1. Oracle chooses niche
    niche = ask("Return only a two-word niche for a €2 digital product (e.g., retro fonts).")
    slug = niche.lower().replace(" ", "-")

    # 2. Designer writes code + copy
    code = ask(f"Write a minimal Flask app that serves a dynamic QR code pointing to https://gum.co/{slug}. Return only the code.", model="claude-3-haiku")
    copy = ask(f"Write a 50-char Gumroad product title + 1-sentence description for '{niche}'. Return JSON only.", model="claude-3-haiku")

    # 3. DevOps deploys
    folder = Path(f"swarm/{slug}")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "app.py").write_text(code)
    (folder / "requirements.txt").write_text("flask qrcode pillow")
    (folder / "Procfile").write_text("web: python app.py")

    subprocess.run("railway up", shell=True, cwd=folder, capture_output=True)
    url = f"https://{slug}-production.up.railway.app"

    # 4. DevOps creates Gumroad product (manual fallback if no token)
    gum_url = f"https://gum.co/{slug}"

    # 5. Log
    state["swarm"].append({"slug": slug, "railway": url, "gumroad": gum_url})
    STATE.write_text(json.dumps(state, indent=2))
    print(f"🔥 Spawned {niche}: {gum_url}")

def autopilot():
    while True:
        spawn_product()
        time.sleep(7200)  # every 2 hours

if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--halt", action="store_true")
    args = ap.parse_args()

    if args.bootstrap:
        threading.Thread(target=autopilot, daemon=True).start()
        print("🧬 Swarm is alive. Press Ctrl+C to pause.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Swarm paused.")
    elif args.status:
        for p in state["swarm"]:
            print(p)
    else:
        ap.print_help(sys.stderr)