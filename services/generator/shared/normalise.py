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

# Regex to grab the biggest JSON-looking block
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def coerce_json(text):
    """
    Try *really hard* to turn an LLM response into a Python dict.

    Handles:
      - Plain JSON
      - JSON wrapped in ```json ... ``` fences
      - Extra prose before/after the JSON
    Returns:
      - dict on success
      - None on failure
    """
    # Already parsed?
    if isinstance(text, dict):
        return text

    if text is None:
        return None

    s = str(text).strip()
    if not s:
        return None

    # 1) Strip code fences like ```json ... ```
    # Leading fence
    if s.startswith("```"):
        # remove the first line (``` or ```json)
        s = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", s, count=1, flags=re.MULTILINE)
        # remove a trailing ``` if present
        s = re.sub(r"```$", "", s.strip(), count=1, flags=re.MULTILINE).strip()

    # 2) First attempt: parse as-is
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 3) Fallback: extract the largest {...} block and try that
    m = _JSON_OBJECT_RE.search(s)
    if m:
        candidate = m.group(0)
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # 4) Give up
    return None


def _sum_devices_from_sites(s: dict) -> int | None:
    """
    Compute total device count from per-site BOMs only.
    - Uses sites[*].bom
    - Ignores optics rows (type containing 'optic')
    - Treats missing/None qty as 0
    """
    total = 0
    for site in (s.get("sites") or []):
        for row in (site.get("bom") or []):
            if not isinstance(row, dict):
                continue
            t = (row.get("type") or "").strip().lower()
            # Skip optics if you don't want to count them as "devices"
            if "optic" in t:
                continue
            qty = to_number(row.get("qty"))
            if qty:
                total += qty
    return total or None



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

# 12/11/25 multi site addition
def _to_bool_or_none(x):
    if isinstance(x, bool): return x
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("true","yes","y","1","on"): return True
        if s in ("false","no","n","0","off"): return False
    return None

def _to_float_or_none(x):
    try:
        if x in (None, "", "TBD", "tbd"): return None
        return float(str(x).strip())
    except Exception:
        return None

def _coerce_tasks(t):
    """
    Accept either:
      - dict with phase objects, e.g. {"installation": {"include": true, "engineers": 2, "days": 1.5, "steps": [...]} }
      - dict with booleans, e.g. {"installation": true}
      - strings like "yes"/"no" for include
    Always return a full 4-phase dict.
    """
    base = {
        "site_survey":        {"include": None, "engineers": None, "days": None, "steps": []},
        "installation":       {"include": True,  "engineers": None, "days": None, "steps": []},
        "optics_installation":{"include": None, "engineers": None, "days": None, "steps": []},
        "post_install":       {"include": None, "engineers": None, "days": None, "steps": []},
    }
    t = t if isinstance(t, dict) else {}

    out = {}
    for k, defaults in base.items():
        v = t.get(k)
        # Boolean or "yes/no" → set include only
        if isinstance(v, bool) or isinstance(v, str):
            out[k] = {
                "include": _to_bool_or_none(v) if not isinstance(v, bool) else v,
                "engineers": None,
                "days": None,
                "steps": [],
            }
            continue
        # Proper mapping → coerce fields
        if isinstance(v, dict):
            inc = v.get("include")
            out[k] = {
                "include": inc if isinstance(inc, bool) else _to_bool_or_none(inc) if inc is not None else defaults["include"],
                "engineers": to_number(v.get("engineers")),
                "days": _to_float_or_none(v.get("days")),
                "steps": to_array(v.get("steps")),
            }
            continue
        # Missing/unknown → defaults
        out[k] = dict(defaults)

    return out

def _coerce_site(s):
    s = s if isinstance(s, dict) else {}
    out = {
        "site_id": trim(s.get("site_id")) or "",
        "name": trim(s.get("name")),
        "address": trim(s.get("address")),
        "country": trim(s.get("country")),
        "constraints": to_array(s.get("constraints")),
        "bom": s.get("bom") if isinstance(s.get("bom"), list) else [],
        "optics_bom": s.get("optics_bom") if isinstance(s.get("optics_bom"), list) else [],
        "tasks": _coerce_tasks(s.get("tasks")),
        "assumptions": to_array(s.get("assumptions")),
        "out_of_scope": to_array(s.get("out_of_scope")),
    }
    # ensure stable site_id
    if not out["site_id"]:
        base = out["name"] or out["address"] or out["country"] or "site"
        out["site_id"] = re.sub(r"[^a-z0-9]+","-", base.lower()).strip("-")
    return out

# ---------- NEW: global_scope coercer ---------------------------------------

