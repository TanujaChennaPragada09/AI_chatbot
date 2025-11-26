from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import mysql.connector
from fpdf import FPDF
from dotenv import load_dotenv
import os

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

# -----------------------------
# CREATE DATABASE TABLE IF NOT EXISTS
# -----------------------------
def init_db():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(50),
            message TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# -----------------------------
# SAVE CHAT MESSAGE
# -----------------------------
def save_message(role, msg):
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO history (role, message) VALUES (%s, %s)", (role, msg))
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# GET FULL CHAT HISTORY
# -----------------------------
def load_history():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT role, message FROM history")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"role": r[0], "message": r[1]} for r in rows]

# -----------------------------
# HOME ROUTE (API ONLY)
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask Backend Running Successfully"}), 200

# -----------------------------
# CHAT API
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"response": "Please enter a message."}), 400

        save_message("user", user_message)

        # Run Ollama
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, user_message],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({"response": f"ERROR: {result.stderr}"}), 500

        bot_reply = result.stdout.strip()
        save_message("assistant", bot_reply)

        return jsonify({"response": bot_reply})

    except Exception as e:
        return jsonify({"response": f"ERROR: {str(e)}"}), 500

# -----------------------------
# LOAD CHAT HISTORY API
# -----------------------------
@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_history())

# -----------------------------
# CLEAR CHAT HISTORY API
# -----------------------------
@app.route("/clear-history", methods=["POST"])
def clear_history():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM history")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Chat history cleared!"})

# -----------------------------
# DOWNLOAD PDF API
# -----------------------------
@app.route("/download-pdf", methods=["GET"])
def download_pdf():
    history = load_history()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for chat in history:
        pdf.multi_cell(0, 8, f"{chat['role'].upper()}: {chat['message']}")
        pdf.ln(2)
    filename = "chat_history.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)

# -----------------------------
# START SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
