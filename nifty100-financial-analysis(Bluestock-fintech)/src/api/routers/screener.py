"""
Screener router for Bluestock Fintech API.

Implements:

  GET /api/v1/screener  — filter, sort, and paginate the live SQLite-backed
  screener results from ``src.dashboard.utils.db.get_screener_results()``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.api.schemas.screener import ScreenerResponse
from src.dashboard.utils import db

router = APIRouter()

# ---------------------------------------------------------------------------
# Serialization helpers (mirroring src/api/routers/companies.py conventions)
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
    if isinstance(value, (pd.Timestamp,)):
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
# Constants
# ---------------------------------------------------------------------------

# API parameter -> (display_name, min/max key)
# Used to translate the flat API query parameters into the filter dict
# format understood by ``get_screener_results``.
_FILTER_PARAM_MAP: list[tuple[str, str, str]] = [
    ("min_roe", "ROE", "min"),
    ("max_roe", "ROE", "max"),
    ("min_debt_to_equity", "Debt to Equity", "min"),
    ("max_debt_to_equity", "Debt to Equity", "max"),
    ("min_opm", "Operating Profit Margin", "min"),
    ("max_opm", "Operating Profit Margin", "max"),
    ("min_market_cap", "Market Cap", "min"),
    ("max_market_cap", "Market Cap", "max"),
    ("min_fcf", "Free Cash Flow", "min"),
    ("max_fcf", "Free Cash Flow", "max"),
    ("min_revenue_growth", "Revenue CAGR", "min"),
    ("max_revenue_growth", "Revenue CAGR", "max"),
    ("min_pat_growth", "PAT CAGR", "min"),
    ("max_pat_growth", "PAT CAGR", "max"),
    ("min_dividend_yield", "Dividend Yield", "min"),
    ("max_dividend_yield", "Dividend Yield", "max"),
    ("min_pe", "PE", "min"),
    ("max_pe", "PE", "max"),
    ("min_pb", "PB", "min"),
    ("max_pb", "PB", "max"),
    ("min_interest_coverage", "Interest Coverage", "min"),
    ("max_interest_coverage", "Interest Coverage", "max"),
]

# Explicit allowlist of sortable columns — never accept arbitrary SQL names.
_ALLOWED_SORT_FIELDS = frozenset(
    [
        "company_id",
        "company_name",
        "sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "operating_profit_margin_pct",
        "interest_coverage",
        "free_cash_flow_cr",
        "cash_from_operations_cr",
        "net_profit_margin_pct",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "dividend_yield_pct",
        "pe_ratio",
        "pb_ratio",
        "net_profit",
        "composite_quality_score",
        "sector_relative_score",
        "market_cap_crore",
    ]
)

_RESPONSE_COLUMNS = [
    "company_id",
    "company_name",
    "sector",
    "return_on_equity_pct",
    "debt_to_equity",
    "operating_profit_margin_pct",
    "interest_coverage",
    "free_cash_flow_cr",
    "cash_from_operations_cr",
    "net_profit_margin_pct",
    "compounded_sales_growth",
    "compounded_profit_growth",
    "dividend_yield_pct",
    "pe_ratio",
    "pb_ratio",
    "net_profit",
    "composite_quality_score",
    "sector_relative_score",
    "market_cap_crore",
]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/screener", response_model=ScreenerResponse)
async def screener(
    # Threshold filters
    min_roe: float | None = Query(None, ge=0),
    max_roe: float | None = Query(None, ge=0),
    min_debt_to_equity: float | None = Query(None, ge=0),
    max_debt_to_equity: float | None = Query(None, ge=0),
    min_opm: float | None = Query(None, ge=0),
    max_opm: float | None = Query(None, ge=0),
    min_market_cap: float | None = Query(None, ge=0),
    max_market_cap: float | None = Query(None, ge=0),
    min_fcf: float | None = Query(None, ge=0),
    max_fcf: float | None = Query(None, ge=0),
    min_revenue_growth: float | None = Query(None, ge=0),
    max_revenue_growth: float | None = Query(None, ge=0),
    min_pat_growth: float | None = Query(None, ge=0),
    max_pat_growth: float | None = Query(None, ge=0),
    min_dividend_yield: float | None = Query(None, ge=0),
    max_dividend_yield: float | None = Query(None, ge=0),
    min_pe: float | None = Query(None, ge=0),
    max_pe: float | None = Query(None, ge=0),
    min_pb: float | None = Query(None, ge=0),
    max_pb: float | None = Query(None, ge=0),
    min_interest_coverage: float | None = Query(None, ge=0),
    max_interest_coverage: float | None = Query(None, ge=0),
    # Sector filter
    sector: str | None = Query(None),
    # Sorting
    sort: str | None = Query("composite_quality_score"),
    sort_dir: str | None = Query("desc"),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Screen Nifty 100 companies by financial criteria.

    Supports min/max threshold filters for ROE, debt-to-equity, operating
    profit margin, market cap, free cash flow, revenue CAGR, PAT CAGR,
    dividend yield, PE, PB, and interest coverage.  Results are filtered
    at the database layer via ``get_screener_results()``, then sorted and
    paginated at the API layer.

    Returns 422 for invalid sort fields, page, or page_size values."""
    # ------------------------------------------------------------------
    # Validate sort_dir
    # ------------------------------------------------------------------
    if sort_dir not in ("asc", "desc"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_dir '{sort_dir}'. Must be 'asc' or 'desc'.",
        )

    # ------------------------------------------------------------------
    # Validate sort field against explicit allowlist
    # ------------------------------------------------------------------
    if sort is not None and sort not in _ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort field '{sort}'. Allowed fields: {sorted(_ALLOWED_SORT_FIELDS)}",
        )

    # ------------------------------------------------------------------
    # Build the filter dict in the format expected by get_screener_results
    # ------------------------------------------------------------------
    filters: dict[str, dict[str, float]] = {}
    param_values = {
        "min_roe": min_roe,
        "max_roe": max_roe,
        "min_debt_to_equity": min_debt_to_equity,
        "max_debt_to_equity": max_debt_to_equity,
        "min_opm": min_opm,
        "max_opm": max_opm,
        "min_market_cap": min_market_cap,
        "max_market_cap": max_market_cap,
        "min_fcf": min_fcf,
        "max_fcf": max_fcf,
        "min_revenue_growth": min_revenue_growth,
        "max_revenue_growth": max_revenue_growth,
        "min_pat_growth": min_pat_growth,
        "max_pat_growth": max_pat_growth,
        "min_dividend_yield": min_dividend_yield,
        "max_dividend_yield": max_dividend_yield,
        "min_pe": min_pe,
        "max_pe": max_pe,
        "min_pb": min_pb,
        "max_pb": max_pb,
        "min_interest_coverage": min_interest_coverage,
        "max_interest_coverage": max_interest_coverage,
    }

    for param, display_name, min_or_max in _FILTER_PARAM_MAP:
        value = param_values[param]
        if value is not None:
            filters.setdefault(display_name, {})[min_or_max] = value

    # ------------------------------------------------------------------
    # Query the database (filters are applied inside get_screener_results)
    # ------------------------------------------------------------------
    db_sort_by = sort if sort else "company_id"
    df = db.get_screener_results(filters, sort_by=db_sort_by)

    if df is None or df.empty:
        # Empty result — return 200 with empty items
        return JSONResponse(
            content={
                "items": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }
        )

    # ------------------------------------------------------------------
    # Apply sector filter (post-DB, case-sensitive)
    # ------------------------------------------------------------------
    if sector is not None:
        if "sector" in df.columns:
            df = df[df["sector"] == sector]

    total_count = len(df)

    # ------------------------------------------------------------------
    # Sort (post-filter, before pagination) with na_position="last"
    # ------------------------------------------------------------------
    if sort is not None and sort in df.columns:
        df = df.sort_values(
            by=sort,
            ascending=(sort_dir == "asc"),
            na_position="last",
        )

    # ------------------------------------------------------------------
    # Paginate
    # ------------------------------------------------------------------
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

    items = _df_to_records(page_df, _RESPONSE_COLUMNS)

    return JSONResponse(
        content={
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )
