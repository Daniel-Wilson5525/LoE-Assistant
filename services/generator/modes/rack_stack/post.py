# services/generator/modes/rack_stack/post.py
import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

# --- constants --------------------------------------------------------------

# The ONLY task sections we want to keep (in this order)
_TASK_ORDER = [
    "Site Survey (Site Visit 1)",
    "Installation (Site Visit 2)",
    "Client Prerequisites",
    "Out of Scope",
]

# Default Field Engineer tools (always inject if missing)
_FE_BLOCK = (
    "**Field Engineer is expected to provide industry-standard tools including but not limited to:**\n"
    "- Basic Hand Tools\n"
    "- Labelling Printer\n"
    "- Ladder\n"
    "- Laptop with connecting cable"
)

# --- helpers ----------------------------------------------------------------

_CHECKBOX_RE = re.compile(r"^(?P<prefix>\s*[-*•o])\s*\[(?: |x|X)\]\s*", flags=re.M)
def _checkboxes_to_bullets(text: str) -> str:
    """Turn '- [ ] Task' / '* [x] Done' into '- Task' / '* Done'."""
    if not text: return text or ""
    return _CHECKBOX_RE.sub(lambda m: f"{m.group('prefix')} ", text)

def _bullets_block(items):
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    return "\n".join(f"- {i}" for i in items) if items else "- (none provided)"

def _ensure_field_engineer_block(summary: str) -> str:
    """Ensure the FE tools block appears in the summary once."""
    if not summary: return summary
    if re.search(r"(?i)field\s+engineer.*tools", summary):
        return summary
    # Insert FE block just before BOM_TABLE or, if absent, before the device totals line; else append.
    if re.search(r"\bBOM_TABLE\b", summary):
        return re.sub(r"\bBOM_TABLE\b", _FE_BLOCK + "\n\nBOM_TABLE", summary, count=1)
    m = re.search(r"\*\*Device totals:\*\*", summary)
    if m:
        return summary[:m.start()].rstrip() + "\n\n" + _FE_BLOCK + "\n\n" + summary[m.start():]
    return summary.rstrip() + "\n\n" + _FE_BLOCK + "\n"

# detect a generic opener we want to avoid (and also remove the duplicate generic para)
_GENERIC_OPENERS = re.compile(r"(?i)\b(the partner will|this document|this project|the engagement will)\b")

def _build_client_opener(schema: dict) -> str:
    client = (schema.get("client") or "the client").strip()
    site   = primary_site_line(schema) or "(site)"
    # Use a safe, polished objective (do NOT echo raw scope which can be oddly cased)
    objective = "installing, cabling, labelling and powering-on network equipment"
    return (
        f"WWT will assist {client} in {objective} at {site}, "
        f"delivering a clean physical install aligned to site policies and agreed change windows."
    )

def _ensure_client_specific_opener(summary: str, schema: dict) -> str:
    """
    Ensure the first paragraph after '### Project Summary' is a natural, client-specific opener,
    and remove any duplicate generic '...require the physical installation...' paragraph.
    Also inject if the first paragraph starts with **Primary site:** or doesn't mention the client.
    """
    if not summary: return summary
    m = re.search(r"(?im)^###\s*Project Summary\s*$", summary)
    if not m: return summary
    head_end = m.end()
    before = summary[:head_end]
    after  = summary[head_end:].lstrip()

    # First paragraph boundaries
    para_end = re.search(r"\n\s*\n", after)
    first_para = after[:para_end.start()] if para_end else after

    client = (schema.get("client") or "").strip()
    first_starts_with_primary = re.match(r"^\s*\*\*Primary site:\*\*", first_para or "", flags=re.I) is not None
    client_missing = bool(client) and (client.lower() not in (first_para or "")[:200].lower())

    needs_inject = (not first_para.strip()) or _GENERIC_OPENERS.search(first_para) or first_starts_with_primary or client_missing
    if needs_inject:
        opener = _build_client_opener(schema)
        after = f"\n\n{opener}\n\n" + after.lstrip()

    # Remove any paragraph that contains 'require the physical installation'
    after = re.sub(
        r"(?ims)^\s*.*require the physical installation.*?(?:\n\s*\n|$)",
        "",
        after,
    )

    return before + after

def _normalise_heading_levels_to_h3(text: str) -> str:
    """Convert any #### Heading to ### Heading for consistency."""
    if not text: return text or ""
    return re.sub(r"(?m)^\s*#{4,}\s+", "### ", text)

def _split_sections(text: str):
    """
    Return list of (heading, body) for ### sections.
    """
    if not text: return []
    parts = re.split(r"(?im)^\s*###\s+", text.strip())
    out = []
    for p in parts:
        if not p.strip(): continue
        lines = p.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        out.append((heading, body))
    return out

