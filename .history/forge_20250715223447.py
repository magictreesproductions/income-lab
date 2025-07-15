#!/usr/bin/env python3
"""
forge.py  –  Infinite AI-Product Forge
python forge.py --bootstrap   # run forever
"""
import os, json, time, uuid, textwrap, zipfile, io, subprocess, pathlib, httpx, openai
from pathlib import Path

# ---------- CONFIG ----------
STATE_FILE   = Path("forge_state.json")
OPENAI_KEY   = os.getenv("OPENROUTER_KEY") or os.getenv("OPENAI_API_KEY")
HEADERS      = {"Authorization": f"Bearer {OPENAI_KEY}", "HTTP-Referer": "https://income-lab.up.railway.app"}
# ---------- UTILS ----------
# ---------- bullet-proof helpers ----------
def safe_ask(prompt, model="gpt-4o-mini"):
    try:
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_KEY')}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("⚠️ ask fail", e)
        return '{"niche":"fallback","title":"Fallback Asset","hook":"Instant €2 download"}'

def safe_dalle(prompt):
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENROUTER_KEY"),
                               base_url="https://openrouter.ai/api/v1")
        url = client.images.generate(model="dall-e-3", prompt=prompt,
                                     size="1024x1024", n=1).data[0].url
        return httpx.get(url, timeout=30).content
    except Exception as e:
        print("⚠️ dalle fail", e)
        return b""

def safe_gumroad(slug, title):
    try:
        r = httpx.post(
            "https://api.gumroad.com/v2/products",
            headers={"Authorization": f"Bearer {os.getenv('GUMROAD_TOKEN')}"},
            json={"name": title, "url": slug, "price": 200,
                  "description": "AI-generated micro-asset", "published": True},
            timeout=30
        )
        return r.json()["product"]["id"]
    except Exception as e:
        print("⚠️ gumroad fail", e)
        return None

# ---------- STATE ----------
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"swarm": []}

# ---------- CORE LOOP ----------
def spawn():
    # 1. Idea
    raw = ask("Return ONLY JSON like {\"niche\":\"neon cursors\",\"title\":\"Neon Cursor Pack\",\"hook\":\"8-bit cursors for retro vibes\",\"keywords\":\"neon,8-bit,cursor\"}")
    try:
        meta = json.loads(raw)
    except:
        meta = {"niche":"micro-asset", "title":"Micro Asset", "hook":"Instant download €2", "keywords":"asset"}

    slug = meta["niche"].lower().replace(" ", "-")
    print(f"🧠 spawning {slug}...")

    # 2. AI image
    img = dall_e(f"A cool marketing thumbnail for '{meta['title']}', cyberpunk style, 1024x1024")

    # 3. Build .zip
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        z.writestr("README.txt", f"{meta['title']}\n{meta['hook']}")
        if img:
            z.writestr("preview.png", img)
        z.writestr("license.txt", "Royalty-free for personal & commercial.")
    zbuf.seek(0)

    # 4. Gumroad product
    r = gumroad_post("products", json={
        "name": meta["title"],
        "url": slug,
        "price": 200,
        "description": meta["hook"],
        "published": True
    })
    prod_id = r.json()["product"]["id"]
    gumroad_post(f"products/{prod_id}/files", files={"file": (f"{slug}.zip", zbuf.read())})
    gum_url = f"https://gum.co/{slug}"

    # 5. Flask landing page
    folder = pathlib.Path(f"swarm/{slug}")
    folder.mkdir(exist_ok=True)
    folder.joinpath("app.py").write_text(textwrap.dedent(f"""
        from flask import Flask, send_file, abort
        import qrcode, io, os
        app = Flask(__name__)
        @app.route("/")
        def page():
            qr = qrcode.make("{gum_url}")
            buf = io.BytesIO(); qr.save(buf, format="PNG"); buf.seek(0)
            return send_file(buf, mimetype="image/png")
        if __name__ == "__main__":
            port = int(os.environ.get("PORT", 5000))
            app.run(host="0.0.0.0", port=port)
    """).lstrip())
    folder.joinpath("requirements.txt").write_text("flask qrcode pillow")
    folder.joinpath("Procfile").write_text("web: python app.py")

    subprocess.run("railway up", shell=True, cwd=folder, capture_output=True)
    state["swarm"].append({"slug": slug, "railway": f"https://{slug}-production.up.railway.app", "gumroad": gum_url})
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"🔥 LIVE: {gum_url}")

def autopilot():
    while True:
        spawn()
        time.sleep(3600)  # 1 h tonight, change to 7200 for 2 h

if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", action="store_true")
    args = ap.parse_args()
    if args.bootstrap:
        autopilot()
    else:
        print("use --bootstrap")