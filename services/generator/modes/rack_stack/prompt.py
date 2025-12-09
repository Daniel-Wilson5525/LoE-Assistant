from textwrap import dedent
from services.prompt_loader import load_prompt_file
from services.generator.shared.text import bullet_block
from services.generator.shared.derive import sum_bom_qty, derive_mounting_qty_from_notes


def _primary_site(schema: dict) -> str:
    for s in (schema.get("sites") or []):
        name = (s.get("name") or "").strip()
        addr = (s.get("address") or "").strip()
        if name and addr:
            return f"{name} — {addr}"
        if addr:
            return addr
        if name:
            return name
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
    sites         = (schema.get("sites") or [])

    # Simple human-readable site list to help the model
    site_lines = []
    for s in sites:
        name = (s.get("name") or "TBD").strip()
        addr = (s.get("address") or "TBD").strip()
        role = (s.get("role") or "").strip()
        phases = []
        if s.get("survey_in_scope"):
            phases.append("Site Survey")
        if s.get("install_in_scope"):
            phases.append("Installation")
        if s.get("post_in_scope"):
            phases.append("Post-Installation")
        phases_str = ", ".join(phases) if phases else "TBD"
        site_lines.append(f"{name} — {addr} (Role: {role or 'TBD'}, Phases: {phases_str})")

    sites_block = bullet_block(site_lines) if site_lines else "- (no sites provided)"

    return dedent(f"""
    You are a project engineer writing a precise, professional, client-facing Level of Effort (LOE) for a Rack & Stack engagement.

    IMPORTANT – BOM HANDLING
    - When you see the token {{BOM_TABLE}} in the GOLDEN EXAMPLE, keep it exactly as-is in your output.
    - Do NOT modify, expand, or remove {{BOM_TABLE}}.
    - The backend will replace this token with the final Bill of Materials table.

    Use the structured context below and the GOLDEN EXAMPLE as a reference for tone and layout, but you MUST follow the OUTPUT CONTRACT and FORMAT RULES from the system prompt.

    ## Structured context
    Client: {schema.get('client','') or '(Client)'}
    Primary site: {_primary_site(schema)}
    Device totals line to use verbatim:
    {device_totals_line}
    Total ordered devices (from BOM): {total_ordered if total_ordered else 'TBD'}
    Approximate mounting quantity (APs): {mounting_qty}

    Sites and phases:
    {sites_block}

    Client prerequisites (hints):
    {bullet_block(prereqs) or '- (none provided)'}

    Out of scope (hints):
    {bullet_block(exclusions) or '- (none provided)'}

    ## GOLDEN EXAMPLE (style and structure reference ONLY — do NOT copy content verbatim)
    {golden}

    ## OUTPUT CONTRACT
    - Return JSON ONLY with keys:
        "summary" (string) and "tasks" (string).
    - Do NOT include any extra keys.
    - Do NOT include any text before or after the JSON.
    - Do NOT wrap the JSON in code fences.

    You MUST:
    - Produce exactly ONE concise project summary paragraph in "summary" (do not duplicate or restate it).
    - In "summary":
        - Follow the SUMMARY SECTION RULES from the system prompt.
        - Include a Site Overview table covering ALL sites in the schema.
        - Include the required device totals sentence exactly as given above.
    - In "tasks":
        - Begin with the heading: "### Site Work Packages by Location".
        - Under it, create one site card per site using headings of the form:
            "#### 📍 {{Site Name}} — {{Address}}"
          and list only site-specific tasks under each.
        - After the site cards, include the following sections in this order:
            "### Site Survey — Activities Delivered Across Applicable Sites"
            "### Installation — Activities Delivered Across Applicable Sites"
            "### Post-Installation — Activities Delivered Across Applicable Sites"
            "### Client Prerequisites"
            "### Out of Scope"
        - Always include "### Client Prerequisites" and "### Out of Scope", even if you only write "- (none provided)".

    You MUST NOT:
    - Use the word "Generic" in any heading or content.
    - Reproduce the GOLDEN EXAMPLE text word-for-word.
    - Invent sites, devices, quantities, or phases that are not supported by the schema.
    - Create additional top-level sections beyond those described above.
    """).strip()
