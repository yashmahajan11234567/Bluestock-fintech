"""
Pydantic response schemas for company API endpoints.

These models accurately reflect the real data shapes returned by the
existing DB helpers.  Financial-statement tables use dynamic dictionaries
because the database stores heterogeneous values (strings, floats, NULLs).
"""

from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Company list
# ---------------------------------------------------------------------------


class CompanyListItem(BaseModel):
    """Single entry in the company list response."""

    company_id: str
    company_name: str


class CompanyListResponse(BaseModel):
    """Response for GET /api/v1/companies."""

    companies: list[CompanyListItem]
    count: int


# ---------------------------------------------------------------------------
# Company profile
# ---------------------------------------------------------------------------


class CompanyProfile(BaseModel):
    """Full profile for a single company."""

    company_id: str
    company_name: str
    about_company: str | None = None
    website: str | None = None
    face_value: float | None = None
    book_value: float | None = None
    roe_percentage: float | None = None
    return_on_capital_employed_pct: float | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap_cr: float | None = None


# ---------------------------------------------------------------------------
# Financials
# ---------------------------------------------------------------------------


class ProfitAndLossEntry(BaseModel):
    """One year of P&L data — dynamic to accommodate heterogeneous DB values."""

    model_config = {"extra": "allow"}


class BalanceSheetEntry(BaseModel):
    """One year of balance-sheet data — dynamic to accommodate heterogeneous DB values."""

    model_config = {"extra": "allow"}


class FinancialsResponse(BaseModel):
    """Response for GET /api/v1/companies/{company_id}/financials."""

    company_id: str
    profit_and_loss: list[dict[str, Any]]
    balance_sheet: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Ratios
# ---------------------------------------------------------------------------


class RatiosResponse(BaseModel):
    """Response for GET /api/v1/companies/{company_id}/ratios."""

    company_id: str
    ratios: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Cashflow
# ---------------------------------------------------------------------------


class CashflowResponse(BaseModel):
    """Response for GET /api/v1/companies/{company_id}/cashflow."""

    company_id: str
    cashflow: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Peers
# ---------------------------------------------------------------------------


class PeerEntry(BaseModel):
    """Single peer company."""

    peer_group_name: str | None = None
    peer_company_id: str
    peer_company_name: str


class PeersResponse(BaseModel):
    """Response for GET /api/v1/companies/{company_id}/peers."""

    company_id: str
    peer_group_name: str | None = None
    peers: list[PeerEntry]


# ---------------------------------------------------------------------------
# Pros / Cons
# ---------------------------------------------------------------------------


class ProsConsResponse(BaseModel):
    """Response for GET /api/v1/companies/{company_id}/pros-cons."""

    company_id: str
    pros: list[str]
    cons: list[str]


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


class DocumentEntry(BaseModel):
    """Single document entry."""

    year: int | None = None
    annual_report_url: str | None = None


class DocumentsResponse(BaseModel):
    """Response for GET /api/v1/companies/{company_id}/documents."""

    company_id: str
    documents: list[DocumentEntry]
