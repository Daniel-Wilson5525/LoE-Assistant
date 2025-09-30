from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, request, jsonify, make_response

from services.ingest.extract import extract_fields
from services.generator.orchestrator import generate_outputs

app = Flask(__name__)


def _cors_ok():
    """Return a minimal 204 for preflight with permissive CORS headers."""
    resp = make_response("", 204)
    origin = request.headers.get("Origin", "*")
    resp.headers["Access-Control-Allow-Origin"]  = origin
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Vary"] = "Origin"
    return resp

@app.after_request
def _add_cors(resp):
    origin = request.headers.get("Origin")
    if origin:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    return resp

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "mode": "mock" if os.getenv("USE_MOCK", "0") == "1" else "real"
    })

@app.route("/ingest", methods=["POST", "OPTIONS"])
def ingest():
    if request.method == "OPTIONS":
        return _cors_ok()

    p = request.get_json(force=True) or {}
    text = (p.get("text") or "").strip()
    loe_type = (p.get("loe_type") or "").strip() or None
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    schema = extract_fields(text)
    if loe_type:
        schema["loe_type"] = loe_type
    schema["notes_raw"] = text
    return jsonify({"schema": schema})

@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return _cors_ok()

    p = request.get_json(force=True) or {}
    schema   = p.get("schema") or {}
    loe_type = (p.get("loe_type") or schema.get("loe_type") or "").strip() or None
    out = generate_outputs(schema, loe_type)
    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5050)), debug=True)
