"""
Sectors router for Bluestock Fintech API.

Implements three Day 40 endpoints:

  GET /api/v1/sectors                               — list all sector aggregates
  GET /api/v1/sectors/{sector_name}                 — single sector aggregate
  GET /api/v1/sectors/{sector_name}/companies       — companies in a sector
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas.sector import (
    SectorAggregate,
    SectorCompaniesResponse,
    SectorListResponse,
)
from src.dashboard.utils import db

router = APIRouter()


# ---------------------------------------------------------------------------
# Serialization helper (mirrors companies.py convention)
# ---------------------------------------------------------------------------


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
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, str):
        return value
    return value


def _df_to_records(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    """Convert a DataFrame to a list of JSON-serializable dicts for *columns*."""
    if df is None or df.empty:
        return []
    cols_present = [c for c in columns if c in df.columns]
    records = df[cols_present].to_dict(orient="records")
    return [{k: _clean_cell(v) for k, v in row.items()} for row in records]


# ---------------------------------------------------------------------------
# Column lists
# ---------------------------------------------------------------------------

_AGGREGATE_COLUMNS = [
    "sector",
    "company_count",
    "avg_roe_pct",
    "avg_roce_pct",
    "avg_debt_to_equity",
    "avg_net_profit_margin_pct",
    "avg_pe_ratio",
    "total_market_cap_cr",
]

# ---------------------------------------------------------------------------
# 1. GET /api/v1/sectors  —  list all sector aggregates
# ---------------------------------------------------------------------------


@router.get("/sectors", response_model=SectorListResponse)
async def list_sectors():
    """List sector-level financial aggregates across all 10 broad sectors."""
    df = db.get_sector_aggregates()
    sectors = _df_to_records(df, _AGGREGATE_COLUMNS)
    # Ensure company_count is an int
    for s in sectors:
        if s.get("company_count") is not None:
            s["company_count"] = int(s["company_count"])
    return JSONResponse(content={"sectors": sectors})


# ---------------------------------------------------------------------------
# 2. GET /api/v1/sectors/{sector_name}  —  single sector aggregate
# ---------------------------------------------------------------------------


@router.get("/sectors/{sector_name}", response_model=SectorAggregate)
async def get_sector(sector_name: str):
    """Return the aggregate for a single sector."""
    df = db.get_sector_aggregates()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"Sector not found: {sector_name}")

    # Case-sensitive filter on the "sector" column (broad_sector)
    match = df[df["sector"] == sector_name]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Sector not found: {sector_name}")

    record = match.iloc[0]
    result = {col: _clean_cell(record[col]) for col in _AGGREGATE_COLUMNS if col in record.index}
    if result.get("company_count") is not None:
        result["company_count"] = int(result["company_count"])

    return JSONResponse(content=result)


# ---------------------------------------------------------------------------
# 3. GET /api/v1/sectors/{sector_name}/companies  —  companies in a sector
# ---------------------------------------------------------------------------


@router.get("/sectors/{sector_name}/companies", response_model=SectorCompaniesResponse)
async def get_sector_companies(sector_name: str):
    """List all companies belonging to a sector."""
    rows = db.get_sectors()  # -> list[dict] with broad_sector, sub_sector, etc.
    if not rows:
        raise HTTPException(status_code=404, detail=f"Sector not found: {sector_name}")

    # Case-sensitive filter
    filtered = [r for r in rows if r.get("broad_sector") == sector_name]
    if not filtered:
        raise HTTPException(status_code=404, detail=f"Sector not found: {sector_name}")

    companies = []
    for r in filtered:
        companies.append(
            {
                "company_id": r["company_id"],
                "company_name": r["company_name"],
                "sub_sector": r.get("sub_sector") if r.get("sub_sector") else None,
            }
        )

    return JSONResponse(
        content={
            "sector": sector_name,
            "companies": companies,
            "count": len(companies),
        }
    )
