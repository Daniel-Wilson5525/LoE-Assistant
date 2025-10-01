from textwrap import dedent
from services.generator.shared.style_examples import load_style_examples
from services.generator.shared.text import bullet_block
from services.generator.shared.tables import wave_table_markdown
from services.generator.shared.derive import sum_bom_qty, derive_mounting_qty_from_notes, extract_phase_block

def _lines_from_devices(schema: dict) -> str:
    items = []
    bom_rows = [r for r in (schema.get("bom") or []) if (r.get("model") or r.get("type")) and (r.get("qty") not in (None,"",0))]
    if bom_rows:
        for r in bom_rows:
            t = (r.get("type") or "").strip() or "Device"
            m = (r.get("model") or "").strip()
            q = r.get("qty")
            note = (r.get("notes") or "").strip()
            line = f"- {q} × {t}{(' – ' + m) if m else ''}"
            if note: line += f" ({note})"
            items.append(line)
    else:
        for d in (schema.get("devices") or []):
            t = (d.get("type") or "").strip()
            q = d.get("qty")
            if t and q not in (None,"",0): items.append(f"- {q} × {t}")
    return "\n".join(items) if items else "• (No devices listed)"

def build_prompt(schema: dict) -> str:
    examples = load_style_examples(schema.get("service",""))
    sites = schema.get("sites") or []
    site_lines = [f"- {s.get('name','').strip()} — {s.get('address','').strip()}".strip(" — ")
                  for s in sites if (s.get("name") or s.get("address"))]
    sites_block = "\n".join(site_lines) or "• (No sites listed)"

    staging = schema.get("staging") or {}
    staging_flags = []
    if staging.get("ic_used"): staging_flags.append("Use Integration Centre")
    if staging.get("doa"): staging_flags.append("DOA validation")
    if staging.get("burn_in"): staging_flags.append("24h burn-in")
    staging_details = []
    if isinstance(staging.get("labelling"), str) and staging["labelling"].strip():
        staging_details.append(f"Labelling: {staging['labelling'].strip()}")
    if isinstance(staging.get("packing"), str) and staging["packing"].strip():
        staging_details.append(f"Packing/shipping: {staging['packing'].strip()}")

    rollout = schema.get("rollout") or {}
    rollout_lines = []
    if rollout.get("waves"):           rollout_lines.append(f"Waves/sequence: {rollout['waves']}")
    if rollout.get("floors"):          rollout_lines.append(f"Floors/areas: {rollout['floors']}")
    if rollout.get("ooh_windows"):     rollout_lines.append(f"OOH windows: {rollout['ooh_windows']}")
    if rollout.get("change_approvals"):rollout_lines.append(f"Change approvals: {rollout['change_approvals']}")
    rollout_block = "\n".join(f"- {x}" for x in rollout_lines) or "- (Rollout details TBD with client)"

    visits_caps = schema.get("visits_caps", {}) or {}
    counts = schema.get("counts", {}) or {}
    device_totals_line = (
        f"**Device totals:** {counts.get('aps_ordered') or 'TBD'} APs ordered — "
        f"{counts.get('aps_to_mount') or 'TBD'} to be mounted; "
        f"{counts.get('devices_total') or 'TBD'} total devices."
    )

    brackets = schema.get("brackets") or []
    brackets_block = bullet_block([f"{b.get('model_pattern','')}: {b.get('bracket_name','')}"
                                   for b in brackets if (b.get('model_pattern') or b.get('bracket_name'))]) or "- (TBD)"

    wave_table_md = wave_table_markdown(schema)
    notes_raw = schema.get("notes_raw","") or ""
    total_ordered = sum_bom_qty(schema)
    mounting_qty  = derive_mounting_qty_from_notes(notes_raw)
    derived_block = []
    if total_ordered: derived_block.append(f"- Total ordered devices (from BOM/devices): {total_ordered}")
    if mounting_qty:  derived_block.append(f"- Devices to be mounted (from notes): {mounting_qty}")
    phase_block = extract_phase_block(notes_raw)

    acceptance = ((schema.get("handover") or {}).get("acceptance_criteria") or "").strip()

    return dedent(f"""
    You are a project engineer writing a professional, precise Level of Effort (LOE).

    ### Style reference (do not copy verbatim; mirror tone/structure)
    {examples or '(no example provided)'}

    ## Context (structured)
    Client: {schema.get('client','')}
    Project name: {schema.get('project_name','')}
    Requested service: {schema.get('service','')}
    Environment: {schema.get('environment','')}
    Timeline/change window: {schema.get('timeline','')}
    Scope/objective: {schema.get('scope','')}

    ### Sites
    {sites_block}

    ### Devices / BOM
    {_lines_from_devices(schema)}

    ### Derived counts
    **Device totals:** {counts.get('aps_ordered') or 'TBD'} APs ordered — {counts.get('aps_to_mount') or 'TBD'} to be mounted; {counts.get('devices_total') or 'TBD'} total devices.
    {("\n".join(derived_block) if derived_block else "- (no derived counts)")}

    ### Logistics & Staging
    - Flags: {', '.join(staging_flags) if staging_flags else '(none)'}
    {bullet_block(staging_details)}

    ### Rollout Plan
    {rollout_block}

    ### Visit Caps
    Up to **{visits_caps.get('install_max_visits') or 'TBD'}** install visits and **{visits_caps.get('post_deploy_max_visits') or 'TBD'}** post-deployment survey visit(s). Site Survey window up to **{visits_caps.get('site_survey_window_weeks') or 'TBD'}** weeks pre-install.

    - Mounting requirement: **{counts.get('aps_to_mount') or 'TBD'} APs** (spares not mounted).

    ### Brackets / Mounts
    {brackets_block}

    {("### Wave Installation Plan\n" + wave_table_md) if wave_table_md else ("### Phase breakdown (as provided)\n" + phase_block if phase_block else "")}

    ### Governance & Communications
    - Project Manager: {(schema.get('governance') or {}).get('pm') or 'TBD (HSBC/WWT)'}
    - Comms channels: {(schema.get('governance') or {}).get('comms_channels') or 'Teams / Email'}
    - Escalation path: {(schema.get('governance') or {}).get('escalation') or 'WWT PM + HSBC PM'}

    ### Prerequisites (client actions)
    {bullet_block(schema.get('prerequisites')) or '- (none provided)'}

    ### Assumptions
    {bullet_block(schema.get('assumptions')) or '- (none provided)'}

    ### Out of Scope
    {bullet_block(schema.get('out_of_scope')) or '- (none provided)'}

    ### Deliverables
    {bullet_block(schema.get('deliverables')) or '- (none provided)'}

    ### Constraints / special notes
    {bullet_block(schema.get('constraints')) or '- (none provided)'}

    ## Task (follow these formatting rules strictly)
     1) **PROJECT SUMMARY** (Markdown)
        - 6–9 sentences.
        - Include 3–6 “Key tasks” bullets.
        - Include a small BOM table (Type | Model | Qty).
        - You MUST include this exact sentence (verbatim):
          {device_totals_line}
        - Use only '### ' headings (no '#').
     2) **PROJECT TASKS** (Markdown)
        - Use '### ' section headings exactly in this order:
          1) Site Survey (Visit 1)
          2) Pre-checks
          3) Logistics & Staging
          4) Installation (Visit 2)
          5) Registration & Bring-Up
          6) Validation / Post-Deployment
          7) Handover & Documentation
          8) Out of Scope
        - Use GFM checkboxes ('- [ ] ') for every line item.
        - Include model-specific bracket/mount steps where applicable.
     3) **Open Questions**
        - Provide 4–8 targeted questions for missing details (OOH/CAB, photo policy, spares, storage/lifts/permits, etc.).
 
     Return JSON ONLY with keys: "summary", "tasks", "open_questions".
    """).strip()
