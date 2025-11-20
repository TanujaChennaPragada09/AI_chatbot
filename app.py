from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import sqlite3
from fpdf import FPDF

app = Flask(__name__)
CORS(app)

DB_NAME = "chat_history.db"
MODEL_NAME = "llama3.2:1b"

# -----------------------------
# CREATE DATABASE IF NOT EXISTS
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# SAVE CHAT MESSAGE
# -----------------------------
def save_message(role, msg):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO history (role, message) VALUES (?, ?)", (role, msg))
    conn.commit()
    conn.close()

# -----------------------------
# GET FULL CHAT HISTORY
# -----------------------------
def load_history():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT role, message FROM history")
    rows = cur.fetchall()
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM history")
    conn.commit()
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
