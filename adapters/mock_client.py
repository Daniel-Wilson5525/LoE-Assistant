# adapters/mock_client.py
import json
from datetime import datetime

class AIClient:
    """
    Dumb stub to unblock dev. Returns JSON strings the rest of the app can parse.
    Tries to guess whether the prompt is asking for a schema (ingest) or outputs (generate).
    """

    def complete(self, prompt: str, system: str | None = None,
                 json_mode: bool = False, max_tokens: int = 2500) -> str:
        want_outputs = any(k in prompt for k in [
            '"summary"', '"tasks"', '"open_questions"', 'PROJECT SUMMARY', 'PROJECT TASKS'
        ])
        if want_outputs:
            payload = {
                "summary": "PROJECT SUMMARY\nMock summary generated at "
                           + datetime.utcnow().isoformat() + "Z.",
                "tasks": "PROJECT TASKS\n- Do a thing\n- Do another thing",
                "open_questions": [
                    "Any change approvals required?",
                    "Out-of-hours constraints?"
                ],
            }
        else:
            # schema for /ingest
            payload = {
                "client": "Mock Client",
                "project_name": "",
                "service": "Installation",
                "scope": "Rack & Stack",
                "environment": "On-prem",
                "timeline": "2 weeks",
                "sites": [{"name": "HQ", "address": "1 Main St"}],
                "devices": [],
                "bom": [{"type":"AP","model":"AP64","qty":6,"notes":""}],
                "staging": {"ic_used": False, "doa": False, "burn_in": False,
                            "labelling": "", "packing": ""},
                "rollout": {"waves": "", "floors": "", "ooh_windows": "", "change_approvals": ""},
                "governance": {"pm": "", "comms_channels": "", "escalation": ""},
                "visits_caps": {"install_max_visits": None, "post_deploy_max_visits": None, "site_survey_window_weeks": None},
                "counts": {"aps_ordered": None, "aps_to_mount": None, "devices_total": None},
                "wave_plan": [{"phase": "", "floor": "", "allocations": [{"model": "", "qty": 0}]}],
                "brackets": [],
                "prerequisites": [],
                "assumptions": [],
                "out_of_scope": [],
                "handover": {"docs": "", "acceptance_criteria": ""},
                "constraints": [],
                "deliverables": []
            }
        return json.dumps(payload)
