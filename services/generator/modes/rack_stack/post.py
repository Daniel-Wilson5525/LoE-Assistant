# services/generator/modes/rack_stack/post.py
import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

# --- constants --------------------------------------------------------------

# Default Field Engineer tools (always inject if missing)
_FE_BLOCK = (
    "**Field Engineer is expected to provide industry-standard tools including but not limited to:**\n"
    "- Basic Hand Tools\n"
    "- Labelling Printer\n"
    "- Ladder\n"
    "- Laptop with connecting cable"
)

# Match any reasonable variant of the BOM token:
# '{{BOM_TABLE}}', '{BOM_TABLE}', '(BOM_TABLE)', or bare 'BOM_TABLE'
_BOM_TOKEN_RE = re.compile(r"\{?\(?\s*BOM_TABLE\s*\)?\}?")

# Regex for markdown tables (header + separator + one or more data rows)
_TABLE_BLOCK_RE = re.compile(
    r"(?ms)^\|.*\n\|[^\n]*\n(?:\|.*\n)+"
)

# Checkbox bullets like '- [ ] Task' / '* [x] Done'
_CHECKBOX_RE = re.compile(r"^(?P<prefix>\s*[-*•o])\s*\[(?: |x|X)\]\s*", flags=re.M)

# Default Site Survey bullets (used if the model leaves the section empty / '- (none provided)')
_SITE_SURVEY_DEFAULT = [
    "Site Survey may need to be scheduled up to four (4) weeks before installation as appropriate.",
    "Verify that the Customer has a suitable environment for the equipment to be installed, housed, and maintained.",
    "Perform a physical onsite Site Survey at each Customer Site (walk-through with Customer and WWT engineer).",
    "Cover in the Site Survey report:",
    "  - Confirmation of health and safety requirements.",
    "  - Confirmation of access for the site.",
    "  - Confirmation of data provisions for the site.",
    "  - Confirmation of electrical provision for the site, including sufficient receptacles available on PDU.",
    "  - Confirmation of cabling provision for the site.",
    "  - Confirmation of space availability and condition.",
    "  - Confirmation of environmental conditions for the site.",
    "  - Photographs of key aspects of the site, if allowed.",
    "Complete and submit the Site Survey Report.",
]

# Default Installation bullets
_INSTALL_DEFAULT = [
    "WWT will perform the following tasks:",
    "Receive and inventory the equipment.",
    "Check boxes for any damage or triggered tilts and advise the Customer of any faults.",
    "Unbox equipment and check for physical damage.",
    "Validate equipment model and quantity against delivery order or Bill-of-Material (BOM).",
    "Document loose accessories/modules (module cards and SFP/QSFP transceivers) and quantity.",
    "Verify customer-specific asset tag and device hostname label before installation (Customer assists to print/label when required).",
    "Install modules/SFPs as per build document and cabling matrix.",
    "Perform the physical installation and cabling of equipment as per rack elevation diagram and cabling plan.",
    "Patch network cables per cabling matrix, when required.",
    "Print and label power cords, when required.",
    "Install earthing cable for all large equipment, when required.",
    "Connect power cords as per power mapping.",
    "Power on devices for green-light check, including sub-modules (line card/supervisor/power supplies); notify PM of any faults.",
    "If RMA/DOA is required, assist to replace equipment (may require a visit outside of project timeframe depending on OEM parts availability; handled via Change Order process).",
    "Review validation of connectivity with Customer.",
    "Complete Customer-provided QA checklist to ensure installation aligns with Customer build documents.",
    "Validate task completion and receive sign-off.",
    "Engineers can take photographs of devices in the rack (if allowed in the data centre).",
    "Flatten boxes and place at Customer-designated disposal area.",
]

# Default Post-Installation bullets
_POST_INSTALL_DEFAULT = [
    "Support initial go-live period for the newly installed equipment.",
    "Assist with basic connectivity and reachability checks with the customer team.",
    "Provide ad-hoc troubleshooting for hardware or cabling issues identified immediately after install.",
    "Capture any defects or follow-up actions and hand them back to the project manager.",
]

# Default Client Prerequisites bullets
_PREREQS_DEFAULT = [
    "Client to provide SFP slotting matrix.",
    "Client to provide rack layout matrix.",
    "Client to provide cabling matrix.",
    "Client to provide network cables.",
    "Client to provide power mapping matrix.",
]

