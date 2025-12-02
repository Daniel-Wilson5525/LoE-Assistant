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
    Build a BOM table aggregated across:
      - legacy top-level schema["bom"]
      - per-site site["bom"]
      - per-site site["optics_bom"]

    Columns:
      - Part Number | Description | Qty | Type | [Rack Unit]
    """

    def iter_all_rows():
        # 1) Legacy global BOM (backwards compatible)
        for r in (schema.get("bom") or []):
            if isinstance(r, dict):
                yield r

        # 2) Per-site BOM + optics BOM (new multi-site structure)
        for site in (schema.get("sites") or []):
            if not isinstance(site, dict):
                continue
            for r in (site.get("bom") or []):
                if isinstance(r, dict):
                    yield r
            for r in (site.get("optics_bom") or []):
                if isinstance(r, dict):
                    yield r

    seen, rows = set(), []

    for r in iter_all_rows():
        pn_raw = (r.get("model") or "").strip()
        pn     = _canon_label(pn_raw) or pn_raw
        desc   = (r.get("notes") or "").strip()
        typ    = (r.get("type") or "").strip()

        try:
            qty = int(r.get("qty") or 0)
        except Exception:
            qty = 0

        # Prefer modern 'rack_units'; fall back to legacy 'rack_unit' / 'ru'
        if r.get("rack_units") is not None:
            ru_val = r.get("rack_units")
        elif r.get("rack_unit") is not None:
            ru_val = r.get("rack_unit")
        else:
            ru_val = r.get("ru")

        if isinstance(ru_val, str):
            ru = ru_val.strip()
        else:
            ru = ru_val if ru_val not in (None, "") else ""


        # Skip rows with no identifier or zero qty
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
