"""
Pydantic response schemas for the Day 41 valuation API endpoint.

GET /api/v1/valuation/{company_id}
"""

from __future__ import annotations

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Valuation entry
# ---------------------------------------------------------------------------


class ValuationEntry(BaseModel):
    """
    A single yearly valuation record for a company.

    All metric fields are optional because financial valuation data can
    legitimately be NULL in the source database.
    """

    year: int | None = None
    market_cap_crore: float | None = None
    enterprise_value_crore: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    ev_ebitda: float | None = None
    dividend_yield_pct: float | None = None


# ---------------------------------------------------------------------------
# Valuation response
# ---------------------------------------------------------------------------


class ValuationResponse(BaseModel):
    """Response for GET /api/v1/valuation/{company_id}."""

    company_id: str
    valuations: list[ValuationEntry]
