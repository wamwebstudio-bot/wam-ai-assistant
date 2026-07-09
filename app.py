import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

# .env file se environment variables load karo
load_dotenv()

app = Flask(__name__)

# API key ab .env file se aayegi, code mein hardcoded nahi hai
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY nahi mili! .env file banayein aur usme "
        "GROQ_API_KEY=your_key_here likhein."
    )

client = Groq(api_key=GROQ_API_KEY)

# Har user session ke liye alag conversation rakhna better hai,
# lekin simple version ke liye ek global list use kar rahe hain.
conversation = [
    {
        "role": "system",
        "content": (
            "You are an assistant that ALWAYS replies in Roman Urdu "
            "(Urdu language written using English alphabet letters), "
            "no matter what language the user writes in. Never reply "
            "in pure English."
        ),
    }
]


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

    conversation.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversation,
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": f"AI se jawab lene mein masla hua: {str(e)}"}), 500

    conversation.append({"role": "assistant", "content": ai_reply})

    return jsonify({"reply": ai_reply})


@app.route("/reset", methods=["POST"])
def reset():
    """Conversation history reset karne ke liye"""
    global conversation
    conversation = [conversation[0]]  # sirf system message rakho
    return jsonify({"status": "conversation reset ho gayi"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
