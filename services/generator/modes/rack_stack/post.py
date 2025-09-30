import re
from services.generator.shared.tables import bom_table_markdown
from services.generator.shared.derive import primary_site_line

def post_process(schema: dict, result: dict) -> dict:
    summary = result.get("summary","")
    site = primary_site_line(schema)
    if site and "Site address:" not in summary:
        summary += f"\n\n**Site address:** {site}"
    bom_md = bom_table_markdown(schema)
    if bom_md and "Bill of Materials" not in summary:
        summary += f"\n\n### Bill of Materials\n{bom_md}"
    # remove any Wave Plan block if it slipped in
    tasks = re.sub(r"(?s)###\s*Wave Installation Plan.*$", "", result.get("tasks","")).strip()

    counts = (schema.get("counts") or {})
    device_totals = (
        f"**Device totals:** {counts.get('aps_ordered') or 'TBD'} APs ordered — "
        f"{counts.get('aps_to_mount') or 'TBD'} to be mounted; "
        f"{counts.get('devices_total') or 'TBD'} total devices."
    )
    if "Device totals:**" not in summary:
        summary += f"\n\n{device_totals}"

    result["summary"] = summary
    result["tasks"] = tasks
    return result
