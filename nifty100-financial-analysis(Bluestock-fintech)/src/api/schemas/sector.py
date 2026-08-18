"""Pydantic response schemas for the Day 40 sector API endpoints."""

from __future__ import annotations

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Sector aggregate
# ---------------------------------------------------------------------------


class SectorAggregate(BaseModel):
    """A single sector-level aggregate row."""

    sector: str
    company_count: int
    avg_roe_pct: float | None = None
    avg_roce_pct: float | None = None
    avg_debt_to_equity: float | None = None
    avg_net_profit_margin_pct: float | None = None
    avg_pe_ratio: float | None = None
    total_market_cap_cr: float | None = None


class SectorListResponse(BaseModel):
    """Response for GET /api/v1/sectors."""

    sectors: list[SectorAggregate]


# ---------------------------------------------------------------------------
# Sector companies
# ---------------------------------------------------------------------------


class SectorCompaniesItem(BaseModel):
    """A single company within a sector."""

    company_id: str
    company_name: str
    sub_sector: str | None = None


class SectorCompaniesResponse(BaseModel):
    """Response for GET /api/v1/sectors/{sector_name}/companies."""

    sector: str
    companies: list[SectorCompaniesItem]
    count: int
