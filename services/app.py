from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from services.ingest.extract import extract_fields
from services.generator.orchestrator import generate_outputs

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

@app.get("/health")
def health():
    import os
    return jsonify({
        "ok": True,
        "mode": "mock" if os.getenv("USE_MOCK", "0") == "1" else "real"
    })


@app.post("/ingest")
def ingest():
    p = request.get_json(force=True) or {}
    text = (p.get("text") or "").strip()
    loe_type = (p.get("loe_type") or "").strip() or None
    if not text:
        return jsonify({"error":"Missing 'text'"}), 400
    schema = extract_fields(text)
    if loe_type:
        schema["loe_type"] = loe_type
    schema["notes_raw"] = text
    return jsonify({"schema": schema})

@app.post("/generate")
def generate():
    p = request.get_json(force=True) or {}
    schema   = p.get("schema") or {}
    loe_type = (p.get("loe_type") or schema.get("loe_type") or "").strip() or None
    out = generate_outputs(schema, loe_type)
    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5050)), debug=True)
