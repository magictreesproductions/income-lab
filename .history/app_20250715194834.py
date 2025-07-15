from flask import Flask, send_file
import qrcode, io, os

app = Flask(__name__)

@app.route("/")
def qr():
    img = qrcode.make("https://gum.co/tip-001")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)