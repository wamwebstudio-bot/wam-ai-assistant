import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY nahi mili! .env file banayein aur usme "
        "GROQ_API_KEY=your_key_here likhein."
    )

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful assistant. Always reply in the SAME "
        "language and script that the user writes in. If the user "
        "writes in English, reply in English. If the user writes "
        "in Roman Urdu, reply in Roman Urdu. If the user writes in "
        "Urdu script, reply in Urdu script. Match the user's "
        "language naturally."
    ),
}

conversations = {}


def get_ai_reply(user_key, user_message):
    if user_key not in conversations:
        conversations[user_key] = [SYSTEM_PROMPT]

    conversations[user_key].append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversations[user_key],
    )
    ai_reply = response.choices[0].message.content

    conversations[user_key].append({"role": "assistant", "content": ai_reply})

    if len(conversations[user_key]) > 21:
        conversations[user_key] = [SYSTEM_PROMPT] + conversations[user_key][-20:]

    return ai_reply


@app.route("/")
def home():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({"error": "message field zaroori hai"}), 400

    user_message = data["message"].strip()

    if not user_message:
        return jsonify({"error": "Message khaali nahi ho sakta"}), 400

    user_key = "web_user"

    try:
        ai_reply = get_ai_reply(user_key, user_message)
    except Exception as e:
        return jsonify({"error": f"AI se jawab lene mein masla hua: {str(e)}"}), 500

    return jsonify({"reply": ai_reply})


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_message = request.form.get("Body", "").strip()
    sender_number = request.form.get("From", "unknown")

    resp = MessagingResponse()

    if not incoming_message:
        resp.message("Maazrat, mujhe koi message nahi mila.")
        return str(resp)

    try:
        ai_reply = get_ai_reply(sender_number, incoming_message)
    except Exception as e:
        ai_reply = f"Maazrat, abhi jawab dene mein masla hua: {str(e)}"

    resp.message(ai_reply)
    return str(resp)


@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or {}
    user_key = data.get("user_key", "web_user")
    conversations[user_key] = [SYSTEM_PROMPT]
    return jsonify({"status": "conversation reset ho gayi"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
