"""
Companies router for Bluestock Fintech API.

Implements the eight Day 39 company endpoints:

  1. GET /api/v1/companies                                 — list companies
  2. GET /api/v1/companies/{company_id}                    — company profile
  3. GET /api/v1/companies/{company_id}/financials         — P&L + balance sheet
  4. GET /api/v1/companies/{company_id}/ratios               — financial ratios
  5. GET /api/v1/companies/{company_id}/cashflow           — cash flow data
  6. GET /api/v1/companies/{company_id}/peers                — peer group composition
  7. GET /api/v1/companies/{company_id}/pros-cons            — pros / cons text
  8. GET /api/v1/companies/{company_id}/documents            — annual reports

All data is backed by the real SQLite database via the existing DB helpers
in ``src/dashboard/utils/db.py``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas.company import (
    CashflowResponse,
    CompanyListResponse,
    CompanyProfile,
    DocumentsResponse,
    FinancialsResponse,
    PeerEntry,
    PeersResponse,
    ProsConsResponse,
    RatiosResponse,
)
from src.dashboard.utils import db

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal serialization utilities
# ---------------------------------------------------------------------------


def _safe_int(value: Any) -> int | None:
    """
    Normalize a year-like value to a plain Python int (or None).

    Handles datetime strings ("2024-03-01 00:00:00"), floats (2024.0),
    integers, pandas Timestamps, numpy scalars, and NULL/None.
    """
    if value is None:
        return None
    # pandas.Timestamp / numpy datetime64
    if isinstance(value, (pd.Timestamp,)):
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
    if isinstance(value, (pd.Timestamp,)):
        return int(value.year) if not pd.isna(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, str):
        return value
    return value


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Convert a DataFrame to a list of JSON-serializable dicts.

    - NaN  -> None
    - NaN years already cast to Int64 by the helper
    """
    if df is None or df.empty:
        return []
    records = df.to_dict(orient="records")
    # Clean each cell
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
# 1. List companies
# ---------------------------------------------------------------------------


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies():
    """List all 92 companies, sorted alphabetically by company_name.

    Returns:
        JSON with ``companies`` (list of {company_id, company_name}) and ``count``."""
    rows = db.get_company_list()
    companies = [
        {"company_id": r["company_id"], "company_name": r["company_name"]} for r in rows
    ]
    return JSONResponse(content={"companies": companies, "count": len(companies)})


# ---------------------------------------------------------------------------
# 2. Company profile
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}", response_model=CompanyProfile)
async def get_company(company_id: str):
    """Get the full profile for a single company identified by its ticker.

    Unknown ticker -> 404."""
    profile = db.get_company_profile(company_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company not found: {company_id}",
        )
    return profile


# ---------------------------------------------------------------------------
# 3. Financials (P&L + Balance Sheet)
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}/financials", response_model=FinancialsResponse)
async def get_financials(company_id: str):
    """Return profit-and-loss and balance-sheet data for a company.

    Years are returned as integers (or None when NULL in the source)."""
    _ensure_company_exists(company_id)

    pl_df = db.get_pl(company_id)
    bs_df = db.get_bs(company_id)

    # Normalise the year column to int / None
    if not pl_df.empty and "year" in pl_df.columns:
        pl_df = pl_df.copy()
        pl_df["year"] = pl_df["year"].apply(_safe_int)

    if not bs_df.empty and "year" in bs_df.columns:
        bs_df = bs_df.copy()
        bs_df["year"] = bs_df["year"].apply(_safe_int)

    return {
        "company_id": company_id,
        "profit_and_loss": _df_to_records(pl_df),
        "balance_sheet": _df_to_records(bs_df),
    }


# ---------------------------------------------------------------------------
# 4. Financial ratios
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}/ratios", response_model=RatiosResponse)
async def get_ratios(company_id: str):
    """Return financial ratios for a company.

    Year ordering is preserved as DESC (latest first) from the helper."""
    _ensure_company_exists(company_id)

    df = db.get_financial_ratios(company_id)
    records = _df_to_records(df)
    # Normalise year to int / None
    for rec in records:
        if "year" in rec:
            rec["year"] = _safe_int(rec["year"])

    return {
        "company_id": company_id,
        "ratios": records,
    }


# ---------------------------------------------------------------------------
# 5. Cashflow
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}/cashflow", response_model=CashflowResponse)
async def get_cashflow(company_id: str):
    """Return cash-flow data for a company.

    Only stored fields are returned — no derived Free Cash Flow."""
    _ensure_company_exists(company_id)

    df = db.get_cashflow_data(company_id)
    records = _df_to_records(df)
    for rec in records:
        if "year" in rec:
            rec["year"] = _safe_int(rec["year"])

    return {
        "company_id": company_id,
        "cashflow": records,
    }


# ---------------------------------------------------------------------------
# 6. Peers
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}/peers", response_model=PeersResponse)
async def get_company_peers(company_id: str):
    """Return the peer-group composition for a company.

    If the company has no peer-group row → 200 with peer_group_name=null, peers=[]."""
    _ensure_company_exists(company_id)

    peer_group_name = db.get_peer_groups(company_id)  # str or ""
    if not peer_group_name:
        return JSONResponse(
            content={
                "company_id": company_id,
                "peer_group_name": None,
                "peers": [],
            }
        )

    peer_rows = db.get_peers(company_id)

    peers: list[PeerEntry] = []
    for r in peer_rows:
        peers.append(
            {
                "peer_group_name": r.get("peer_group_name"),
                "peer_company_id": r.get("peer_company_id", ""),
                "peer_company_name": r.get("peer_company_name", ""),
            }
        )

    return JSONResponse(
        content={
            "company_id": company_id,
            "peer_group_name": peer_group_name,
            "peers": peers,
        }
    )


# ---------------------------------------------------------------------------
# 7. Pros / Cons
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}/pros-cons", response_model=ProsConsResponse)
async def get_pros_cons_endpoint(company_id: str):
    """Return pros and cons for a company.

    If no record exists → 200 with pros=[], cons=[]."""
    _ensure_company_exists(company_id)

    rows = db.get_pros_cons(company_id)

    # Build flat lists from all rows.
    # Each row stores a single pro string and a single cons string.
    pros: list[str] = []
    cons: list[str] = []
    for r in rows:
        p = r.get("pros")
        c = r.get("cons")
        # Treat the literal string 'None' as no value (some seed data stores it)
        if isinstance(p, str) and p.strip().lower() != "none" and p.strip():
            pros.append(p.strip())
        if isinstance(c, str) and c.strip().lower() != "none" and c.strip():
            cons.append(c.strip())

    return JSONResponse(
        content={
            "company_id": company_id,
            "pros": pros,
            "cons": cons,
        }
    )


# ---------------------------------------------------------------------------
# 8. Documents
# ---------------------------------------------------------------------------


@router.get("/companies/{company_id}/documents", response_model=DocumentsResponse)
async def get_documents_endpoint(company_id: str):
    """Return documents (annual reports) for a company.

    If no record exists → 200 with documents=[]."""
    _ensure_company_exists(company_id)

    rows = db.get_documents(company_id)

    documents: list[dict[str, Any]] = []
    for r in rows:
        documents.append(
            {
                "year": _safe_int(r.get("Year")),
                "annual_report_url": r.get("Annual_Report"),
            }
        )

    return JSONResponse(
        content={
            "company_id": company_id,
            "documents": documents,
        }
    )
