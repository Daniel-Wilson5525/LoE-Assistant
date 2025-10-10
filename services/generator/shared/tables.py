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

def wave_table_markdown(schema: dict) -> str:
    rows = schema.get("wave_plan") or []
    if not rows: return ""
    groups: dict[str, set[str]] = {}
    def add_label(lbl: str):
        if not lbl: return
        canon = _canon_label(lbl)
        groups.setdefault(canon, set()).add(lbl)
    for b in (schema.get("bom") or []):
        add_label((b.get("model") or b.get("type") or "").strip())
    for r in rows:
        for a in (r.get("allocations") or []):
            add_label((a.get("model") or "").strip())
    if not groups: return ""
    def col_key(c):
        m = re.match(r"^AP(\d+)([A-Z]?)$", c, flags=re.I)
        if m: return (0, int(m.group(1)), m.group(2) or "")
        if c.startswith("Mist Edge"): return (1, 0, c)
        if c.startswith("ATS-"):      return (1, 1, c)
        return (2, 0, c)
    cols = sorted(groups.keys(), key=col_key)
    header = ["Phase","Floor"] + cols
    align  = ["---","---"] + [":---:" for _ in cols]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(align)  + " |",
    ]
    for r in rows:
        phase = (r.get("phase") or "").strip()
        floor = (r.get("floor") or "").strip()
        sums = {c:0 for c in cols}
        for a in (r.get("allocations") or []):
            canon = _canon_label((a.get("model") or "").strip())
            try: qty = int(a.get("qty") or 0)
            except Exception: qty = 0
            if canon in sums: sums[canon] += qty
        cells = [str(sums[c]) for c in cols]
        lines.append("| " + " | ".join([phase, floor] + cells) + " |")
    return "\n".join(lines)

def bom_table_markdown(schema: dict) -> str:
    """
    Golden BOM table:
    Part Number | Description | Qty | Type | Rack Unit
    """
    seen, rows = set(), []
    for r in (schema.get("bom") or []):
        pn   = (r.get("model") or "").strip()
        desc = (r.get("notes") or "").strip() or "-"  # use notes as description if present
        typ  = (r.get("type")  or "").strip() or "-"
        try: qty = int(r.get("qty") or 0)
        except Exception: qty = 0

        # optional rack-unit keys we might receive
        ru = r.get("rack_unit") or r.get("ru") or r.get("u") or r.get("racku") or r.get("rack_unit_u")
        ru = (str(ru).strip() if ru not in (None, "") else "-")

        if not ((pn or typ) and qty > 0):
            continue
        key = (pn.lower(), desc.lower(), qty, typ.lower(), ru.lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append((pn or "-", desc, qty, typ, ru))

    if not rows:
        return ""

    lines = [
        "| Part Number | Description | Qty | Type | Rack Unit |",
        "| --- | --- | :---: | --- | --- |",
    ]
    for pn, desc, qty, typ, ru in rows:
        lines.append(f"| {pn} | {desc or '-'} | {qty} | {typ or '-'} | {ru or '-'} |")
    return "\n".join(lines)
