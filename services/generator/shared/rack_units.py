# services/generator/shared/rack_units.py

import json
import re
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Paths / lookup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
LOOKUP_PATH = BASE_DIR / "rack_units.json"


def _canon_model(raw: str) -> str:
    """
    Canonicalise model names to increase hit rate with the JSON lookup.

    Examples:
      'Dell R650'          -> 'R650'
      'Cisco C9300-24T'    -> 'C9300-24T'
      'Arista 7050X'       -> '7050X'
      '   r650  '          -> 'R650'
    """
    s = (raw or "").strip()
    # normalise whitespace
    s = re.sub(r"\s+", " ", s)
    # strip leading common vendor names
    s = re.sub(r"(?i)^(Cisco|Juniper|Dell|Arista|HP|HPE)\s+", "", s)
    return s.upper()


def _load_lookup() -> Dict[str, int]:
    """
    Load rack_units.json and normalise keys using _canon_model.

    File format is expected to be:
      {
        "R650": 1,
        "C9300-24T": 1,
        ...
      }
    """
    try:
        with LOOKUP_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        # Fail-safe: if file is broken, don't crash the app.
        return {}

    lookup: Dict[str, int] = {}
    for k, v in raw.items():
        try:
            if v is None:
                continue
            canon = _canon_model(k)
            if canon:
                lookup[canon] = int(v)
        except Exception:
            # Skip bad rows rather than failing the whole load
            continue
    return lookup


RACK_UNITS_LOOKUP: Dict[str, int] = _load_lookup()

# Optional type-based defaults if we don't know the specific model
TYPE_DEFAULTS: Dict[str, int] = {
    "Switch": 1,
    "Firewall": 1,
    "Router": 1,
    "Server-1U": 1,
    "Server-2U": 2,
    "Chassis": 7,
}


# ---------------------------------------------------------------------------
# Core enrichment helpers
# ---------------------------------------------------------------------------

def _enrich_row_ru(row: Any) -> Any:
    """
    Enrich a single BOM row with 'rack_unit' if we can.

    Precedence:
      1. If an existing rack unit (rack_unit / rack_units / ru) looks sane,
         keep it.
      2. Else, look up by canonicalised model in RACK_UNITS_LOOKUP.
      3. Else, fall back to TYPE_DEFAULTS based on 'type' (optional hint).
      4. Else, set rack_unit = None.

    Never throws away a valid existing value.
    """
    if not isinstance(row, dict):
        return row

    item: Dict[str, Any] = dict(row)

    # 1) Keep any existing sane value
    existing = (
        item.get("rack_unit")
        or item.get("rack_units")
        or item.get("ru")
    )
    if isinstance(existing, (int, float)) and 0 < existing < 50:
        item["rack_unit"] = int(existing)
        return item

    # 2) Lookup by model
    model_raw = (item.get("model") or "").strip()
    canon = _canon_model(model_raw)
    if canon and canon in RACK_UNITS_LOOKUP:
        item["rack_unit"] = RACK_UNITS_LOOKUP[canon]
        return item

    # 3) Fallback by type (optional)
    type_key = (item.get("type") or "").strip()
    if type_key in TYPE_DEFAULTS:
        item["rack_unit"] = TYPE_DEFAULTS[type_key]
        return item

    # 4) Unknown
    item["rack_unit"] = None
    return item


def _enrich_list(lst: Any) -> Any:
    """
    Enrich all rows in a list with rack units.
    If lst is not a list, returns it unchanged.
    """
    if not isinstance(lst, list):
        return lst
    return [_enrich_row_ru(r) for r in lst]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enrich_schema_rack_units(schema: Any) -> Any:
    """
    Walk the extracted schema dict and enrich BOM entries with rack units.

    Expected schema shape (simplified):

      {
        "bom": [ ... ],              # legacy/global BOM
        "sites": [
          {
            "bom": [...],
            "optics_bom": [...],
            ...
          },
          ...
        ],
        ...
      }

    All BOM-like lists are enriched in-place and the same schema object
    is returned (for convenience in pipelines).
    """
    if not isinstance(schema, dict):
        return schema

    # 1) Legacy/global BOM
    schema["bom"] = _enrich_list(schema.get("bom") or [])

    # 2) Per-site BOM + optics BOM
    sites = schema.get("sites") or []
    if isinstance(sites, list):
        new_sites: List[Dict[str, Any]] = []
        for raw_site in sites:
            if not isinstance(raw_site, dict):
                new_sites.append(raw_site)
                continue

            site: Dict[str, Any] = dict(raw_site)
            site["bom"] = _enrich_list(site.get("bom") or [])
            site["optics_bom"] = _enrich_list(site.get("optics_bom") or [])
            new_sites.append(site)

        schema["sites"] = new_sites

    return schema