# Default Out of Scope bullets
_OUT_OF_SCOPE_DEFAULT = [
    "Site remediation including, but not limited to, provisioning of rack space, cooling, and power; and troubleshooting of carrier circuits.",
    "Device wiping or erasing of any operating system (OS) and/or configurations.",
    "Testing of, or access to, existing installed devices.",
    "Configuration development or applying configurations to any devices.",
    "Lift requirements: no work that requires the use of lifts.",
    "Equipment removal: no removal of decommissioned gear from the project site.",
    "Electric power installations: no work that requires electric power installations.",
    "Conduit installation: no cable installations requiring conduit.",
    "Rack/cabinet installations: no rack or cabinet installations.",
    "No materials are provided as part of this engagement, including small consumables such as zip ties and Velcro.",
    "Server lifts: no server lifts are provided.",
    "Field terminations are limited to continuity testing only; no cable certifications.",
    "Certification/Validation: no certification or validation for copper or fibre cables.",
]

# --- basic helpers ----------------------------------------------------------


def _checkboxes_to_bullets(text: str) -> str:
    """Turn '- [ ] Task' / '* [x] Done' into '- Task' / '* Done'."""
    if not text:
        return text or ""
    return _CHECKBOX_RE.sub(lambda m: f"{m.group('prefix')} ", text)


def _strip_orphan_blockquotes(text: str) -> str:
    """Remove lines that are just a lone '>' to avoid stray quote blocks."""
    if not text:
        return text or ""
    return re.sub(r"(?m)^\s*>\s*$", "", text).strip()


def _strip_leading_project_tasks_heading(text: str) -> str:
    """Remove a top-level '### Project Tasks' heading from the tasks block, if present."""
    if not text:
        return text or ""
    return re.sub(
        r"(?im)^\s*###\s*Project Tasks\s*(?:\n\s*)?",
        "",
        text,
        count=1,
    ).lstrip()


def _strip_site_specific_tbd(tasks: str) -> str:
    """Remove vague 'Site-specific tasks TBD' bullets."""
    if not tasks:
        return tasks or ""
    return re.sub(
        r"(?mi)^\s*[-*]\s*Site-specific tasks TBD\.?\s*$",
        "",
        tasks,
    ).strip()


# --- BOM handling -----------------------------------------------------------


def _site_label(site: dict, idx: int) -> str:
    """Build a human-readable site label: 'Name — Address' or fallback to 'Site N'."""
    name = (site.get("name") or "").strip()
    addr = (site.get("address") or "").strip()
    if name and addr:
        return f"{name} — {addr}"
    if name:
        return name
    if addr:
        return addr
    return f"Site {idx}"


def _multi_site_bom_markdown(schema: dict, include_rack_unit: bool = True) -> str:
    """
    Build BOM tables per site.

    For each site with any BOM/optics rows, emit:

      #### <Site label>
      | Part Number | Description | Qty | Type | [Rack Unit] |
      ...

    If no site has any valid rows, return "".
    """
    sites = [s for s in (schema.get("sites") or []) if isinstance(s, dict)]
    if not sites:
        return ""

    blocks = []
    for idx, site in enumerate(sites, start=1):
        # Combine bom + optics_bom for the site
        rows = []
        for r in (site.get("bom") or []):
            if isinstance(r, dict):
                rows.append(r)
        for r in (site.get("optics_bom") or []):
            if isinstance(r, dict):
                rows.append(r)

        if not rows:
            continue

        temp_schema = {"bom": rows}
        table_md = bom_table_markdown(temp_schema, include_rack_unit=include_rack_unit)
        if not table_md:
            continue

        label = _site_label(site, idx)
        blocks.append(f"#### {label}\n\n{table_md}")

    return "\n\n".join(blocks)


def _replace_bom_tokens(summary: str, schema: dict) -> str:
    """
    Replace any BOM token variant the model may emit with per-site BOM tables.
    """
    bom_md = _multi_site_bom_markdown(schema, include_rack_unit=True)
    if not bom_md:
        # No BOM rows at any site -> generic placeholder
        return _BOM_TOKEN_RE.sub("_(No BOM items provided)_", summary)

    replacement = f"\n\n{bom_md}\n\n"
    return _BOM_TOKEN_RE.sub(replacement, summary)


def _ensure_field_engineer_block(summary: str) -> str:
    """Ensure the FE tools block appears in the summary once."""
    if not summary:
        return summary
    if re.search(r"(?i)field\s+engineer.*tools", summary):
        return summary

    # If we see any BOM_TABLE token, inject FE block immediately before it.
    if _BOM_TOKEN_RE.search(summary):
        return _BOM_TOKEN_RE.sub(
            _FE_BLOCK + "\n\nBOM_TABLE",
            summary,
            count=1,
        )

    # Else insert before device totals line, if present
    m = re.search(r"\*\*Device totals:\*\*", summary)
    if m:
        return (
            summary[: m.start()].rstrip()
            + "\n\n"
            + _FE_BLOCK
            + "\n\n"
            + summary[m.start() :]
        )

    # Otherwise append at the end of the summary
    return summary.rstrip() + "\n\n" + _FE_BLOCK + "\n"


