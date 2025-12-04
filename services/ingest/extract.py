# services/ingest/extract.py
import json, re, os
from services.prompt_loader import load_prompt_file
from services.generator.shared.rack_units import enrich_schema_rack_units


# Import classes only (choose at runtime)
from adapters.mock_client import AIClient as MockAIClient
from adapters.ai_client  import AIClient as RealAIClient

from services.generator.shared.normalise import normalize_schema, coerce_json as _coerce_llm_json


def _get_client():
    """Decide mock vs real at call time based on USE_MOCK env."""
    use_mock = os.getenv("USE_MOCK", "0") == "1"
    return MockAIClient() if use_mock else RealAIClient()


def _empty_schema(notes_raw: str = "") -> dict:
    return {
        "client": "",
        "project_name": "",
        "service": "",
        "scope": "",
        "environment": "",
        "timeline": "",
        "sites": [],
        "bom": [],
        "global_scope": {},  # normalise_schema will coerce to full shape
        "effort_summary": {},
        "staging": {
            "ic_used": False,
            "doa": False,
            "burn_in": False,
            "labelling": "",
            "packing": "",
        },
        "rollout": {
            "waves": "",
            "floors": "",
            "ooh_windows": "",
            "change_approvals": "",
        },
        "governance": {
            "pm": "",
            "comms_channels": "",
            "escalation": "",
        },
        "visits_caps": {
            "install_max_visits": None,
            "post_deploy_max_visits": None,
            "site_survey_window_weeks": None,
        },
        "counts": {
            "aps_ordered": None,
            "aps_to_mount": None,
            "devices_total": None,
        },
        "wave_plan": [],
        "brackets": [],
        "prerequisites": [],
        "assumptions": [],
        "out_of_scope": [],
        "handover": {
            "docs": "",
            "acceptance_criteria": "",
        },
        "constraints": [],
        "deliverables": [],
        "notes_raw": notes_raw,
    }


def _coerce_json_or_empty(text: str) -> dict:
    """
    Try to coerce LLM output into JSON, falling back to an empty schema.
    Uses the shared coerce_json from normalise.py to strip code fences, etc.
    """
    obj = _coerce_llm_json(text)

    print("[DEBUG] coerce_json type:", type(obj))

    if isinstance(obj, dict):
        print("[DEBUG] coerce_json keys:", list(obj.keys()))
        return obj

    print("[DEBUG] coerce_json failed, falling back to _empty_schema")
    return _empty_schema()



def extract_fields(email_text: str) -> dict:
    email_text = (email_text or "").strip()
    if len(email_text) < 10:
        return _empty_schema(notes_raw=email_text)

    system  = load_prompt_file("services/ingest/prompts", "system.txt")
    content = load_prompt_file("services/ingest/prompts", "content.txt").replace("{{EMAIL_TEXT}}", email_text)

    client = _get_client()
    raw = client.complete(
        content,
        system=system,
        json_mode=False,
        max_tokens=6000,
    )

    # TEMP: debug
    print("=== RAW LLM OUTPUT (first 1000 chars) ===")
    print(raw[:1000])
    print("=== END RAW ===")

    data = _coerce_json_or_empty(raw)

    # 🔍 DEBUG: see what the LLM JSON actually contains **before** normalize_schema
    try:
        print("[DEBUG] pre-normalize client:", data.get("client"))
        print("[DEBUG] pre-normalize sites len:", len(data.get("sites") or []))
        if (data.get("sites") or []):
            print("[DEBUG] pre-normalize first site keys:",
                list((data.get("sites") or [{}])[0].keys()))
    except Exception as e:
        print("[DEBUG] pre-normalize debug failed:", e)

    data["notes_raw"] = email_text

    # Single place to clean + coerce everything
    data = normalize_schema(data)
    data = enrich_schema_rack_units(data)
    return data

