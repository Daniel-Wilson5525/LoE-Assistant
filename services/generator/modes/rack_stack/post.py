# services/generator/modes/rack_stack/post.py
import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

_MINI_BOM_RE = re.compile(
    r"(?ims)^\s*\|\s*Type\s*\|\s*Model\s*\|\s*Qty\s*\|\s*$"  # header
    r".+?"                                                    # table body
    r"(?=^\S|\Z)"                                             # stop at next non-table section
)


_BULLET_RE = re.compile(r"^(?:\s*[-*•o]\s+)(?!\[[ xX]\])", flags=re.M)

def _bullets_to_checkboxes(text: str) -> str:
    return _BULLET_RE.sub("- [ ] ", text or "")

def post_process(schema: dict, result: dict) -> dict:
    summary = (result.get("summary") or "").strip()
    tasks   = (result.get("tasks") or "").strip()

    # Placeholder replacements
    client = (schema.get("client") or "(Client)").strip()
    site   = primary_site_line(schema) or "(TBD)"

    summary = summary.replace("{{CLIENT}}", client)
    summary = summary.replace("{{PRIMARY_SITE}}", site)
    # Remove any small auto-generated Type/Model/Qty tables from AI output
    summary = _MINI_BOM_RE.sub("", summary).strip()


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

    # Normalise bullets -> checkboxes in both sections
    summary = _bullets_to_checkboxes(summary)
    tasks   = _bullets_to_checkboxes(tasks)

    # Remove any stray "Wave Installation Plan" block (legacy guard)
    tasks = re.sub(r"(?s)###\s*Wave Installation Plan.*$", "", tasks).strip()

    result["summary"] = summary
    result["tasks"]   = tasks
    return result