# --- Site Overview table in summary ----------------------------------------


def _phase_cell_for_site(site: dict, tasks_key: str, flag_key: str | None = None) -> str:
    """
    Decide the 'Site Survey' / 'Installation' / 'Post-Installation' cell value for a site.

    Priority:
      1. site["tasks"][tasks_key]["include"] -> '✔' or '✘'
      2. site[flag_key] (e.g. 'survey_in_scope') -> '✔' or '✘'
      3. else -> 'TBD'
    """
    tasks = (site.get("tasks") or {})
    phase = (tasks.get(tasks_key) or {})
    include = phase.get("include")

    if isinstance(include, bool):
        return "✔" if include else "✘"

    if flag_key is not None and flag_key in site:
        val = site.get(flag_key)
        if isinstance(val, bool):
            return "✔" if val else "✘"

    return "TBD"


def _generate_site_overview_table(schema: dict) -> str:
    """
    Build the Site Overview table:

    | Site | Address | Site Role | Site Survey | Installation | Post-Installation | Notes |

    using the 'sites' array from the schema.
    """
    sites = [s for s in (schema.get("sites") or []) if isinstance(s, dict)]
    if not sites:
        return ""

    header = (
        "| Site | Address | Site Role | Site Survey | Installation | Post-Installation | Notes |\n"
        "|------|---------|-----------|-------------|--------------|-------------------|-------|"
    )

    rows = []
    for idx, site in enumerate(sites, start=1):
        name = (site.get("name") or f"Site {idx}").strip()
        addr = (site.get("address") or "TBD").strip()
        role = (site.get("role") or "TBD").strip()
        notes = (site.get("notes") or "TBD").strip()

        site_survey_cell = _phase_cell_for_site(site, "site_survey", "survey_in_scope")
        install_cell = _phase_cell_for_site(site, "installation", "install_in_scope")
        post_cell = _phase_cell_for_site(site, "post_install", "post_in_scope")

        rows.append(
            f"| {name} | {addr} | {role or 'TBD'} | "
            f"{site_survey_cell} | {install_cell} | {post_cell} | {notes or 'TBD'} |"
        )

    return header + "\n" + "\n".join(rows)


def _inject_site_overview_table(summary: str, schema: dict) -> str:
    """
    Ensure the Project Summary section contains exactly one Site Overview table
    generated from the schema, and remove any model-generated tables in that region.
    """
    if not summary:
        return summary

    # Locate "### Project Summary"
    m_summary = re.search(r"(?im)^###\s*Project Summary\s*$", summary)
    if not m_summary:
        return summary

    head_end = m_summary.end()

    # Locate "### Bill of Materials" to bound the region
    m_bom = re.search(r"(?im)^###\s*Bill of Materials\b", summary)
    mid_end = m_bom.start() if m_bom else len(summary)

    before = summary[:head_end]
    mid = summary[head_end:mid_end]
    after = summary[mid_end:]

    mid = mid.lstrip("\n")

    # 1) Strip any markdown tables in the Project Summary region
    mid_no_tables = _TABLE_BLOCK_RE.sub("", mid).strip("\n")

    # 2) Split mid_no_tables into first paragraph + rest (blank line as separator)
    para_match = re.search(r"\n\s*\n", mid_no_tables)
    if para_match:
        first_para = mid_no_tables[: para_match.start()].strip()
        rest = mid_no_tables[para_match.end() :].lstrip("\n")
    else:
        first_para = mid_no_tables.strip()
        rest = ""

    # 3) Generate the canonical Site Overview table
    table_md = _generate_site_overview_table(schema)

    if not table_md:
        new_mid = mid_no_tables
    else:
        parts = [p for p in [first_para, table_md, rest] if p]
        new_mid = "\n\n".join(parts)

    new_mid = new_mid.strip("\n")

    # Ensure there is a blank line before whatever comes after (e.g. '### Bill of Materials')
    if after and not after.startswith("\n\n"):
        after = "\n\n" + after.lstrip("\n")

    return before + "\n" + new_mid + after


# --- Summary key-tasks pruning ---------------------------------------------


