import re

def sum_bom_qty(schema: dict) -> int:
    total = 0
    for r in (schema.get("bom") or []):
        try: total += int(r.get("qty") or 0)
        except Exception: pass
    if total == 0:
        for d in (schema.get("devices") or []):
            try: total += int(d.get("qty") or 0)
            except Exception: pass
    return total

def derive_mounting_qty_from_notes(notes: str) -> int | None:
    if not notes: return None
    m = re.search(r"(require\s+mount(?:ing)?|to\s+be\s+mounted)\D+(\d{2,5})", notes, flags=re.I)
    if m:
        try: return int(m.group(2))
        except Exception: return None
    return None

def extract_phase_block(notes: str) -> str:
    if not notes: return ""
    start = re.search(r"(?im)^(?:core\s*&\s*user|phase\s*\d+)\b", notes)
    if not start: return ""
    tail = notes[start.start():]
    m = re.search(r"\n\s*\n", tail)
    chunk = tail[: m.start()] if m else tail
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in chunk.splitlines() if ln.strip()]
    return "\n".join(lines)

def primary_site_line(schema: dict) -> str:
    for s in (schema.get("sites") or []):
        name = (s.get("name") or "").strip()
        addr = (s.get("address") or "").strip()
        if name and addr: return f"{name} — {addr}"
        if addr: return addr
        if name: return name
    return ""
