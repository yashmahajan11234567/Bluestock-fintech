"""
Valuation router for Bluestock Fintech API.

Implements:

  GET /api/v1/valuation/{company_id}
  — Per-company valuation time-series
  — Uses ``get_valuation()`` from ``src/dashboard/utils/db``.

This endpoint is distinct from the Day 39:
    GET /api/v1/companies/{company_id}
which returns a single latest-year snapshot as part of the profile.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas.valuation import ValuationResponse
from src.dashboard.utils import db

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal serialization utilities (mirrors companies.py convention)
# ---------------------------------------------------------------------------


def _safe_int(value: Any) -> int | None:
    """
    Normalize a year-like value to a plain Python int (or None).

    Handles floats (2024.0), strings ("2024", "2024-03-01 00:00:00"),
    pandas Timestamps, numpy scalars, and NULL/None.
    """
    if value is None:
        return None
    # pandas.Timestamp
    if isinstance(value, pd.Timestamp):
        return int(value.year) if not pd.isna(value) else None
    if isinstance(value, np.datetime64):
        if np.isnat(value):
            return None
        return int(pd.Timestamp(value).year)
    # numpy scalar types
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        if np.isnan(value):
            return None
        return int(value)
    # strings that look like datetimes — extract the year
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # Try parsing as a date/datetime string
        try:
            ts = pd.to_datetime(s, errors="coerce")
            if not pd.isna(ts):
                return int(ts.year)
        except Exception:
            pass
        # Fall back: try plain integer parse
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return None
    # Plain float / int
    if isinstance(value, float):
        if np.isnan(value):
            return None
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _clean_cell(value: Any) -> Any:
    """Convert a single pandas/numpy cell to a JSON-serializable Python value."""
    if value is None:
        return None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float):
        if np.isnan(value):
            return None
        return value
    if isinstance(value, pd.Timestamp):
        return int(value.year) if not pd.isna(value) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, str):
        return value
    return value


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Convert a DataFrame to a list of JSON-serializable dicts.

    - NaN  -> None
    - numpy scalars -> native Python values
    - DataFrame -> list of dictionaries
    """
    if df is None or df.empty:
        return []
    records = df.to_dict(orient="records")
    cleaned: list[dict[str, Any]] = []
    for row in records:
        cleaned.append({k: _clean_cell(v) for k, v in row.items()})
    return cleaned


def _ensure_company_exists(company_id: str) -> None:
    """Raise HTTP 404 if the company ticker is unknown."""
    profile = db.get_company_profile(company_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company not found: {company_id}",
        )


# ---------------------------------------------------------------------------
# Valuation time-series
# ---------------------------------------------------------------------------

VALUATION_FIELDS = [
    "year",
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]


@router.get("/valuation/{company_id}", response_model=ValuationResponse)
async def get_valuation_endpoint(company_id: str):
    """Return the valuation time-series for a single company identified by its ticker.

    The response is ordered by year DESC (latest first), matching ``get_valuation()``.

    - Unknown ticker → HTTP 404
    - Valid company with no valuation rows → HTTP 200 with ``valuations=[]``"""
    _ensure_company_exists(company_id)

    df = db.get_valuation(company_id)
    records = _df_to_records(df)

    # Defensive year normalization
    for rec in records:
        if "year" in rec:
            rec["year"] = _safe_int(rec["year"])

    # Build response ensuring exactly the seven valuation fields
    valuations = []
    for rec in records:
        entry = {}
        for field in VALUATION_FIELDS:
            entry[field] = rec.get(field)
        valuations.append(entry)

    return JSONResponse(
        content={
            "company_id": company_id,
            "valuations": valuations,
        }
    )