def _tidy_key_tasks(summary: str) -> str:
    """Remove a dangling '- Key tasks:' label but keep the bullets that follow."""
    if not summary:
        return summary or ""
    return re.sub(r"(?mi)^\s*[-*]\s*Key tasks:\s*\n", "", summary)


def _prune_key_tasks_block(summary: str, schema: dict) -> str:
    """
    Make the 'Key tasks overview' list in the summary match what is actually
    in scope in global_scope.

    - If site_survey include=False -> drop any 'Site survey' bullet.
    - If post_install include=False -> drop any 'Post-install' / 'Post-installation' bullets.
    Everything else is left as-is.
    """
    if not summary:
        return summary or ""

    m = re.search(
        r"(?mi)^(?P<header>\s*[-*]\s*Key tasks[^\n]*)(?P<body>(?:\n[ \t]*[-*]\s+.*)*)",
        summary,
    )
    if not m:
        return summary

    header = m.group("header")
    body = m.group("body") or ""

    lines = body.splitlines()
    if not lines:
        return summary

    global_scope = schema.get("global_scope") or {}
    site_survey_in_scope = bool(global_scope.get("site_survey", {}).get("include"))
    post_install_in_scope = bool(global_scope.get("post_install", {}).get("include"))

    kept_bullets = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            kept_bullets.append(line)
            continue

        text_l = stripped[1:].strip().lower()  # text after '-'
        if ("site survey" in text_l) and not site_survey_in_scope:
            continue
        if ("post-install" in text_l or "post installation" in text_l) and not post_install_in_scope:
            continue

        kept_bullets.append(line)

    # If we somehow removed everything, just drop the whole block
    if not kept_bullets:
        return summary[: m.start()] + summary[m.end() :]

    new_block = header + "\n" + "\n".join(kept_bullets)
    return summary[: m.start()] + new_block + summary[m.end() :]


# --- Section splitting / defaults for phases --------------------------------


def _split_h3_sections(text: str):
    """
    Split markdown into a list of (heading, body) where heading is the text
    after '### ' and body is everything until the next '### '.
    """
    if not text:
        return []

    parts = re.split(r"(?im)^###\s+", text.strip())
    sections = []

    for p in parts:
        if not p.strip():
            continue
        lines = p.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip("\n")
        sections.append((heading, body))

    return sections


def _rebuild_h3_sections(sections) -> str:
    """Rebuild markdown from list of (heading, body)."""
    blocks = []
    for h, b in sections:
        if b:
            blocks.append(f"### {h}\n{b}".rstrip())
        else:
            blocks.append(f"### {h}".rstrip())
    return "\n\n".join(blocks).strip()


def _apply_phase_defaults(tasks: str) -> str:
    """
    For each key phase section, if the body is empty or '- (none provided)',
    replace it with the standard default bullets so we always get a 'chunky'
    rack & stack LoE by default.
    """
    if not tasks:
        return tasks or ""

    sections = _split_h3_sections(tasks)
    if not sections:
        return tasks

    default_map = {
        "Site Survey — Activities Delivered Across Applicable Sites": _SITE_SURVEY_DEFAULT,
        "Installation — Activities Delivered Across Applicable Sites": _INSTALL_DEFAULT,
        "Post-Installation — Activities Delivered Across Applicable Sites": _POST_INSTALL_DEFAULT,
        "Client Prerequisites": _PREREQS_DEFAULT,
        "Out of Scope": _OUT_OF_SCOPE_DEFAULT,
    }

    patched = []
    for heading, body in sections:
        cleaned = (body or "").strip()

        if heading in default_map and (not cleaned or cleaned == "- (none provided)"):
            lines = []
            for line in default_map[heading]:
                if line.startswith("  -"):
                    lines.append(line)
                elif line.startswith("- "):
                    lines.append(line)
                else:
                    lines.append(f"- {line}")
            body = "\n".join(lines).strip()

        patched.append((heading, body))

    return _rebuild_h3_sections(patched)


# --- Site Work Packages auto-fill ------------------------------------------


