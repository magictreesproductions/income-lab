#!/usr/bin/env python3
"""
emergency_spawn.py – create one product with *zero* APIs
"""
import os, zipfile, io, pathlib, subprocess, uuid, json

slug = f"demo-{uuid.uuid4().hex[:6]}"
title = "Demo Pixel Pack"
zip_bytes = io.BytesIO()
with zipfile.ZipFile(zip_bytes, "w") as z:
    z.writestr("README.txt", "Instant €2 pixel-pack.\nGenerated tonight.")
    z.writestr("preview.png", b"\x89PNG\r\n\x1a\n\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82")  # 1×1 red PNG
zip_bytes.seek(0)

folder = pathlib.Path(f"swarm/{slug}")
folder.mkdir(exist_ok=True)
folder.joinpath("product.zip").write_bytes(zip_bytes.read())
folder.joinpath("app.py").write_text(f"""
from flask import Flask, send_file, redirect, url_for
import qrcode, io
app = Flask(__name__)
gum = "https://gum.co/{slug}"
@app.route("/")
def qr():
    qr_img = qrcode.make(gum)
    buf = io.BytesIO(); qr_img.save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png")
@app.route("/buy")
def buy():
    return redirect(gum)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
""")
folder.joinpath("requirements.txt").write_text("flask qrcode pillow")
folder.joinpath("Procfile").write_text("web: python app.py")

subprocess.run(["railway", "up"], cwd=folder, check=True)

# add to commander state
state = pathlib.Path("forge_state.json")
swarm = json.loads(state.read_text()) if state.exists() else {"swarm": []}
swarm["swarm"].append({
    "slug": slug,
    "railway": f"https://{slug}-production.up.railway.app",
    "gumroad": f"https://gum.co/{slug}"
})
state.write_text(json.dumps(swarm, indent=2))
print(f"✅ LIVE: https://{slug}-production.up.railway.app")