def _rebuild_sections(sections):
    """Rebuild markdown from list of (heading, body)."""
    buff = []
    for h, b in sections:
        buff.append(f"### {h}\n{b}".rstrip())
    return "\n\n".join(buff).strip()

def _filter_and_order_task_sections(tasks_md: str, schema: dict) -> str:
    """
    Keep ONLY the allowed headings in _TASK_ORDER (in that order). If any are missing,
    create them with defaults from schema. Drop everything else.
    """
    tasks_md = _normalise_heading_levels_to_h3(tasks_md or "")
    found = {h: "" for h in _TASK_ORDER}

    # Harvest existing sections that we allow
    for h, body in _split_sections(tasks_md):
        if h in found:
            found[h] = body.strip()

    # Build defaults
    prereqs = found["Client Prerequisites"] or _bullets_block(schema.get("prerequisites"))
    oos     = found["Out of Scope"]         or _bullets_block(schema.get("out_of_scope"))

    defaults = {
        "Site Survey (Site Visit 1)": found["Site Survey (Site Visit 1)"] or "- (none provided)",
        "Installation (Site Visit 2)": found["Installation (Site Visit 2)"] or "- (none provided)",
        "Client Prerequisites": prereqs or "- (none provided)",
        "Out of Scope": oos or "- (none provided)",
    }

    ordered = []
    for h in _TASK_ORDER:
        body = (found[h] or defaults[h]).strip()
        ordered.append((h, body))

    return _rebuild_sections(ordered)

def _replace_bom_tokens(summary: str, schema: dict) -> str:
    """
    Replace any BOM token variant the model may emit:
      '{{BOM_TABLE}}', '{BOM_TABLE}', '(BOM_TABLE)', or bare 'BOM_TABLE'
    """
    bom_md = bom_table_markdown(schema, include_rack_unit=True)
    if not bom_md:
        return re.sub(r"\{?\(?\s*BOM_TABLE\s*\)?\}?", "_(No BOM items provided)_", summary)
    replacement = f"\n\n{bom_md}\n\n"  # ensure blank lines for clean rendering
    return re.sub(r"\{?\(?\s*BOM_TABLE\s*\)?\}?", replacement, summary)

def _strip_orphan_blockquotes(text: str) -> str:
    """Remove lines that are just a lone '>' to avoid stray quote blocks."""
    if not text: return text or ""
    return re.sub(r"(?m)^\s*>\s*$", "", text).strip()

def _tidy_key_tasks(summary: str) -> str:
    """Remove a dangling '- Key tasks:' label but keep the bullets that follow."""
    if not summary: return summary or ""
    return re.sub(r"(?mi)^\s*[-*]\s*Key tasks:\s*\n", "", summary)

# --- main -------------------------------------------------------------------

def post_process(schema: dict, result: dict) -> dict:
    summary = (result.get("summary") or "").strip()
    tasks   = (result.get("tasks") or "").strip()

    # Placeholder replacements
    client = (schema.get("client") or "(Client)").strip()
    site   = primary_site_line(schema) or "(TBD)"
    summary = summary.replace("{{CLIENT}}", client)
    summary = summary.replace("{{PRIMARY_SITE}}", site)

    # Ensure natural opener + remove generic duplicate
    summary = _ensure_client_specific_opener(summary, schema)

    # Ensure Field Engineer tools block exists
    summary = _ensure_field_engineer_block(summary)

    # Replace any BOM token variant (or append a standard section if token missing)
    if re.search(r"\bBOM_TABLE\b", summary):
        summary = _replace_bom_tokens(summary, schema)
    else:
        bom_md = bom_table_markdown(schema, include_rack_unit=True)
        if bom_md and not re.search(r"(?i)\bBill of Materials\b", summary):
            summary += f"\n\n### Bill of Materials\n\n{bom_md}\n\n"

    # Ensure Device totals line appears once (and replace placeholder if present)
    counts = (schema.get("counts") or {})
    device_totals = (
        f"**Device totals:** {counts.get('aps_ordered') or 'TBD'} APs ordered — "
        f"{counts.get('aps_to_mount') or 'TBD'} to be mounted; "
        f"{counts.get('devices_total') or 'TBD'} total devices."
    )
    if "{{DEVICE_TOTALS_SENTENCE}}" in summary:
        summary = summary.replace("{{DEVICE_TOTALS_SENTENCE}}", device_totals)
    elif not re.search(r"\*\*Device totals:\*\*", summary, flags=re.I):
        summary += f"\n\n{device_totals}"

    # Final format cleanups
    summary = _checkboxes_to_bullets(summary)
    summary = _tidy_key_tasks(summary)
    summary = _strip_orphan_blockquotes(summary)

    tasks   = _checkboxes_to_bullets(tasks)
    tasks   = _filter_and_order_task_sections(tasks, schema)

    result["summary"] = summary.strip()
    result["tasks"]   = tasks.strip()
    return result
