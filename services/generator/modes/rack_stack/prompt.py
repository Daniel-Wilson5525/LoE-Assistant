# services/generator/modes/rack_stack/prompt.py
from textwrap import dedent
from services.prompt_loader import load_prompt_file
from services.generator.shared.text import bullet_block
from services.generator.shared.derive import sum_bom_qty, derive_mounting_qty_from_notes

def _primary_site(schema: dict) -> str:
    for s in (schema.get("sites") or []):
        name = (s.get("name") or "").strip()
        addr = (s.get("address") or "").strip()
        if name and addr: return f"{name} — {addr}"
        if addr: return addr
        if name: return name
    return "(TBD)"

def build_prompt(schema: dict) -> str:
    golden = load_prompt_file("services/generator/modes/rack_stack", "golden.md") or ""

    counts = schema.get("counts") or {}
    device_totals_line = (
        f"**Device totals:** {counts.get('aps_ordered') or 'TBD'} APs ordered — "
        f"{counts.get('aps_to_mount') or 'TBD'} to be mounted; "
        f"{counts.get('devices_total') or 'TBD'} total devices."
    )

    notes_raw     = schema.get("notes_raw", "") or ""
    total_ordered = sum_bom_qty(schema)
    mounting_qty  = counts.get("aps_to_mount") or derive_mounting_qty_from_notes(notes_raw) or "TBD"

    exclusions    = (schema.get("out_of_scope") or [])
    prereqs       = (schema.get("prerequisites") or [])

    return dedent(f"""
    You are a delivery engineer. Start from the GOLDEN TEMPLATE below and make **minimal edits**:
    - Keep the golden headings and order.
    - Replace placeholders:
      • {{CLIENT}} with the 'client' field or '(Client)'.
      • {{PRIMARY_SITE}} with the primary site line (Name — Address) or '(TBD)'.
      • {{BOM_TABLE}} keep as the exact token; do not remove. The backend will replace it.
      • {{DEVICE_TOTALS_SENTENCE}} replace with the exact sentence provided below.
    - Use the GOLDEN TEMPLATE as the baseline for every section.
    - Preserve all checklist items by default.
    - Only remove individual bullets that are explicitly contradicted or marked redundant in the schema context.
    - If the schema lists a few extra prerequisites or out-of-scope items, append them rather than deleting existing bullets.
    - Do NOT shorten or rewrite sections arbitrarily — keep the structure, depth, and phrasing of the golden template.
    - Do NOT invent new sections; keep to the template only.


    ## Context
    Client: {schema.get('client','') or '(Client)'}
    Primary site: {_primary_site(schema)}
    Device totals line to use verbatim:
    {device_totals_line}
    Total ordered devices (from BOM): {total_ordered if total_ordered else 'TBD'}
    Client prerequisites (hints): {bullet_block(prereqs) or '- (none)'}
    Out of scope (hints): {bullet_block(exclusions) or '- (none)'}

    ### GOLDEN TEMPLATE (use as your base; then minimally edit per rules)
    {golden}

    ## Output contract
    Return JSON ONLY with keys:
      "summary" (string) — begin with "### Project Summary"
      "tasks"   (string) — begin with "### Project Tasks"
    """).strip()
