# services/generator/modes/rack_stack/prompt.py
from textwrap import dedent
from services.prompt_loader import load_prompt_file
from services.generator.shared.text import bullet_block
from services.generator.shared.tables import wave_table_markdown
from services.generator.shared.derive import (
    sum_bom_qty,
    derive_mounting_qty_from_notes,
    extract_phase_block,
)

def _lines_from_bom(schema: dict) -> str:
    items = []
    for r in (schema.get("bom") or []):
        if not ((r.get("model") or r.get("type")) and (r.get("qty") not in (None, "", 0))):
            continue
        t = (r.get("type") or "").strip() or "Device"
        m = (r.get("model") or "").strip()
        q = r.get("qty")
        note = (r.get("notes") or "").strip()
        line = f"- {q} × {t}{(' – ' + m) if m else ''}"
        if note:
            line += f" ({note})"
        items.append(line)
    return "\n".join(items) if items else "• (No BOM items listed)"

def _sites_block(schema: dict) -> str:
    sites = schema.get("sites") or []
    lines = [
        f"- {s.get('name','').strip()} — {s.get('address','').strip()}".strip(" — ")
        for s in sites if (s.get("name") or s.get("address"))
    ]
    return "\n".join(lines) or "• (No sites listed)"

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

    rollout = schema.get("rollout") or {}
    visits_caps = schema.get("visits_caps", {}) or {}
    counts = schema.get("counts", {}) or {}

    device_totals_line = (
        f"**Device totals:** {counts.get('aps_ordered') or 'TBD'} APs ordered — "
        f"{counts.get('aps_to_mount') or 'TBD'} to be mounted; "
        f"{counts.get('devices_total') or 'TBD'} total devices."
    )

    notes_raw     = schema.get("notes_raw", "") or ""
    total_ordered = sum_bom_qty(schema)
    mounting_qty  = counts.get("aps_to_mount") or derive_mounting_qty_from_notes(notes_raw) or "TBD"
    wave_table_md = wave_table_markdown(schema)
    phase_block   = extract_phase_block(notes_raw)

    exclusions  = (schema.get("out_of_scope") or [])
    hints_text  = "\n".join(
        (schema.get("assumptions") or [])
        + (schema.get("prerequisites") or [])
        + (schema.get("constraints") or [])
        + [notes_raw]
    )

    sites_block   = _sites_block(schema)
    bom_lines     = _lines_from_bom(schema)

    rollout_lines = []
    if rollout.get("waves"):           rollout_lines.append(f"Waves/sequence: {rollout['waves']}")
    if rollout.get("floors"):          rollout_lines.append(f"Floors/areas: {rollout['floors']}")
    if rollout.get("ooh_windows"):     rollout_lines.append(f"OOH windows: {rollout['ooh_windows']}")
    if rollout.get("change_approvals"):rollout_lines.append(f"Change approvals: {rollout['change_approvals']}")
    rollout_block = "\n".join(f"- {x}" for x in rollout_lines) or "- (Rollout details TBD with client)"

    governance = schema.get("governance") or {}
    phase_or_wave = ("### Wave Installation Plan\n" + wave_table_md) if wave_table_md else (
        "### Phase breakdown (as provided)\n" + phase_block if phase_block else "")

    return dedent(f"""
    You are a delivery engineer. Start from the GOLDEN TEMPLATE below and produce a Rack & Stack LOE as **minimal edits**.
    Use the BOM as the single source of truth (ignore any legacy 'devices' input).
                  
    ### Tone & opener rules (important)
    - Open the **Project Summary** with a single client-specific sentence that names **{{CLIENT}}**, the **primary site**, and the **objective** in natural language.
      Example: "WWT will assist {{CLIENT}} in installing and labelling network equipment at {{PRIMARY_SITE}} to support the Datacenter Rack & Stack Upgrade."
    - Avoid generic phrasing like "The partner will perform..." as your first sentence.
    - Keep the rest concise and professional.

    ## Project context (structured)
    Client: {schema.get('client','')}
    Primary site: {_primary_site(schema)}
    Project name: {schema.get('project_name','')}
    Requested service: {schema.get('service','')}
    Environment: {schema.get('environment','')}
    Timeline/change window: {schema.get('timeline','')}
    Scope/objective: {schema.get('scope','')}

    ### Sites
    {sites_block}

    ### Devices / BOM
    (BOM_TABLE)

    ### Derived counts
    {device_totals_line}
    {"- Total ordered devices (from BOM): " + str(total_ordered) if total_ordered else "- (no derived counts)"}

    ### Governance & Communications
    - Project Manager: {governance.get('pm') or 'TBD'}
    - Comms channels: {governance.get('comms_channels') or 'Teams / Email'}
    - Escalation path: {governance.get('escalation') or 'Partner PM + Client PM'}

    ### Rollout Plan
    {rollout_block}

    ### Visit Caps
    Up to **{visits_caps.get('install_max_visits') or 'TBD'}** install visits and **{visits_caps.get('post_deploy_max_visits') or 'TBD'}** post-deployment survey visit(s). Site Survey window up to **{visits_caps.get('site_survey_window_weeks') or 'TBD'}** weeks pre-install.

    ### Phase/Wave info (optional)
    {phase_or_wave}

    ### Exclusions (from schema.out_of_scope)
    {bullet_block(exclusions) or '- (none provided)'}

    ### Client-provided hints (free text – use to prune/mark tasks)
    {hints_text[:1200]}

    ### GOLDEN TEMPLATE (use as your base; then minimally edit per rules)
    {golden}

    ### Placeholder values to apply
    - CLIENT = {schema.get('client') or '(Client)'}
    - PRIMARY_SITE = {_primary_site(schema)}
    - DEVICE_TOTALS_SENTENCE = {device_totals_line}
    - MOUNTING_REQUIREMENT = {mounting_qty} device(s)  # if referenced

    ## Output contract
    Return JSON ONLY with keys:
      "summary" (string) — begin with "### Project Summary"
      "tasks"   (string) — begin with "### Project Tasks"
      "open_questions" (array of 4–8 strings).
    """).strip()
