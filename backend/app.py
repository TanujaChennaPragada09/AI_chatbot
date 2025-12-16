from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import mysql.connector
from fpdf import FPDF
from dotenv import load_dotenv
import os
from datetime import datetime
from googletrans import Translator

# -----------------------------
# LOAD ENV VARIABLES
# -----------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))

MODEL_NAME = "llama3.2:1b"

app = Flask(__name__)
CORS(app)

translator = Translator()

# -----------------------------
# DB CONNECTION
# -----------------------------
def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(20),
            language VARCHAR(10),
            message LONGTEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# -----------------------------
# SAVE MESSAGE
# -----------------------------
def save_message(role, lang, message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (role, language, message) VALUES (%s, %s, %s)",
        (role, lang, message)
    )
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# LOAD HISTORY
# -----------------------------
def load_history():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, language, message, timestamp FROM history ORDER BY id ASC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "role": r[0],
            "language": r[1],
            "message": r[2],
            "timestamp": r[3].strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in rows
    ]

# -----------------------------
# HEALTH
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend running"})

# -----------------------------
# CHAT API (TRUE MULTILINGUAL)
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"response": "Please enter a message"}), 400

        # Detect language
        detected = translator.detect(user_message)
        user_lang = detected.lang

        # Translate to English
        translated_input = (
            translator.translate(user_message, src=user_lang, dest="en").text
            if user_lang != "en" else user_message
        )

        save_message("user", user_lang, user_message)

        # Run Ollama (English only)
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, translated_input],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({"response": "AI error"}), 500

        ai_reply_en = result.stdout.strip()

        # Translate back to user language
        final_reply = (
            translator.translate(ai_reply_en, src="en", dest=user_lang).text
            if user_lang != "en" else ai_reply_en
        )

        save_message("bot", user_lang, final_reply)

        return jsonify({
            "response": final_reply,
            "language": user_lang,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"response": str(e)}), 500

# -----------------------------
# CHAT HISTORY
# -----------------------------
@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_history())

# -----------------------------
# CLEAR HISTORY
# -----------------------------
@app.route("/clear-history", methods=["POST"])
def clear_history():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM history")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "History cleared"})

# -----------------------------
# DOWNLOAD PDF (MULTILINGUAL)
# -----------------------------
@app.route("/download-pdf", methods=["GET"])
def download_pdf():
    chats = load_history()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0, 10, "TanujaNikitha AI Chat History", ln=True, align="C")
    pdf.ln(5)

    for c in chats:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, f"{c['role'].upper()} ({c['language']}) {c['timestamp']}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, c["message"])
        pdf.ln(2)

    filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)

# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
