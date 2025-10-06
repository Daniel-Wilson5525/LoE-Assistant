# services/generator/shared/normalise.py
import json, re

_SPLIT = re.compile(r"[\r\n,;]+")

def to_array(x):
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    return [p.strip() for p in _SPLIT.split(str(x)) if p.strip()]

def trim(s):
    """
    Robust trim:
      - strings -> .strip()
      - lists   -> join non-empty items with ', '
      - others  -> str(...) then .strip()
    """
    if isinstance(s, str):
        return s.strip()
    if isinstance(s, list):
        parts = [str(i).strip() for i in s if str(i).strip()]
        return ", ".join(parts)
    return (str(s) if s is not None else "").strip()

def to_number(x):
    try:
        if x in (None, "", "TBD", "tbd"):
            return None
        return int(str(x).strip())
    except Exception:
        return None

def stringify_mapping(m):
    if isinstance(m, dict):
        parts = []
        for k, v in m.items():
            ks = str(k).strip().replace("_", " ")
            vs = trim(v)
            if vs:
                parts.append(f"{ks}: {vs}")
        return "; ".join(parts)
    return trim(m)

def coerce_json(text: str) -> dict:
    if not isinstance(text, str): return {}
    t = re.sub(r"^\s*```(?:json)?\s*", "", text.strip(), flags=re.I)
    t = re.sub(r"\s*```\s*$", "", t, flags=re.I)
    try: return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, flags=re.DOTALL)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
    return {}

# -------- mapping coercers (accept string OR dict) --------------------------

def _coerce_rollout(ro) -> dict:
    if isinstance(ro, dict):
        return {
            "waves": trim(ro.get("waves")),
            "floors": trim(ro.get("floors")),
            "ooh_windows": trim(ro.get("ooh_windows")),
            "change_approvals": trim(ro.get("change_approvals")),
        }
    # If a single string was returned, treat it as "waves/sequence" text
    s = trim(ro)
    return {"waves": s, "floors": "", "ooh_windows": "", "change_approvals": ""}

def _coerce_governance(gv) -> dict:
    if isinstance(gv, dict):
        return {
            "pm": trim(gv.get("pm")),
            "comms_channels": trim(gv.get("comms_channels")),
            "escalation": trim(gv.get("escalation")),
        }
    s = trim(gv)
    # If just a string, better to store it in pm
    return {"pm": s, "comms_channels": "", "escalation": ""}

def _coerce_handover(ho) -> dict:
    if isinstance(ho, dict):
        return {
            "docs": trim(ho.get("docs")),
            "acceptance_criteria": trim(ho.get("acceptance_criteria")),
        }
    s = trim(ho)
    return {"docs": s, "acceptance_criteria": ""}

def _coerce_staging(st) -> dict:
    if isinstance(st, dict):
        return {
            "ic_used": bool(st.get("ic_used")),
            "doa": bool(st.get("doa")),
            "burn_in": bool(st.get("burn_in")),
            "labelling": trim(st.get("labelling")) if isinstance(st.get("labelling"), (str, list)) else "",
            "packing": trim(st.get("packing")) if isinstance(st.get("packing"), (str, list)) else "",
        }
    s = trim(st)
    # If just a string (e.g., "labels provided"), treat as labelling note
    return {"ic_used": False, "doa": False, "burn_in": False, "labelling": s, "packing": ""}

def _coerce_visits_caps(vc) -> dict:
    if isinstance(vc, dict):
        return {
            "install_max_visits": to_number(vc.get("install_max_visits")),
            "post_deploy_max_visits": to_number(vc.get("post_deploy_max_visits")),
            "site_survey_window_weeks": to_number(vc.get("site_survey_window_weeks")),
        }
    n = to_number(vc)
    return {"install_max_visits": n, "post_deploy_max_visits": None, "site_survey_window_weeks": None}

def _coerce_counts(ct) -> dict:
    if isinstance(ct, dict):
        return {
            "aps_ordered": to_number(ct.get("aps_ordered")),
            "aps_to_mount": to_number(ct.get("aps_to_mount")),
            "devices_total": to_number(ct.get("devices_total")),
        }
    n = to_number(ct)
    return {"aps_ordered": None, "aps_to_mount": None, "devices_total": n}

def _normalize_devices(devs) -> list[dict]:
    """
    Accepts:
      - list of dicts like {'type': 'Server', 'qty': 10}
      - list of strings like 'Server', 'Cisco 9300 x8'
    Returns list of {'type': str, 'qty': int}
    """
    out = []
    for x in (devs or []):
        t, q = "", 0
        if isinstance(x, dict):
            t = trim(x.get("type"))
            q = to_number(x.get("qty")) or 0
        else:
            s = trim(x)
            m = re.search(r"\bx\s*(\d+)\b$", s, flags=re.I)
            if m:
                try: q = int(m.group(1))
                except Exception: q = 0
                t = trim(re.sub(r"\bx\s*\d+\b$", "", s, flags=re.I))
            else:
                t = s
        if t or q:
            out.append({"type": t, "qty": int(q)})
    return out

# -------- main --------------------------------------------------------------

def normalize_schema(s: dict) -> dict:
    s = dict(s or {})

    # Arrays (free-text)
    for k in ["prerequisites", "assumptions", "out_of_scope", "deliverables", "constraints"]:
        s[k] = to_array(s.get(k))

    # Sites array of dicts
    s["sites"] = [
        {"name": trim(x.get("name")), "address": trim(x.get("address"))}
        for x in (s.get("sites") or [])
        if (isinstance(x, dict) and (x.get("name") or x.get("address")))
    ]

    # Devices / BOM
    if not isinstance(s.get("bom"), list): s["bom"] = []
    s["devices"] = _normalize_devices(s.get("devices"))
    if not s["bom"] and s.get("devices"):
        for d in s["devices"]:
            if d["type"] or d["qty"]:
                s["bom"].append({"type": d["type"], "model": "", "qty": d["qty"], "notes": ""})

    # Coerce structured mappings (accept dict or string)
    s["rollout"]    = _coerce_rollout(s.get("rollout"))
    s["governance"] = _coerce_governance(s.get("governance"))
    s["handover"]   = _coerce_handover(s.get("handover"))
    s["staging"]    = _coerce_staging(s.get("staging"))
    s["visits_caps"]= _coerce_visits_caps(s.get("visits_caps"))
    s["counts"]     = _coerce_counts(s.get("counts"))

    # Scalars
    s["client"]       = trim(s.get("client"))
    s["project_name"] = trim(s.get("project_name"))
    s["service"]      = trim(s.get("service"))
    s["scope"]        = trim(s.get("scope"))
    s["environment"]  = trim(s.get("environment"))
    s["timeline"]     = stringify_mapping(s.get("timeline"))
    s["notes_raw"]    = trim(s.get("notes_raw"))
    if len(s["notes_raw"]) > 3000:
        s["notes_raw"] = s["notes_raw"][:3000]

    # Wave plan – force list
    s["wave_plan"] = s.get("wave_plan") if isinstance(s.get("wave_plan"), list) else []

    return s
