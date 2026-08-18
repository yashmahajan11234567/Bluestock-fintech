"""Pydantic response schemas for the Day 40 screener API endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Screener item
# ---------------------------------------------------------------------------


class ScreenerItem(BaseModel):
    """A single company row from the screener results."""

    company_id: str
    company_name: str
    sector: str | None = None
    return_on_equity_pct: float | None = None
    debt_to_equity: float | None = None
    operating_profit_margin_pct: float | None = None
    interest_coverage: float | None = None
    free_cash_flow_cr: float | None = None
    cash_from_operations_cr: float | None = None
    net_profit_margin_pct: float | None = None
    compounded_sales_growth: float | None = None
    compounded_profit_growth: float | None = None
    dividend_yield_pct: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    net_profit: float | None = None
    composite_quality_score: float | None = None
    sector_relative_score: float | None = None
    market_cap_crore: float | None = None


# ---------------------------------------------------------------------------
# Screener response
# ---------------------------------------------------------------------------


class ScreenerResponse(BaseModel):
    """Paginated response for GET /api/v1/screener."""

    items: list[ScreenerItem]
    total_count: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)
