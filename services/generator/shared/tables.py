# services/generator/shared/tables.py
import re

def _canon_label(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"^(Juniper|Cisco)\s+", "", s, flags=re.I)
    s = re.sub(r"External\s*APs?-?\s*", "", s, flags=re.I)
    s = re.sub(r"\bAP\s+(\d+[A-Z]?)\b", r"AP\1", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    if re.fullmatch(r"(?i)(mist\s*edge(\s*me10)?|me10)", s): return "Mist Edge ME10"
    if re.search(r"(?i)476RPTP|antenna\s*patch\s*wifi", s):  return "ATS-01106"
    return s

def bom_table_markdown(schema: dict, include_rack_unit: bool = False) -> str:
    """
    Build a BOM table:
      - Part Number | Description | Qty | Type | [Rack Unit]
    """
    seen, rows = set(), []
    for r in (schema.get("bom") or []):
        pn   = (r.get("model") or "").strip()
        desc = (r.get("notes") or "").strip()
        typ  = (r.get("type") or "").strip()
        try: qty = int(r.get("qty") or 0)
        except Exception: qty = 0
        ru = (r.get("rack_unit") or r.get("ru") or "").strip() if isinstance(r.get("rack_unit") or r.get("ru"), str) else (r.get("rack_unit") or r.get("ru") or "")
        if not ((pn or typ) and qty > 0): 
            continue
        key = (pn.lower(), desc.lower(), qty, typ.lower(), str(ru))
        if key in seen: 
            continue
        seen.add(key)
        rows.append((pn or "-", desc or "-", qty, typ or "-", ru if ru not in (None, "") else "-"))

    if not rows:
        return ""

    if include_rack_unit:
        lines = [
            "| Part Number | Description | Qty | Type | Rack Unit |",
            "| --- | --- | :---: | --- | --- |",
        ]
        for pn, desc, qty, typ, ru in rows:
            lines.append(f"| {pn} | {desc} | {qty} | {typ} | {ru} |")
    else:
        lines = [
            "| Part Number | Description | Qty | Type |",
            "| --- | --- | :---: | --- |",
        ]
        for pn, desc, qty, typ, _ru in rows:
            lines.append(f"| {pn} | {desc} | {qty} | {typ} |")

    return "\n".join(lines)
