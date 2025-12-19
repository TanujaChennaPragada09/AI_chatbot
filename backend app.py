from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess, os
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime
from googletrans import Translator
from fpdf import FPDF
from werkzeug.utils import secure_filename

# ---------------- CONFIG ----------------
load_dotenv()
MODEL_NAME = "llama3.2:1b"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))

app = Flask(__name__)
CORS(app)
translator = Translator()

# ---------------- DATABASE ----------------
def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(10),
            language VARCHAR(10),
            message LONGTEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    cur.close()
    db.close()

init_db()

def save_msg(role, lang, msg):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO history (role, language, message) VALUES (%s,%s,%s)",
        (role, lang, msg)
    )
    db.commit()
    cur.close()
    db.close()

# ---------------- ROUTES ----------------
@app.route("/")
def health():
    return jsonify({"status": "AI backend running"})

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"response": "Empty message"}), 400

    lang = translator.detect(user_msg).lang
    prompt_en = translator.translate(user_msg, src=lang, dest="en").text if lang!="en" else user_msg

    save_msg("user", lang, user_msg)

    result = subprocess.run(
        ["ollama", "run", MODEL_NAME, prompt_en],
        capture_output=True, text=True, timeout=120
    )

    ai_en = result.stdout.strip()
    reply = translator.translate(ai_en, src="en", dest=lang).text if lang!="en" else ai_en

    save_msg("bot", lang, reply)

    return jsonify({"response": reply})

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"response": "No file received"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"response": "Invalid file"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    save_msg("user", "file", f"Uploaded file: {filename}")
    save_msg("bot", "en", f"File '{filename}' uploaded successfully")

    return jsonify({"response": f"✅ File '{filename}' uploaded successfully"})

@app.route("/history")
def history():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT role, language, message FROM history ORDER BY id ASC")
    rows = cur.fetchall()
    cur.close()
    db.close()
    return jsonify([{"role":r[0],"language":r[1],"message":r[2]} for r in rows])

@app.route("/download-pdf")
def pdf():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT role, language, message FROM history")
    rows = cur.fetchall()
    cur.close()
    db.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 10, "TanujaNikitha AI Chat History", ln=True, align="C")

    for r in rows:
        pdf.set_font("Arial","B",10)
        pdf.cell(0,8,f"{r[0].upper()} ({r[1]})",ln=True)
        pdf.set_font("Arial",size=11)
        pdf.multi_cell(0,8,r[2])

    pdf.output("chat_history.pdf")
    return send_file("chat_history.pdf", as_attachment=True)

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

