import re

def _qty_from_row(r) -> int:
    """Return an integer qty from either a dict row or a string row."""
    try:
        if isinstance(r, dict):
            return int(r.get("qty") or 0)
        # string (or other): try patterns like "x6" or any trailing/standalone number
        s = str(r)
        m = re.search(r"\bx\s*(\d+)\b", s, flags=re.I) or re.search(r"\b(\d+)\b", s)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def sum_bom_qty(schema: dict) -> int:
    """Sum qtys from top-level, site-level, and legacy BOM/device lists."""
    total = 0

    # top-level BOM
    for r in (schema.get("bom") or []):
        total += _qty_from_row(r)

    # site-level BOMs
    for site in (schema.get("sites") or []):
        for r in (site.get("bom") or []):
            total += _qty_from_row(r)

    # legacy devices
    for d in (schema.get("devices") or []):
        total += _qty_from_row(d)

    return total


def derive_mounting_qty_from_notes(notes: str) -> int | None:
    """Extract quantities from phrases like 'require mounting 12'."""
    if not notes:
        return None
    m = re.search(r"(require\s+mount(?:ing)?|to\s+be\s+mounted)\D+(\d{2,5})", notes, flags=re.I)
    if m:
        try:
            return int(m.group(2))
        except Exception:
            return None
    return None


def extract_phase_block(notes: str) -> str:
    """Extracts a section starting with 'Core & User' or 'Phase #' from notes."""
    if not notes:
        return ""
    start = re.search(r"(?im)^(?:core\s*&\s*user|phase\s*\d+)\b", notes)
    if not start:
        return ""
    tail = notes[start.start():]
    m = re.search(r"\n\s*\n", tail)
    chunk = tail[: m.start()] if m else tail
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in chunk.splitlines() if ln.strip()]
    return "\n".join(lines)


def primary_site_line(schema: dict) -> str:
    """Returns a one-line summary of the first site (name + address)."""
    for s in (schema.get("sites") or []):
        name = (s.get("name") or "").strip()
        addr = (s.get("address") or "").strip()
        if name and addr:
            return f"{name} — {addr}"
        if addr:
            return addr
        if name:
            return name
    return ""
