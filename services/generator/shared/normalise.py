import json, re

_SPLIT = re.compile(r"[\r\n,;]+")

def to_array(x):
    if x is None: return []
    if isinstance(x, list): return [str(i).strip() for i in x if str(i).strip()]
    return [p.strip() for p in _SPLIT.split(str(x)) if p.strip()]

def trim(s): return (s or "").strip()

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

def normalize_schema(s: dict) -> dict:
    s = dict(s or {})

    if not isinstance(s.get("bom"), list): s["bom"] = []
    if not isinstance(s.get("devices"), list): s["devices"] = []

    for k in ["prerequisites", "assumptions", "out_of_scope", "deliverables", "constraints"]:
        s[k] = to_array(s.get(k))

    ro = s.get("rollout") or {}
    s["rollout"] = {
        "waves": trim(ro.get("waves")),
        "floors": trim(ro.get("floors")),
        "ooh_windows": trim(ro.get("ooh_windows")),
        "change_approvals": trim(ro.get("change_approvals")),
    }
    gv = s.get("governance") or {}
    s["governance"] = {
        "pm": trim(gv.get("pm")),
        "comms_channels": trim(gv.get("comms_channels")),
        "escalation": trim(gv.get("escalation")),
    }
    ho = s.get("handover") or {}
    s["handover"] = {
        "docs": trim(ho.get("docs")),
        "acceptance_criteria": trim(ho.get("acceptance_criteria")),
    }
    st = s.get("staging") or {}
    lab_raw, pack_raw = st.get("labelling"), st.get("packing")
    s["staging"] = {
        "ic_used": bool(st.get("ic_used")),
        "doa": bool(st.get("doa")),
        "burn_in": bool(st.get("burn_in")),
        "labelling": trim(lab_raw) if isinstance(lab_raw, str) else "",
        "packing": trim(pack_raw) if isinstance(pack_raw, str) else "",
    }
    s["sites"] = [
        {"name": trim(x.get("name")), "address": trim(x.get("address"))}
        for x in (s.get("sites") or []) if (x and (x.get("name") or x.get("address")))
    ]
    s["devices"] = [
        {"type": trim(x.get("type")), "qty": int(x.get("qty") or 0)}
        for x in (s.get("devices") or [])
        if (x and (x.get("type") or x.get("qty") not in (None, "")))
    ]
    if not s["bom"] and s.get("devices"):
        for d in (s.get("devices") or []):
            t = trim(d.get("type"))
            try: q = int(d.get("qty") or 0)
            except Exception: q = 0
            if t or q:
                s["bom"].append({"type": t, "model": "", "qty": q, "notes": ""})

    for k in ["client","project_name","service","scope","environment","timeline","notes_raw"]:
        s[k] = trim(s.get(k))
    if len(s["notes_raw"]) > 3000:
        s["notes_raw"] = s["notes_raw"][:3000]
    return s
