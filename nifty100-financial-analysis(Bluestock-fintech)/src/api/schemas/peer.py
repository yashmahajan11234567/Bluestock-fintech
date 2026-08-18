"""Pydantic response schemas for the Day 40 peer comparison API endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Peer percentile
# ---------------------------------------------------------------------------


class PeerPercentiles(BaseModel):
    """Percentile scores for a company within its peer group."""

    roe_percentile: float | None = None
    net_profit_margin_percentile: float | None = None
    debt_to_equity_percentile: float | None = None
    free_cash_flow_percentile: float | None = None
    pe_percentile: float | None = None
    pb_percentile: float | None = None


# ---------------------------------------------------------------------------
# Peer member
# ---------------------------------------------------------------------------


class PeerMember(BaseModel):
    """A single peer-group member."""

    peer_company_id: str
    peer_company_name: str


# ---------------------------------------------------------------------------
# Peer comparison response
# ---------------------------------------------------------------------------


class PeerComparisonResponse(BaseModel):
    """Response for GET /api/v1/peers/{company_id}."""

    company_id: str
    peer_group_name: str | None = None
    overall_peer_score: float | None = None
    percentiles: PeerPercentiles | None = None
    peers: list[PeerMember] = Field(default_factory=list)