def _build_site_card_body(schema: dict, site_idx: int) -> str:
    """
    Build a default body for a site card when the model left it empty.
    Uses survey/install/post flags from the schema to describe scope.
    """
    sites = schema.get("sites") or []
    if not isinstance(site_idx, int) or site_idx < 0 or site_idx >= len(sites):
        # Fallback generic text if index is out of range
        return (
            "At this site, WWT will deliver the in-scope rack & stack activities "
            "as defined in this Level of Effort.\n\n"
            "- Coordinate rack locations and power feeds with the customer.\n"
            "- Validate onsite readiness (space, power, cooling and access) before installation."
        )

    site = sites[site_idx] or {}

    survey = bool(site.get("survey_in_scope"))
    install = bool(site.get("install_in_scope"))
    post = bool(site.get("post_in_scope"))

    phases = []
    if survey:
        phases.append("site survey")
    if install:
        phases.append("installation")
    if post:
        phases.append("post-installation support")

    if phases:
        if len(phases) == 1:
            phases_str = phases[0]
        elif len(phases) == 2:
            phases_str = " and ".join(phases)
        else:
            phases_str = ", ".join(phases[:-1]) + f" and {phases[-1]}"
        scope_sentence = (
            f"At this site, WWT will deliver {phases_str} activities as defined in this Level of Effort."
        )
    else:
        scope_sentence = (
            "At this site, WWT will deliver the in-scope rack & stack activities "
            "as defined in this Level of Effort."
        )

    bullets = [
        "- Coordinate rack locations, power feeds and patching with the customer team.",
        "- Validate onsite readiness (space, power, cooling and access) before installation.",
    ]

    return scope_sentence + "\n\n" + "\n".join(bullets)


def _ensure_site_work_packages_have_content(tasks: str, schema: dict) -> str:
    """
    Ensure each '#### 📍 ...' site card under
    '### Site Work Packages by Location' has some body content.

    If the model left a site card empty, inject a default scope sentence
    and 1–2 bullets based on schema.
    """
    if not tasks:
        return tasks or ""

    # Find the Site Work Packages section
    m = re.search(r"(?im)^###\s+Site Work Packages by Location\s*$", tasks)
    if not m:
        return tasks

    start = m.end()
    # Find the next '### ' heading after this section (phase sections)
    m_next = re.search(r"(?im)^###\s+", tasks[start:])
    end = start + m_next.start() if m_next else len(tasks)

    before = tasks[:start]
    block = tasks[start:end]
    after = tasks[end:]

    # Split block into [pre, heading1, body1, heading2, body2, ...]
    parts = re.split(r"(?m)^(####\s+📍[^\n]*\n)", block)
    if len(parts) <= 1:
        return tasks  # nothing to do

    rebuilt = parts[0]
    site_idx = 0

    for i in range(1, len(parts), 2):
        heading = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""

        if heading.lstrip().startswith("#### 📍"):
            if not body.strip():
                # Inject default content for this site index
                body = "\n" + _build_site_card_body(schema, site_idx) + "\n\n"
            site_idx += 1

        rebuilt += heading + body

    return before + rebuilt + after


# --- main -------------------------------------------------------------------


def post_process(schema: dict, result: dict) -> dict:
    summary = (result.get("summary") or "").strip()
    tasks = (result.get("tasks") or "").strip()

    # Placeholder replacements
    client = (schema.get("client") or "(Client)").strip()
    site = primary_site_line(schema) or "(TBD)"
    summary = summary.replace("{{CLIENT}}", client)
    summary = summary.replace("{{PRIMARY_SITE}}", site)

    # Inject canonical Site Overview table based on schema,
    # and strip any model-generated site tables in the Project Summary region.
    summary = _inject_site_overview_table(summary, schema)

    # Ensure Field Engineer tools block exists
    summary = _ensure_field_engineer_block(summary)

    # Replace any BOM token variant (or append a standard section if token missing)
    if _BOM_TOKEN_RE.search(summary):
        summary = _replace_bom_tokens(summary, schema)
    else:
        bom_md = _multi_site_bom_markdown(schema, include_rack_unit=True)
        if bom_md and not re.search(r"(?i)\bBill of Materials\b", summary):
            summary += f"\n\n### Bill of Materials by Site\n\n{bom_md}\n\n"

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

    # Make sure 'Key tasks overview' (if present) reflects what is actually in scope
    summary = _prune_key_tasks_block(summary, schema)

    # Final format cleanups for summary
    summary = _checkboxes_to_bullets(summary)
    summary = _tidy_key_tasks(summary)
    summary = _strip_orphan_blockquotes(summary)

    # ---- TASKS PIPELINE (light touch: keep model structure) ----
    tasks = _checkboxes_to_bullets(tasks)
    tasks = _strip_leading_project_tasks_heading(tasks or "")
    tasks = _strip_site_specific_tbd(tasks or "")
    tasks = _ensure_site_work_packages_have_content(tasks or "", schema)
    # If the model left any phase sections empty / '- (none provided)', fill with defaults
    tasks = _apply_phase_defaults(tasks or "")
    tasks = _strip_orphan_blockquotes(tasks or "")

    result["summary"] = summary.strip()
    result["tasks"] = tasks.strip()
    return result
