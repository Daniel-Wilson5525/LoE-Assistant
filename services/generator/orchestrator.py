# services/generator/orchestrator.py
from __future__ import annotations
import os, json, re
from services.prompt_loader import load_prompt_file
from services.generator.registry import get_mode

from adapters import AIClient
print(f"[generator] Using AIClient") 

def _coerce_json(text: str) -> dict:
    if isinstance(text, dict):
        return text
    try:
        return json.loads(str(text))
    except Exception:
        pass
    m = re.search(r"\{.*\}", str(text), flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # With json_mode=True this should basically never happen:
    return {"summary": "", "tasks": "", "open_questions": ["Non-JSON response from model"]}

def _ensure_heading(text: str, heading: str) -> str:
    if not text:
        return text
    stripped = str(text).lstrip()
    return f"{heading}\n{stripped}" if not stripped.upper().startswith(heading) else text

def generate_outputs(schema: dict, loe_type: str | None = None) -> dict:
    schema = dict(schema or {})
    # stamp loe_type if provided separately
    if loe_type and not schema.get("loe_type"):
        schema["loe_type"] = loe_type

    mode = get_mode(schema.get("loe_type"))

    # load system prompt from mode dir, fallback to default
    system = (
        load_prompt_file(mode.prompt_dir, "system.txt")
        or load_prompt_file("services/generator/modes/default", "system.txt")
        or "Return JSON only."
    )
    # build the user prompt via the mode
    user_prompt = mode.build_prompt(schema)

    client = AIClient()
    try:
        raw = client.complete(user_prompt, system=system, json_mode=True, max_tokens=3000)
    except TypeError:
        raw = client.complete(user_prompt, system=system, json_mode=False, max_tokens=3000)
    # Force strict JSON; AIClient handles enforcement + repair.
    raw = client.complete(
        user_prompt,
        system=system,
        json_mode=True,
        max_tokens=3000,
    )

    data = _coerce_json(raw)

    # normalize headings the UI expects
    data["summary"] = _ensure_heading(data.get("summary", ""), "PROJECT SUMMARY")
    data["tasks"]   = _ensure_heading(data.get("tasks",   ""), "PROJECT TASKS")
    if not isinstance(data.get("open_questions"), list):
        data["open_questions"] = [str(data.get("open_questions") or "")]

    # allow the mode to do final shaping (e.g., Rack & Stack extras)
    result = {
        "summary": data.get("summary", ""),
        "tasks": data.get("tasks", ""),
        "open_questions": data.get("open_questions", []),
    }
    result = mode.post_process(schema, result) if callable(mode.post_process) else result
    return result
