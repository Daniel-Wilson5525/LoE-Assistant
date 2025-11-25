# services/generator/modes/rack_stack/post.py
import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

# --- constants --------------------------------------------------------------

# The ONLY task sections we want to keep (in this order)
_TASK_ORDER = [
    "Site Survey (Site Visit 1)",
    "Installation (Site Visit 2)",
    "Post-Installation Services",
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
    if not text:
        return text or ""
    return _CHECKBOX_RE.sub(lambda m: f"{m.group('prefix')} ", text)


def _bullets_block(items):
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    return "\n".join(f"- {i}" for i in items) if items else "- (none provided)"


def _site_label(site: dict, idx: int) -> str:
    """
    Build a human-readable site label: 'Name — Address' or fallback to 'Site N'.
    """
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

    For each site with any BOM/optics rows (with qty > 0), emit:

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
        # Combine BOM + optics_bom for the site
        rows = []
        for r in (site.get("bom") or []):
            if isinstance(r, dict):
                rows.append(r)
        for r in (site.get("optics_bom") or []):
            if isinstance(r, dict):
                rows.append(r)

        if not rows:
            continue

        # Reuse existing table builder by passing a temp schema with just "bom"
        temp_schema = {"bom": rows}
        table_md = bom_table_markdown(temp_schema, include_rack_unit=include_rack_unit)
        if not table_md:
            continue

        label = _site_label(site, idx)
        blocks.append(f"#### {label}\n\n{table_md}")

    return "\n\n".join(blocks)


def _ensure_field_engineer_block(summary: str) -> str:
    """Ensure the FE tools block appears in the summary once."""
    if not summary:
        return summary
    if re.search(r"(?i)field\s+engineer.*tools", summary):
        return summary
    # Insert FE block just before BOM_TABLE or, if absent, before the device totals line; else append.
    if re.search(r"\bBOM_TABLE\b", summary):
        return re.sub(r"\bBOM_TABLE\b", _FE_BLOCK + "\n\nBOM_TABLE", summary, count=1)
    m = re.search(r"\*\*Device totals:\*\*", summary)
    if m:
        return (
            summary[: m.start()].rstrip()
            + "\n\n"
            + _FE_BLOCK
            + "\n\n"
            + summary[m.start() :]
        )
    return summary.rstrip() + "\n\n" + _FE_BLOCK + "\n"


# detect a generic opener we want to avoid (and also remove the duplicate generic para)
_GENERIC_OPENERS = re.compile(
    r"(?i)\b(the partner will|this document|this project|the engagement will)\b"
)


def _build_client_opener(schema: dict) -> str:
    """
    Build a natural, client-specific one/two sentence opener for the Project Summary.

    Example vibe:
      "HSBC requires on-site installation services for Juniper wireless AP hardware across four floors
       within the Huanpu Science and Technology Industrial Park campus during a weekend in October."
    """
    client = (schema.get("client") or "the client").strip()
    site = primary_site_line(schema) or "(site)"
    service = (schema.get("service") or "rack & stack installation services").strip()
    scope = (schema.get("scope") or "").strip()
    timeline = (schema.get("timeline") or "").strip()

    # First sentence: what / where / when
    if scope:
        first = f"{client} require {service} to support {scope.lower()} at {site}"
    else:
        first = f"{client} require {service} at {site}"

    if timeline:
        first += f", targeted for {timeline.lower()}"

    first += "."

    # Second sentence: what WWT actually does
    second = (
        "WWT will provide on-site engineering to install, cable, label and power-on the equipment, "
        "delivering a clean physical install aligned to site policies and agreed change windows."
    )

    return f"{first} {second}"


def _inject_opener_after_heading(summary: str, schema: dict) -> str:
    """
    Hard guarantee: ensure a client/site opener appears immediately after
    '### Project Summary', even if earlier heuristics didn't fire.

    We consider it already present if the standard phrase
    'WWT will provide on-site engineering' is near the top.
    """
    if not summary:
        return summary

    # If we've already injected this style of opener, don't add another
    if "WWT will provide on-site engineering" in summary[:400]:
        return summary

    m = re.search(r"(?im)^###\s*Project Summary\s*$", summary)
    if not m:
        return summary

    opener = _build_client_opener(schema)
    head_end = m.end()
    before = summary[:head_end]
    after = summary[head_end:].lstrip()

    return f"{before}\n\n{opener}\n\n{after}".rstrip()


def _ensure_client_specific_opener(summary: str, schema: dict) -> str:
    """
    Ensure the first paragraph after '### Project Summary' is a natural, client-specific opener,
    and remove any duplicate generic '...require the physical installation...' paragraph.

    Also:
      - If the first paragraph starts with **Site address:**, inject the opener above it
        so you don't just jump straight into address/BOM.
    """
    if not summary:
        return summary

    m = re.search(r"(?im)^###\s*Project Summary\s*$", summary)
    if not m:
        return summary

    head_end = m.end()
    before = summary[:head_end]
    after = summary[head_end:].lstrip()

    # First paragraph boundaries
    para_end_match = re.search(r"\n\s*\n", after)
    if para_end_match:
        first_para = after[: para_end_match.start()]
        rest = after[para_end_match.end() :].lstrip()
    else:
        first_para = after
        rest = ""

    client = (schema.get("client") or "").strip()

    first_starts_with_primary = re.match(
        r"^\s*\*\*Primary site:\*\*", first_para or "", flags=re.I
    ) is not None
    first_starts_with_site_addr = re.match(
        r"^\s*\*\*Site address:\*\*", first_para or "", flags=re.I
    ) is not None

    client_missing = bool(client) and (
        client.lower() not in (first_para or "")[:200].lower()
    )

    needs_inject = (
        (not first_para.strip())
        or _GENERIC_OPENERS.search(first_para or "")
        or first_starts_with_primary
        or first_starts_with_site_addr  # address-first → inject opener
        or client_missing
    )

    if needs_inject:
        opener = _build_client_opener(schema)
        # Put opener before whatever was there as first paragraph
        if first_para.strip():
            after = f"\n\n{opener}\n\n{first_para.strip()}\n\n{rest}".strip()
        else:
            after = f"\n\n{opener}\n\n{rest}".strip()
    else:
        after = first_para + ("\n\n" + rest if rest else "")

    # Remove any paragraph that contains 'require the physical installation'
    after = re.sub(
        r"(?ims)^\s*.*require the physical installation.*?(?:\n\s*\n|$)",
        "",
        after,
    ).lstrip()

    return before + "\n" + after.strip()


def _normalise_heading_levels_to_h3(text: str) -> str:
    """Convert any #### Heading to ### Heading for consistency."""
    if not text:
        return text or ""
    return re.sub(r"(?m)^\s*#{4,}\s+", "### ", text)


def _split_sections(text: str):
    """
    Return list of (heading, body) for ### sections.
    """
    if not text:
        return []
    parts = re.split(r"(?im)^\s*###\s+", text.strip())
    out = []
    for p in parts:
        if not p.strip():
            continue
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

def _phase_in_scope(schema: dict, site_phase_key: str, global_key: str | None = None) -> bool:
    """
    Return True if this phase is in scope anywhere:
      - global_scope[global_key].include
      - OR any site.tasks[site_phase_key].include
    """
    global_scope = schema.get("global_scope") or {}
    gkey = global_key or site_phase_key
    g_phase = (global_scope.get(gkey) or {})
    if g_phase.get("include") is True:
        return True

    for site in (schema.get("sites") or []):
        if not isinstance(site, dict):
            continue
        tasks = (site.get("tasks") or {}).get(site_phase_key) or {}
        if tasks.get("include") is True:
            return True

    return False


def _filter_and_order_task_sections(tasks_md: str, schema: dict) -> str:
    """
    Keep ONLY the allowed headings in _TASK_ORDER (in that order).

    Phases are conditionally included:
      - If a phase is not in scope anywhere (global + all sites), it is dropped.
      - Otherwise we keep the model's body if present, or a sensible default.
    """
    tasks_md = _normalise_heading_levels_to_h3(tasks_md or "")
    found = {h: "" for h in _TASK_ORDER}

    # Harvest existing sections from the model output
    for h, body in _split_sections(tasks_md):
        if h in found:
            found[h] = body.strip()

    # Build defaults for sections that the model omitted
    prereqs = found["Client Prerequisites"] or _bullets_block(schema.get("prerequisites"))
    oos     = found["Out of Scope"]         or _bullets_block(schema.get("out_of_scope"))

    defaults = {
        "Site Survey (Site Visit 1)": "- (none provided)",
        "Installation (Site Visit 2)": "- (none provided)",
        "Post-Installation Services": "- (none provided)",
        "Client Prerequisites": prereqs or "- (none provided)",
        "Out of Scope": oos or "- (none provided)",
    }

    ordered = []
    for h in _TASK_ORDER:
        # Phase-level gating
        if h == "Site Survey (Site Visit 1)" and not _phase_in_scope(schema, "site_survey", "site_survey"):
            continue

        if h == "Installation (Site Visit 2)" and not _phase_in_scope(schema, "installation", "rack_and_stack"):
            # If you *never* want an LoE without an Installation section, remove this `continue`.
            continue

        if h == "Post-Installation Services" and not _phase_in_scope(schema, "post_install", "post_install"):
            continue

        body = (found[h] or defaults[h]).strip()
        ordered.append((h, body))

    return _rebuild_sections(ordered)





def _render_phase_per_site(
    schema: dict, base_body: str, phase_label: str, phase_key: str
) -> str:
    """
    If multiple sites have different 'include' flags or custom 'steps' for a phase,
    expand the generic phase body into per-site subsections.

    Otherwise, return the base_body untouched.
    """
    sites = schema.get("sites") or []
    if len(sites) <= 1:
        return base_body

    per_site = []
    for idx, site in enumerate(sites, start=1):
        if not isinstance(site, dict):
            continue

        name = (site.get("name") or site.get("site_id") or f"Site {idx}").strip()
        addr = (site.get("address") or "").strip()
        label = f"{name} — {addr}" if addr else name

        tasks = (site.get("tasks") or {}).get(phase_key) or {}
        include = bool(tasks.get("include"))
        steps = [str(s).strip() for s in (tasks.get("steps") or []) if str(s).strip()]

        per_site.append(
            {
                "label": label,
                "include": include,
                "steps": steps,
            }
        )

    if not per_site:
        return base_body

    has_mixed_include = len({s["include"] for s in per_site}) > 1
    has_any_steps = any(s["steps"] for s in per_site)

    # If all sites are identical (all include or all exclude, no extra steps),
    # don't clutter the doc — just keep the shared body.
    if not (has_mixed_include or has_any_steps):
        return base_body

    lines = []
    lines.append("Per-site breakdown:")

    for s in per_site:
        lines.append("")
        lines.append(f"#### {s['label']}")
        if s["include"]:
            lines.append("- In scope for this site.")
        else:
            lines.append("- Not in scope for this site.")

        if s["steps"]:
            lines.append("- Additional site-specific steps:")
            for st in s["steps"]:
                lines.append(f"  - {st}")

    base_body = base_body.strip()
    if base_body:
        lines.append("")
        lines.append("Generic tasks for this phase (applied where in scope):")
        lines.append("")
        lines.append(base_body)

    return "\n".join(lines).strip()


def _replace_bom_tokens(summary: str, schema: dict) -> str:
    """
    Replace any BOM token variant the model may emit:
      '{{BOM_TABLE}}', '{BOM_TABLE}', '(BOM_TABLE)', or bare 'BOM_TABLE'

    Now uses per-site BOM tables instead of a single global table.
    """
    bom_md = _multi_site_bom_markdown(schema, include_rack_unit=True)
    if not bom_md:
        # No BOM rows at any site -> generic placeholder
        return re.sub(
            r"\{?\(?\s*BOM_TABLE\s*\)?\}?", "_(No BOM items provided)_", summary
        )

    # Ensure blank lines before/after for clean markdown
    replacement = f"\n\n{bom_md}\n\n"
    return re.sub(r"\{?\(?\s*BOM_TABLE\s*\)?\}?", replacement, summary)


def _strip_orphan_blockquotes(text: str) -> str:
    """Remove lines that are just a lone '>' to avoid stray quote blocks."""
    if not text:
        return text or ""
    return re.sub(r"(?m)^\s*>\s*$", "", text).strip()


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
    body   = m.group("body") or ""

    lines = body.splitlines()
    if not lines:
        return summary

    global_scope = schema.get("global_scope") or {}
    site_survey_in_scope   = bool(global_scope.get("site_survey", {}).get("include"))
    post_install_in_scope  = bool(global_scope.get("post_install", {}).get("include"))

    kept_bullets = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            # odd line, keep it
            kept_bullets.append(line)
            continue

        text_l = stripped[1:].strip().lower()  # after '-'
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


# --- main -------------------------------------------------------------------

def post_process(schema: dict, result: dict) -> dict:
    summary = (result.get("summary") or "").strip()
    tasks = (result.get("tasks") or "").strip()

    # Placeholder replacements
    client = (schema.get("client") or "(Client)").strip()
    site = primary_site_line(schema) or "(TBD)"
    summary = summary.replace("{{CLIENT}}", client)
    summary = summary.replace("{{PRIMARY_SITE}}", site)

    # Ensure natural opener + remove generic duplicate
    summary = _ensure_client_specific_opener(summary, schema)

    # Hard guarantee: opener appears directly under "### Project Summary"
    summary = _inject_opener_after_heading(summary, schema)

    # Ensure Field Engineer tools block exists
    summary = _ensure_field_engineer_block(summary)

    # Replace any BOM token variant (or append a standard section if token missing)
    if re.search(r"\bBOM_TABLE\b", summary):
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

    # Make sure 'Key tasks overview' reflects what is actually in scope
    summary = _prune_key_tasks_block(summary, schema)

    # Final format cleanups for summary
    summary = _checkboxes_to_bullets(summary)
    summary = _tidy_key_tasks(summary)
    summary = _strip_orphan_blockquotes(summary)

    # ---- TASKS PIPELINE ----
    tasks = _checkboxes_to_bullets(tasks)
    tasks = _filter_and_order_task_sections(tasks, schema)

    # Inject per-site breakdowns for key phases when sites differ
    tasks = _normalise_heading_levels_to_h3(tasks or "")
    sections = _split_sections(tasks)
    new_sections = []
    for heading, body in sections:
        if heading == "Site Survey (Site Visit 1)":
            body = _render_phase_per_site(schema, body, heading, "site_survey")
        elif heading == "Installation (Site Visit 2)":
            body = _render_phase_per_site(schema, body, heading, "installation")
        elif heading == "Post-Installation Services":
            body = _render_phase_per_site(schema, body, heading, "post_install")
        new_sections.append((heading, body))

    tasks = _rebuild_sections(new_sections)

    result["summary"] = summary.strip()
    result["tasks"] = tasks.strip()
    return result
