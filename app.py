import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Sabhi sources aur pre-flight requests ko safely handle karne ke liye CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Gemini configuration (Check environment or provide fallback)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

@app.route('/')
def health_check():
    return jsonify({
        "status": "online",
        "service": "AI Language Translator Backend",
        "ready": bool(GEMINI_API_KEY) and "YOUR_" not in GEMINI_API_KEY
    })

@app.route('/translate', methods=['POST', 'OPTIONS'])
def translate_text():
    # OPTIONS request handle karne ke liye (CORS preflight)
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json or {}
    text = data.get("text", "").strip()
    from_lang = data.get("from_lang", "English").strip()
    to_lang = data.get("to_lang", "Hindi").strip()

    if not text:
        return jsonify({"error": "No text provided for translation"}), 400

    # Strict system instruction for pure translations
    system_instruction = (
        f"You are a professional, high-accuracy language translation model. "
        f"Translate the given text from {from_lang} to {to_lang}. "
        f"Provide ONLY the direct translation. Do not add explanations, notes, or conversational filler."
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_instruction}\n\nText to translate: {text}"}]
        }]
    }
    
    headers = {"Content-Type": "application/json"}

    # Testing Fallback (If API Key is missing or default placeholder)
    if not GEMINI_API_KEY or "YOUR_" in GEMINI_API_KEY or GEMINI_API_KEY == "":
        # Hardcoded fallback text generation for testing frontend connectivity
        if to_lang.lower() == "hindi":
            mock_response = f"नमस्ते, क्या चल रहा है (Demo Translation)"
        else:
            mock_response = f"[Demo] {text} (Translated to {to_lang})"
        return jsonify({"translation": mock_response})

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            # Extracting token safely from Gemini's response structure
            try:
                translation = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                return jsonify({"translation": translation})
            except (KeyError, IndexError):
                return jsonify({"error": "Unexpected structure from Gemini API"}), 502
        else:
            return jsonify({"error": f"Gemini responded with code {response.status_code}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
