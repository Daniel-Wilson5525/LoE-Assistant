# services/generator/modes/rack_stack/post.py
import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

# Convert GitHub-style checkboxes to plain bullets
_CHECKBOX_RE = re.compile(
    r"^(?P<prefix>\s*[-*•o])\s*\[(?: |x|X)\]\s*", flags=re.M
)

def _checkboxes_to_bullets(text: str) -> str:
    """
    Turn lines like '- [ ] Task' or '* [x] Done' into '- Task' / '* Done'.
    Leaves normal bullets unchanged.
    """
    if not text:
        return text or ""
    return _CHECKBOX_RE.sub(lambda m: f"{m.group('prefix')} ", text)

# detect a generic opener we want to avoid
_GENERIC_OPENERS = re.compile(
    r"(?i)\b(the partner will|this document|this project|the engagement will)\b"
)

def _build_client_opener(schema: dict) -> str:
    client = (schema.get("client") or "the client").strip()
    site   = primary_site_line(schema) or "(site)"
    # prefer scope → project_name → service
    scope  = (schema.get("scope") or "").strip()
    proj   = (schema.get("project_name") or "").strip()
    svc    = (schema.get("service") or "Rack & Stack").strip()
    objective = scope or proj or f"{svc} installation"
    return (
        f"WWT will assist {client} in {objective} at {site}, "
        f"delivering a clean physical install aligned to site policies and agreed change windows."
    )

def _ensure_client_specific_opener(summary: str, schema: dict) -> str:
    """
    Ensure the first paragraph after '### Project Summary' begins with a natural,
    client-specific sentence. If missing or overly generic, prepend one.
    """
    if not summary:
        return summary
    # split on heading
    m = re.search(r"(?im)^###\s*Project Summary\s*$", summary)
    if not m:
        return summary
    head_end = m.end()
    before = summary[:head_end]
    after  = summary[head_end:].lstrip()

    # get first paragraph
    para_end = re.search(r"\n\s*\n", after)
    first_para = after[:para_end.start()] if para_end else after

    if not first_para.strip() or _GENERIC_OPENERS.search(first_para):
        opener = _build_client_opener(schema)
        injected = f"\n\n{opener}\n\n" + after.lstrip()
        return before + injected
    return summary

def post_process(schema: dict, result: dict) -> dict:
    summary = (result.get("summary") or "").strip()
    tasks   = (result.get("tasks") or "").strip()

    # Placeholder replacements
    client = (schema.get("client") or "(Client)").strip()
    site   = primary_site_line(schema) or "(TBD)"
    summary = summary.replace("{{CLIENT}}", client)
    summary = summary.replace("{{PRIMARY_SITE}}", site)

    # Ensure a natural client-specific opening sentence exists
    summary = _ensure_client_specific_opener(summary, schema)

    # BOM replacement: if template left {{BOM_TABLE}}, replace with actual table; else append if missing
    bom_md = bom_table_markdown(schema)
    if "{{BOM_TABLE}}" in summary:
        summary = summary.replace("{{BOM_TABLE}}", bom_md or "_(No BOM items provided)_")
    else:
        if bom_md and not re.search(r"(?i)\bBill of Materials\b", summary):
            summary += f"\n\n### Bill of Materials\n{bom_md}"

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

    # ---- Normalize list formatting: checkboxes -> bullets ----
    summary = _checkboxes_to_bullets(summary)
    tasks   = _checkboxes_to_bullets(tasks)

    # Remove any stray "Wave Installation Plan" block (legacy guard)
    tasks = re.sub(r"(?s)###\s*Wave Installation Plan.*$", "", tasks).strip()

    result["summary"] = summary
    result["tasks"]   = tasks
    return result
