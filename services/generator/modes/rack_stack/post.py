# services/generator/modes/rack_stack/post.py
import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

# =============================================================================
# Constants
# =============================================================================

_FE_BLOCK = (
    "**Field Engineer is expected to provide industry-standard tools including but not limited to:**\n"
    "- Basic Hand Tools\n"
    "- Labelling Printer\n"
    "- Ladder\n"
    "- Laptop with connecting cable"
)

_BOM_TOKEN_RE = re.compile(r"\{?\(?\s*BOM_TABLE\s*\)?\}?")

# Markdown table block (header + separator + one or more rows)
_TABLE_BLOCK_RE = re.compile(r"(?ms)^\|.*\n\|[^\n]*\n(?:\|.*\n)+")

# Checkboxes like '- [ ] Task' / '* [x] Done'
_CHECKBOX_RE = re.compile(r"^(?P<prefix>\s*[-*•o])\s*\[(?: |x|X)\]\s*", flags=re.M)

# Detect the Site Overview table header specifically
_SITE_OVERVIEW_HEADER_RE = re.compile(
    r"(?m)^\|\s*Site\s*\|\s*Address\s*\|\s*Site Role\s*\|\s*Site Survey\s*\|\s*Installation\s*\|\s*Post-Installation\s*\|\s*Notes\s*\|\s*$"
)

# =============================================================================
# Default content (system-owned phase sections)
# =============================================================================

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

_POST_INSTALL_DEFAULT = [
    "Support initial go-live period for the newly installed equipment.",
    "Assist with basic connectivity and reachability checks with the customer team.",
    "Provide ad-hoc troubleshooting for hardware or cabling issues identified immediately after install.",
    "Capture any defects or follow-up actions and hand them back to the project manager.",
]

_PREREQS_DEFAULT = [
    "Client to provide SFP slotting matrix.",
    "Client to provide rack layout matrix.",
    "Client to provide cabling matrix.",
    "Client to provide network cables.",
    "Client to provide power mapping matrix.",
]

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

_PHASES = {
    "site_survey": {
        "canonical_heading": "Site Survey — Activities Delivered Across Applicable Sites",
        "defaults": _SITE_SURVEY_DEFAULT,
    },
    "installation": {
        "canonical_heading": "Installation — Activities Delivered Across Applicable Sites",
        "defaults": _INSTALL_DEFAULT,
        "intro_unbullet": "WWT will perform the following tasks:",
    },
    "post_install": {
        "canonical_heading": "Post-Installation — Activities Delivered Across Applicable Sites",
        "defaults": _POST_INSTALL_DEFAULT,
    },
    "client_prereqs": {
        "canonical_heading": "Client Prerequisites",
        "defaults": _PREREQS_DEFAULT,
    },
    "out_of_scope": {
        "canonical_heading": "Out of Scope",
        "defaults": _OUT_OF_SCOPE_DEFAULT,
    },
}

# =============================================================================
# Generic text cleanup helpers
# =============================================================================

def _checkboxes_to_bullets(text: str) -> str:
    if not text:
        return text or ""
    return _CHECKBOX_RE.sub(lambda m: f"{m.group('prefix')} ", text)

def _strip_orphan_blockquotes(text: str) -> str:
    if not text:
        return text or ""
    return re.sub(r"(?m)^\s*>\s*$", "", text).strip()

def _strip_leading_project_tasks_heading(text: str) -> str:
    if not text:
        return text or ""
    return re.sub(r"(?im)^\s*###\s*Project Tasks\s*(?:\n\s*)?", "", text, count=1).lstrip()

def _strip_site_specific_tbd(tasks: str) -> str:
    if not tasks:
        return tasks or ""
    return re.sub(r"(?mi)^\s*[-*]\s*Site-specific tasks TBD\.?\s*$", "", tasks).strip()

# =============================================================================
# BOM handling
# =============================================================================

def _site_label(site: dict, idx: int) -> str:
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
    sites = [s for s in (schema.get("sites") or []) if isinstance(s, dict)]
    if not sites:
        return ""

    blocks = []
    for idx, site in enumerate(sites, start=1):
        rows = []
        for r in (site.get("bom") or []):
            if isinstance(r, dict):
                rows.append(r)
        for r in (site.get("optics_bom") or []):
            if isinstance(r, dict):
                rows.append(r)

        if not rows:
            continue

        table_md = bom_table_markdown({"bom": rows}, include_rack_unit=include_rack_unit)
        if not table_md:
            continue

        blocks.append(f"#### {_site_label(site, idx)}\n\n{table_md}")

    return "\n\n".join(blocks)

