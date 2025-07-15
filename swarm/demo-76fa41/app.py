
from flask import Flask, send_file, redirect, url_for
import qrcode, io
app = Flask(__name__)
gum = "https://gum.co/demo-76fa41"
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