def _coerce_global_scope(gs) -> dict:
    """
    Normalise global_scope to:
      {
        "rack_and_stack":       {"include": bool|None, "notes": str},
        "optics_installation":  {"include": bool|None, "notes": str},
        "site_survey":          {"include": bool|None, "notes": str},
        "post_install":         {"include": bool|None, "notes": str},
      }

    Accepts:
      - dict with those keys as either:
          * bool / "yes"/"no" / "true"/"false"
          * { include, notes }
      - any other value → treated as "unknown" (include=None, notes="")
    """
    keys = ["site_survey", "rack_and_stack", "post_install", "optics_installation"]
    out = {}

    if not isinstance(gs, dict):
        gs = {}

    for k in keys:
        v = gs.get(k)

        if isinstance(v, dict):
            inc = v.get("include")
            notes = trim(v.get("notes"))
            out[k] = {
                "include": inc if isinstance(inc, bool) else _to_bool_or_none(inc),
                "notes": notes,
            }
        elif isinstance(v, (bool, str)):
            out[k] = {
                "include": v if isinstance(v, bool) else _to_bool_or_none(v),
                "notes": "",
            }
        else:
            out[k] = {
                "include": None,
                "notes": "",
            }

    return out

# ---------- NEW: aggregate per-site BOMs into top-level BOM -----------------

def _aggregate_site_boms(sites) -> list:
    """
    Build a flattened BOM from all site.bom and site.optics_bom entries.
    Ensures each row has {type, model, qty, notes}.
    """
    aggregated = []
    for site in sites or []:
        for src_key in ("bom", "optics_bom"):
            for row in (site.get(src_key) or []):
                if not isinstance(row, dict):
                    continue
                aggregated.append({
                    "type": trim(row.get("type")) or "Device",
                    "model": trim(row.get("model")),
                    "qty": to_number(row.get("qty")) or 0,
                    "notes": trim(row.get("notes")),
                })
    return aggregated

def _merge_devices_into_bom(bom: list, devices) -> list:
    """
    Fold legacy `devices` into BOM.
    Accepts:
      - list of dicts like {'type': 'Server', 'qty': 10}
      - list of strings like 'Server x8'
    Produces BOM rows {type, model, qty, notes}.
    """
    out = list(bom or [])
    for x in (devices or []):
        typ, qty = "", 0
        if isinstance(x, dict):
            typ = trim(x.get("type"))
            qty = to_number(x.get("qty")) or 0
        else:
            s = trim(x)
            m = re.search(r"\bx\s*(\d+)\b", s, flags=re.I)
            if m:
                qty = int(m.group(1))
                typ = trim(re.sub(r"\bx\s*\d+\b", "", s, flags=re.I))
            else:
                typ = s
        if typ or qty:
            out.append({"type": typ or "Device", "model": "", "qty": int(qty), "notes": ""})
    return out

# -------- main --------------------------------------------------------------

def normalize_schema(s: dict) -> dict:
    s = dict(s or {})

    # Arrays (free-text)
    for k in ["prerequisites", "assumptions", "out_of_scope", "deliverables", "constraints"]:
        s[k] = to_array(s.get(k))

    # Sites: preserve rich objects
    s["sites"] = [
        _coerce_site(x)
        for x in (s.get("sites") or [])
        if isinstance(x, dict) and (x.get("name") or x.get("address") or x.get("bom"))
    ]

    # Global scope – now always {key: {include, notes}}
    s["global_scope"] = _coerce_global_scope(s.get("global_scope"))

    # Effort summary: derive engineer-days from per-site installation tasks
    tot_ed = 0.0
    for site in s["sites"]:
        inst = (site.get("tasks") or {}).get("installation") or {}
        e, d = inst.get("engineers"), inst.get("days")
        if isinstance(e, (int, float)) and isinstance(d, (int, float)):
            tot_ed += e * d

    s["effort_summary"] = s.get("effort_summary") if isinstance(s.get("effort_summary"), dict) else {}
    s["effort_summary"]["totals"] = (s["effort_summary"].get("totals") or {})
    s["effort_summary"]["totals"]["engineer_days"] = (
        round(tot_ed, 2) if tot_ed > 0 else s["effort_summary"]["totals"].get("engineer_days")
    )
    s["effort_summary"]["totals"]["sites"] = len(s["sites"]) or None

    # We now treat per-site BOMs as the source of truth.
    # Top-level 'bom' is kept only for backwards compatibility and left empty.
    s.pop("devices", None)  # drop any legacy 'devices' field
    s["bom"] = []           # do not maintain a global BOM anymore


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

    wave_plan = s.get("wave_plan")
    s["wave_plan"] = wave_plan if isinstance(wave_plan, list) else []


    # ---- Auto-derive counts.devices_total from per-site BOMs ----
    total = s.get("counts", {}).get("devices_total")
    if not total:
        computed = _sum_devices_from_sites(s)
        if computed:
            s["counts"]["devices_total"] = computed


    return s