def _replace_bom_tokens(summary: str, schema: dict) -> str:
    bom_md = _multi_site_bom_markdown(schema, include_rack_unit=True)
    if not bom_md:
        return _BOM_TOKEN_RE.sub("_(No BOM items provided)_", summary)
    return _BOM_TOKEN_RE.sub(f"\n\n{bom_md}\n\n", summary)

def _ensure_field_engineer_block(summary: str) -> str:
    if not summary:
        return summary
    if re.search(r"(?i)field\s+engineer.*tools", summary):
        return summary

    if _BOM_TOKEN_RE.search(summary):
        return _BOM_TOKEN_RE.sub(_FE_BLOCK + "\n\nBOM_TABLE", summary, count=1)

    m = re.search(r"\*\*Device totals:\*\*", summary)
    if m:
        return summary[: m.start()].rstrip() + "\n\n" + _FE_BLOCK + "\n\n" + summary[m.start():]

    return summary.rstrip() + "\n\n" + _FE_BLOCK + "\n"

# =============================================================================
# Site overview table generation + de-dupe
# =============================================================================

def _phase_cell_for_site(site: dict, tasks_key: str, flag_key: str | None = None) -> str:
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
            f"| {name} | {addr} | {role or 'TBD'} | {site_survey_cell} | {install_cell} | {post_cell} | {notes or 'TBD'} |"
        )

    return header + "\n" + "\n".join(rows)

def _inject_site_overview_table(summary: str, schema: dict) -> str:
    """
    Ensure the Project Summary region contains exactly one Site Overview table:
    - Remove any model tables within Project Summary region
    - Insert canonical table based on schema
    """
    if not summary:
        return summary

    m_summary = re.search(r"(?im)^###\s*Project Summary\s*$", summary)
    if not m_summary:
        return summary

    head_end = m_summary.end()

    m_bom = re.search(r"(?im)^###\s*Bill of Materials\b", summary)
    mid_end = m_bom.start() if m_bom else len(summary)

    before = summary[:head_end]
    mid = summary[head_end:mid_end]
    after = summary[mid_end:]

    mid = mid.lstrip("\n")

    # Strip any markdown tables in the Project Summary region
    mid_no_tables = _TABLE_BLOCK_RE.sub("", mid).strip("\n")

    # Split into first paragraph + rest
    para_match = re.search(r"\n\s*\n", mid_no_tables)
    if para_match:
        first_para = mid_no_tables[:para_match.start()].strip()
        rest = mid_no_tables[para_match.end():].lstrip("\n")
    else:
        first_para = mid_no_tables.strip()
        rest = ""

    table_md = _generate_site_overview_table(schema)
    parts = [p for p in [first_para, table_md, rest] if p]
    new_mid = "\n\n".join(parts).strip("\n")

    if after and not after.startswith("\n\n"):
        after = "\n\n" + after.lstrip("\n")

    return before + "\n" + new_mid + after

def _dedupe_site_overview_tables(summary: str) -> str:
    """
    Keep only the first Site Overview table anywhere in the summary.
    Removes any duplicates (e.g., model adds a second one later).
    """
    if not summary:
        return summary or ""

    matches = list(_SITE_OVERVIEW_HEADER_RE.finditer(summary))
    if len(matches) <= 1:
        return summary

    def _remove_table_at(text: str, start_idx: int) -> str:
        tail = text[start_idx:]
        m = _TABLE_BLOCK_RE.search(tail)
        if not m:
            return text
        return text[:start_idx] + tail[m.end():].lstrip("\n")

    for m in reversed(matches[1:]):
        summary = _remove_table_at(summary, m.start())

    return summary

# =============================================================================
# Summary tidy helpers
# =============================================================================

def _tidy_key_tasks(summary: str) -> str:
    if not summary:
        return summary or ""
    return re.sub(r"(?mi)^\s*[-*]\s*Key tasks:\s*\n", "", summary)

