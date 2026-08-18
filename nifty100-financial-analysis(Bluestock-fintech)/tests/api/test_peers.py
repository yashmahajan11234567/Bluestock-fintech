"""
Tests for the Day 40 Peer Comparison API endpoint.

Uses real SQLite-backed data from the live database.  No data is modified.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils import db

client = TestClient(app)

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"


def _json_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def _company_with_peers() -> str | None:
    """Return a company_id that has a peer group, or None."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM peer_groups ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _company_without_peers() -> str | None:
    """Return a company_id that has NO peer group row."""
    rows = db._fetchall("""
        SELECT c.id FROM companies c
        LEFT JOIN peer_groups pg ON pg.company_id = c.id
        WHERE pg.company_id IS NULL
        ORDER BY c.id
        """)
    return rows[0]["id"] if rows else None


# ---------------------------------------------------------------------------
# 1. known peer company → 200
# ---------------------------------------------------------------------------


def test_known_peer_company_200():
    ticker = _company_with_peers()
    assert ticker is not None, "No company with a peer group found in DB"
    response = client.get(f"/api/v1/peers/{ticker}")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. peer_group_name correct
# ---------------------------------------------------------------------------


def test_peer_group_name_correct():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/peers/{ticker}")
    data = response.json()
    expected = db.get_peer_groups(ticker)
    assert data["peer_group_name"] == expected


# ---------------------------------------------------------------------------
# 3. overall_peer_score matches get_peer_percentiles()
# ---------------------------------------------------------------------------


def test_overall_peer_score_matches():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/peers/{ticker}")
    data = response.json()
    db_pct = db.get_peer_percentiles(ticker)
    assert data["overall_peer_score"] == db_pct.get("overall_peer_score")


# ---------------------------------------------------------------------------
# 4. all six percentile fields present
# ---------------------------------------------------------------------------


def test_all_six_percentile_fields_present():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/peers/{ticker}")
    data = response.json()
    pct = data["percentiles"]
    assert pct is not None
    expected_fields = {
        "roe_percentile",
        "net_profit_margin_percentile",
        "debt_to_equity_percentile",
        "free_cash_flow_percentile",
        "pe_percentile",
        "pb_percentile",
    }
    assert set(pct.keys()) == expected_fields


# ---------------------------------------------------------------------------
# 5. percentile values match existing helper
# ---------------------------------------------------------------------------


def test_percentile_values_match_helper():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/peers/{ticker}")
    data = response.json()
    db_pct = db.get_peer_percentiles(ticker)
    pct = data["percentiles"]
    assert pct is not None
    for field in pct:
        assert pct[field] == db_pct.get(field)


# ---------------------------------------------------------------------------
# 6. peer members match get_peer_group_members()
# ---------------------------------------------------------------------------


def test_peer_members_match():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/peers/{ticker}")
    data = response.json()
    peer_group = db.get_peer_groups(ticker)
    db_members = db.get_peer_group_members(peer_group)
    db_ids = {m["company_id"] for m in db_members}
    api_ids = {p["peer_company_id"] for p in data["peers"]}
    assert db_ids == api_ids


# ---------------------------------------------------------------------------
# 7. unknown company → 404
# ---------------------------------------------------------------------------


def test_unknown_company_peers_404():
    response = client.get("/api/v1/peers/THIS_COMPANY_DOES_NOT_EXIST")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 8. company without peer group → 200 with empty peers
# ---------------------------------------------------------------------------


def test_company_without_peers_200_empty():
    ticker = _company_without_peers()
    assert ticker is not None, "No company without a peer group found"
    response = client.get(f"/api/v1/peers/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert data["peer_group_name"] is None
    assert data["overall_peer_score"] is None
    assert data["percentiles"] is None
    assert data["peers"] == []


# ---------------------------------------------------------------------------
# 9. JSON serializable
# ---------------------------------------------------------------------------


def test_peers_json_serializable():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/peers/{ticker}")
    assert _json_serializable(response.json())

    # Also test the no-peer-group case
    ticker2 = _company_without_peers()
    if ticker2:
        response2 = client.get(f"/api/v1/peers/{ticker2}")
        assert _json_serializable(response2.json())


# ---------------------------------------------------------------------------
# 10. Day 39 /companies/{id}/peers still works
# ---------------------------------------------------------------------------


def test_day39_companies_peers_still_works():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/companies/{ticker}/peers")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == ticker
    assert data["peer_group_name"] is not None
    assert len(data["peers"]) > 0
