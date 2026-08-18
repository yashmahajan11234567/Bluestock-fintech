"""
Peers router for Bluestock Fintech API.

Implements:

  GET /api/v1/peers/{company_id}
  — How does a company rank against its peer group?
  — Uses ``get_peer_percentiles()`` and ``get_peer_group_members()`` from
    ``src.dashboard.utils.db``.

This endpoint differs from the Day 39
``GET /api/v1/companies/{company_id}/peers`` which answers "who are my peers?"
rather than "how do I rank?".
"""

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas.peer import (
    PeerComparisonResponse,
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
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, str):
        return value
    return value


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/peers/{company_id}", response_model=PeerComparisonResponse)
async def get_peers_endpoint(company_id: str):
    """Compare a company against its peer group using percentile rankings."""
    # --- Company existence check (Day 39 convention) ---
    profile = db.get_company_profile(company_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company not found: {company_id}",
        )

    # --- Peer percentiles (exact reuse of existing helper) ---
    percentiles = db.get_peer_percentiles(company_id)

    # --- Determine peer group name ---
    peer_group_name = db.get_peer_groups(company_id)  # str or ""

    if not peer_group_name:
        # Company exists but has no peer group
        return JSONResponse(
            content={
                "company_id": company_id,
                "peer_group_name": None,
                "overall_peer_score": None,
                "percentiles": None,
                "peers": [],
            }
        )

    # --- Build percentiles object (exact reuse of existing helper values) ---
    percentile_fields = [
        "roe_percentile",
        "net_profit_margin_percentile",
        "debt_to_equity_percentile",
        "free_cash_flow_percentile",
        "pe_percentile",
        "pb_percentile",
    ]
    pct_obj = {field: _clean_cell(percentiles.get(field)) for field in percentile_fields}

    # --- Peer group members (exact reuse of existing helper) ---
    members = db.get_peer_group_members(peer_group_name)
    peers = [
        {
            "peer_company_id": _clean_cell(m.get("company_id")),
            "peer_company_name": _clean_cell(m.get("company_name")),
        }
        for m in members
    ]

    overall_score = _clean_cell(percentiles.get("overall_peer_score"))

    return JSONResponse(
        content={
            "company_id": company_id,
            "peer_group_name": peer_group_name,
            "overall_peer_score": overall_score,
            "percentiles": pct_obj,
            "peers": peers,
        }
    )