def _prune_key_tasks_block(summary: str, schema: dict) -> str:
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

    kept = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            kept.append(line)
            continue

        text_l = stripped[1:].strip().lower()
        if ("site survey" in text_l) and not site_survey_in_scope:
            continue
        if ("post-install" in text_l or "post installation" in text_l) and not post_install_in_scope:
            continue

        kept.append(line)

    if not kept:
        return summary[:m.start()] + summary[m.end():]

    new_block = header + "\n" + "\n".join(kept)
    return summary[:m.start()] + new_block + summary[m.end():]

# =============================================================================
# Markdown section splitting
# =============================================================================

def _split_h3_sections(text: str):
    """
    Split markdown into list of (heading, body) for '### ' headings.
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
    blocks = []
    for h, b in sections:
        blocks.append(f"### {h}\n{b}".rstrip() if b else f"### {h}".rstrip())
    return "\n\n".join(blocks).strip()

# =============================================================================
# Phase sections: system-owned, bullet-only merge
# =============================================================================

def _heading_key(h: str) -> str:
    if not h:
        return ""
    x = h.strip().lower()
    x = re.sub(r"[:\s]+$", "", x)
    x = x.replace("—", "-").replace("–", "-")
    x = re.sub(r"\s+", " ", x)

    if x.startswith("site survey - activities delivered across"):
        return "site_survey"
    if x.startswith("installation - activities delivered across"):
        return "installation"
    if x.startswith("post-installation - activities delivered across") or x.startswith("post installation - activities delivered across"):
        return "post_install"
    if x.startswith("client prerequisites"):
        return "client_prereqs"
    if x.startswith("out of scope"):
        return "out_of_scope"
    return ""

def _bullet_lines_only(body: str) -> list[str]:
    """
    Keep ONLY markdown bullet lines; discard prose completely.
    Accepts '- ', '* ', and '  - '.
    """
    if not body:
        return []

    PLACEHOLDERS = {
        "(none provided)",
        "- (none provided)",
        "none provided",
        "- none provided",
    }

    out = []
    for raw in str(body).splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue

        # sub-bullet
        if line.startswith("  - "):
            txt = line[4:].strip()
            if txt.lower() in {p.strip("- ").lower() for p in PLACEHOLDERS}:
                continue
            out.append("  - " + txt)
            continue

        s = line.lstrip()
        if s.startswith(("- ", "* ")):
            txt = s[2:].strip()
            if txt.lower() in {p.strip("- ").lower() for p in PLACEHOLDERS}:
                continue
            out.append("- " + txt)

    return out


def _normalize_default_lines(default_lines: list[str]) -> list[str]:
    """
    Defaults -> bullet list (preserve sub-bullets). Plain lines become bullets.
    """
    out = []
    for line in (default_lines or []):
        if line is None:
            continue
        line = str(line).strip()
        if not line:
            continue

        if line.startswith("  - "):
            out.append("  - " + line[4:].strip())
        else:
            # everything else is a bullet at top level
            out.append("- " + (line[2:].strip() if line.startswith("- ") else line))
    return out

def _merge_bullet_blocks(default_lines: list[str], model_body: str) -> str:
    base = _normalize_default_lines(default_lines)
    model_bullets = _bullet_lines_only(model_body)

    seen = set()
    merged = []

    def key(line: str) -> str:
        return line.strip().lower()

    for line in base + model_bullets:
        k = key(line)
        if k and k not in seen:
            merged.append(line)
            seen.add(k)

    return "\n".join(merged).strip()

def _unbullet_intro_line(body: str, intro: str) -> str:
    """
    If the first non-empty line is '- <intro>', convert it to a plain line.
    """
    if not body:
        return body or ""

    lines = body.splitlines()
    first_idx = next((i for i, ln in enumerate(lines) if ln.strip()), None)
    if first_idx is None:
        return body

    first = lines[first_idx].strip()
    if first.lower() == f"- {intro}".lower():
        lines[first_idx] = intro
        if first_idx + 1 < len(lines) and lines[first_idx + 1].lstrip().startswith(("-", "*")):
            lines.insert(first_idx + 1, "")
        return "\n".join(lines).strip()

    return body

def _apply_phase_defaults(tasks: str) -> str:
    """
    System-owned phase sections:
    - Always include defaults
    - Only allow model *bullet* additions (no prose)
    - Normalize headings so small variations don't bypass enforcement
    """
    if not tasks:
        return tasks or ""

    sections = _split_h3_sections(tasks)
    if not sections:
        return tasks

    patched = []
    for heading, body in sections:
        k = _heading_key(heading)
        if k in _PHASES:
            info = _PHASES[k]
            merged_body = _merge_bullet_blocks(info["defaults"], body or "")
            intro = info.get("intro_unbullet")
            if intro:
                merged_body = _unbullet_intro_line(merged_body, intro)
            patched.append((info["canonical_heading"], merged_body))
        else:
            patched.append((heading, body))

    return _rebuild_h3_sections(patched)

# =============================================================================
# Site work packages: ensure each site card has content
# =============================================================================

def _build_site_card_body(schema: dict, site_idx: int) -> str:
    sites = schema.get("sites") or []
    if not isinstance(site_idx, int) or site_idx < 0 or site_idx >= len(sites):
        return (
            "At this site, WWT will deliver the in-scope rack & stack activities as defined in this Level of Effort.\n\n"
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
        scope_sentence = f"At this site, WWT will deliver {phases_str} activities as defined in this Level of Effort."
    else:
        scope_sentence = "At this site, WWT will deliver the in-scope rack & stack activities as defined in this Level of Effort."

    bullets = [
        "- Coordinate rack locations, power feeds and patching with the customer team.",
        "- Validate onsite readiness (space, power, cooling and access) before installation.",
    ]
    return scope_sentence + "\n\n" + "\n".join(bullets)

def _ensure_site_work_packages_have_content(tasks: str, schema: dict) -> str:
    if not tasks:
        return tasks or ""

    m = re.search(r"(?im)^###\s+Site Work Packages by Location\s*$", tasks)
    if not m:
        return tasks

    start = m.end()
    m_next = re.search(r"(?im)^###\s+", tasks[start:])
    end = start + m_next.start() if m_next else len(tasks)

    before = tasks[:start]
    block = tasks[start:end]
    after = tasks[end:]

    parts = re.split(r"(?m)^(####\s+📍[^\n]*\n)", block)
    if len(parts) <= 1:
        return tasks

    rebuilt = parts[0]
    site_idx = 0

    for i in range(1, len(parts), 2):
        heading = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""

        if heading.lstrip().startswith("#### 📍") and not body.strip():
            body = "\n" + _build_site_card_body(schema, site_idx) + "\n\n"
        if heading.lstrip().startswith("#### 📍"):
            site_idx += 1

        rebuilt += heading + body

    return before + rebuilt + after

# =============================================================================
# Main
# =============================================================================

def post_process(schema: dict, result: dict) -> dict:
    summary = (result.get("summary") or "").strip()
    tasks = (result.get("tasks") or "").strip()

    # Placeholders
    client = (schema.get("client") or "(Client)").strip()
    site = primary_site_line(schema) or "(TBD)"
    summary = summary.replace("{{CLIENT}}", client).replace("{{PRIMARY_SITE}}", site)

    # Summary: canonical site table + de-dupe any duplicates
    summary = _inject_site_overview_table(summary, schema)
    summary = _dedupe_site_overview_tables(summary)

    # Summary: FE tools, BOM, device totals
    summary = _ensure_field_engineer_block(summary)

    if _BOM_TOKEN_RE.search(summary):
        summary = _replace_bom_tokens(summary, schema)
    else:
        bom_md = _multi_site_bom_markdown(schema, include_rack_unit=True)
        if bom_md and not re.search(r"(?i)\bBill of Materials\b", summary):
            summary += f"\n\n### Bill of Materials by Site\n\n{bom_md}\n\n"

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

    # Summary: prune key tasks + cleanup
    summary = _prune_key_tasks_block(summary, schema)
    summary = _checkboxes_to_bullets(summary)
    summary = _tidy_key_tasks(summary)
    summary = _strip_orphan_blockquotes(summary)
    summary = _dedupe_site_overview_tables(summary)  # safe to run twice

    # Tasks: cleanup + ensure site cards + enforce phase defaults
    tasks = _checkboxes_to_bullets(tasks)
    tasks = _strip_leading_project_tasks_heading(tasks)
    tasks = _strip_site_specific_tbd(tasks)
    tasks = _ensure_site_work_packages_have_content(tasks, schema)
    tasks = _apply_phase_defaults(tasks)
    tasks = _strip_orphan_blockquotes(tasks)

    result["summary"] = summary.strip()
    result["tasks"] = tasks.strip()
    return result
