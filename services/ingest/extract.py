# services/ingest/extract.py
import json, re, os
from services.prompt_loader import load_prompt_file

# Import classes only (choose at runtime)
from adapters.mock_client import AIClient as MockAIClient
from adapters.ai_client  import AIClient as RealAIClient

from services.generator.shared.normalise import normalize_schema


def _get_client():
    """Decide mock vs real at call time based on USE_MOCK env."""
    use_mock = os.getenv("USE_MOCK", "0") == "1"
    return MockAIClient() if use_mock else RealAIClient()

def _jload(t):
    try:
        return json.loads(t)
    except Exception:
        return None

def _empty_schema(notes_raw: str = "") -> dict:
    return {
        "client": "", "project_name": "", "service": "", "scope": "", "environment": "", "timeline": "",
        "sites": [], "bom": [],
        "staging": {"ic_used": False, "doa": False, "burn_in": False, "labelling": "", "packing": ""},
        "rollout": {"waves": "", "floors": "", "ooh_windows": "", "change_approvals": ""},
        "governance": {"pm": "", "comms_channels": "", "escalation": ""},
        "visits_caps": {"install_max_visits": None, "post_deploy_max_visits": None, "site_survey_window_weeks": None},
        "counts": {"aps_ordered": None, "aps_to_mount": None, "devices_total": None},
        "wave_plan": [],
        "brackets": [],
        "prerequisites": [], "assumptions": [], "out_of_scope": [],
        "handover": {"docs": "", "acceptance_criteria": ""},
        "constraints": [], "deliverables": [],
        "notes_raw": notes_raw,
    }

def _coerce_json(text: str) -> dict:
    obj = _jload(text)
    if obj is not None:
        return obj
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        obj = _jload(m.group(0))
        if obj is not None:
            return obj
    return _empty_schema()

def extract_fields(email_text: str) -> dict:
    email_text = (email_text or "").strip()
    if len(email_text) < 10:
        return _empty_schema(notes_raw=email_text)

    system  = load_prompt_file("services/ingest/prompts", "system.txt")
    content = load_prompt_file("services/ingest/prompts", "content.txt").replace("{{EMAIL_TEXT}}", email_text)

    client = _get_client()
    raw = client.complete(content, system=system, json_mode=False, max_tokens=2500)
    data = _coerce_json(raw)
    data["notes_raw"] = email_text

    # single place to clean + coerce everything (also folds legacy 'devices' into 'bom')
    data = normalize_schema(data)
    return data
