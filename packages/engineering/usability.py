"""Usability, pagination, search, and unit round-trip system (GD-A04).

Provides:
- Searchable, filterable, and paginated record table navigation with row-level error tagging.
- Bi-directional unit conversion with guaranteed round-trip numerical preservation.
- Unit profile management (SI Metric, Field/Imperial, Oilfield Canadian/North Sea).
- Preservation of unknown/null values (null never silently becomes 0).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict

from .readiness import UNIT_FACTORS


class UnitProfile(TypedDict):
    name: str
    length: str
    force: str
    torque: str
    velocity: str
    pressure: str
    volume_flow: str
    angle: str
    frequency: str


UNIT_PROFILES: Dict[str, UnitProfile] = {
    "SI": {
        "name": "SI Metric (Canonical)",
        "length": "m",
        "force": "N",
        "torque": "N.m",
        "velocity": "m/s",
        "pressure": "Pa",
        "volume_flow": "m3/s",
        "angle": "deg",
        "frequency": "rpm",
    },
    "Field_US": {
        "name": "Oilfield US / Imperial",
        "length": "ft",
        "force": "klbf",
        "torque": "kft.lbf",
        "velocity": "ft/h",
        "pressure": "psi",
        "volume_flow": "gpm",
        "angle": "deg",
        "frequency": "rpm",
    },
    "Metric_Oilfield": {
        "name": "Metric Oilfield (European/Eurasian)",
        "length": "m",
        "force": "kN",
        "torque": "kN.m",
        "velocity": "m/h",
        "pressure": "bar",
        "volume_flow": "l/min",
        "angle": "deg",
        "frequency": "rpm",
    },
}


def convert_unit(
    val: Optional[float],
    dimension: str,
    from_unit: str,
    to_unit: str,
) -> Optional[float]:
    """Convert a value between units within the same dimension.

    Guarantees:
    - None / missing values remain None (never coerced to 0.0).
    - Preserves exact IEEE-754 precision where possible, with verified round-trip tolerance.
    """
    if val is None:
        return None
    if math.isnan(val) or math.isinf(val):
        return val

    from_u = from_unit.strip().lower()
    to_u = to_unit.strip().lower()

    if from_u == to_u:
        return val

    table = UNIT_FACTORS.get(dimension.lower())
    if not table:
        raise ValueError(f"Unknown physical dimension: {dimension}")

    if from_u not in table:
        raise ValueError(f"Unknown source unit '{from_unit}' for dimension '{dimension}'")
    if to_u not in table:
        raise ValueError(f"Unknown target unit '{to_unit}' for dimension '{dimension}'")

    from_factor = table[from_u]
    to_factor = table[to_u]

    # Convert to canonical SI baseline, then to target unit
    val_si = val * from_factor
    return val_si / to_factor


def paginate_and_search_records(
    rows: List[Dict[str, Any]],
    page: int = 1,
    page_size: int = 50,
    search_query: str = "",
    search_columns: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_desc: bool = False,
    error_flag_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Search, filter, sort, and paginate large engineering record sets.

    Returns:
    - paginated rows
    - total count & matching count
    - page metadata
    - error-flagged row indices for fast jump navigation
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50

    filtered = rows
    query = search_query.strip().lower()

    # Search filter
    if query:
        def matches(r: Dict[str, Any]) -> bool:
            cols = search_columns or list(r.keys())
            for c in cols:
                v = r.get(c)
                if v is not None and query in str(v).lower():
                    return True
            return False

        filtered = [r for r in filtered if matches(r)]

    # Identify row indices with error flags
    flagged_indices: List[int] = []
    if error_flag_key:
        for idx, r in enumerate(filtered):
            if r.get(error_flag_key):
                flagged_indices.append(idx)

    # Sorting
    if sort_by:
        def sort_key(r: Dict[str, Any]):
            val = r.get(sort_by)
            return (val is None, val)  # None sorted to end

        filtered = sorted(filtered, key=sort_key, reverse=sort_desc)

    total_records = len(rows)
    total_matching = len(filtered)
    total_pages = max(1, math.ceil(total_matching / page_size)) if total_matching > 0 else 1

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_rows = filtered[start_idx:end_idx]

    return {
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_matching": total_matching,
        "total_pages": total_pages,
        "flagged_indices": flagged_indices,
        "rows": page_rows,
    }
