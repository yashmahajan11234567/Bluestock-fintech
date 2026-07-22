"""
Integration tests for src/analytics/db_integration.py.

Verifies that the db_integration module correctly reads raw financial data
from the database, computes ratios, and inserts results into the
financial_ratios table.
"""

import sys
from pathlib import Path
import sqlite3

import pytest

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import module directly using importlib to avoid package conflicts
import importlib.util
db_integration_path = Path(__file__).parents[2] / "src" / "analytics" / "db_integration.py"
spec = importlib.util.spec_from_file_location("analytics.db_integration", db_integration_path)
analytics_db_integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_db_integration)

get_raw_financial_rows = analytics_db_integration.get_raw_financial_rows
compute_row_metrics = analytics_db_integration.compute_row_metrics
populate_financial_ratios = analytics_db_integration.populate_financial_ratios


DB_PATH = Path(__file__).parents[2] / "db" / "nifty100.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the test database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_test_database() -> sqlite3.Connection:
    """Create an in-memory SQLite database with schema and sample data for testing.

    Builds all tables needed by get_raw_financial_rows() and populate_financial_ratios(),
    populated with known test values so ratio computations are deterministic.
    """
    conn = sqlite3.connect(":memory:")

    # Create tables
    conn.executescript("""
        CREATE TABLE companies (
            id TEXT PRIMARY KEY,
            company_name TEXT,
            book_value REAL
        );
        CREATE TABLE profitandloss (
            id INTEGER PRIMARY KEY,
            company_id TEXT NOT NULL,
            year TEXT,
            sales INTEGER,
            operating_profit REAL,
            other_income INTEGER,
            interest INTEGER,
            net_profit INTEGER,
            eps REAL,
            dividend_payout REAL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );
        CREATE TABLE balancesheet (
            id INTEGER PRIMARY KEY,
            company_id TEXT NOT NULL,
            year TEXT,
            equity_capital INTEGER,
            reserves INTEGER,
            borrowings INTEGER,
            total_assets INTEGER,
            investments INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );
        CREATE TABLE cashflow (
            id INTEGER PRIMARY KEY,
            company_id TEXT NOT NULL,
            year TEXT,
            operating_activity REAL,
            investing_activity REAL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );
        CREATE TABLE financial_ratios (
            id INTEGER PRIMARY KEY,
            company_id TEXT NOT NULL,
            year TEXT,
            net_profit_margin_pct REAL,
            operating_profit_margin_pct REAL,
            return_on_equity_pct REAL,
            debt_to_equity REAL,
            interest_coverage REAL,
            asset_turnover REAL,
            free_cash_flow_cr REAL,
            capex_cr REAL,
            earnings_per_share REAL,
            book_value_per_share REAL,
            dividend_payout_ratio_pct REAL,
            total_debt_cr INTEGER,
            cash_from_operations_cr REAL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );
    """)

    # Insert test data: two companies with known values
    conn.executescript("""
        INSERT INTO companies (id, company_name, book_value) VALUES
            ('TCS', 'Tata Consultancy Services', 200.0),
            ('TESTCORP', 'Test Corporation', 50.0);

        -- profitandloss: TCS has healthy profits, TESTCORP has some NULLs
        INSERT INTO profitandloss (company_id, year, sales, operating_profit, other_income, interest, net_profit, eps, dividend_payout) VALUES
            ('TCS', '2023', 100000, 25000, 2000, 500, 20000, 50.0, 40.0),
            ('TCS', '2022', 90000, 22000, 1500, 400, 18000, 45.0, 35.0),
            ('TESTCORP', '2023', 50000, 8000, 1000, 2000, 5000, 10.0, 20.0),
            ('TESTCORP', '2022', NULL, NULL, NULL, NULL, NULL, NULL, NULL);

        -- balancesheet
        INSERT INTO balancesheet (company_id, year, equity_capital, reserves, borrowings, total_assets, investments) VALUES
            ('TCS', '2023', 5000, 30000, 2000, 80000, 10000),
            ('TCS', '2022', 5000, 25000, 3000, 70000, 8000),
            ('TESTCORP', '2023', 2000, 8000, 10000, 30000, 2000),
            ('TESTCORP', '2022', 2000, 8000, 10000, 30000, 2000);

        -- cashflow
        INSERT INTO cashflow (company_id, year, operating_activity, investing_activity) VALUES
            ('TCS', '2023', 22000, -5000),
            ('TCS', '2022', 20000, -4000),
            ('TESTCORP', '2023', 6000, -3000),
            ('TESTCORP', '2022', NULL, NULL);
    """)

    return conn


class TestGetRawFinancialRows:
    """Tests for get_raw_financial_rows()."""

    def test_returns_list_of_dicts(self):
        """Should return a list of dicts with raw financial data."""
        conn = get_connection()
        try:
            rows = get_raw_financial_rows(conn)
            assert isinstance(rows, list)
            assert len(rows) > 0
            row = rows[0]
            assert isinstance(row, dict)
        finally:
            conn.close()

    def test_contains_expected_keys(self):
        """Each row should contain the expected financial data keys."""
        conn = get_connection()
        try:
            rows = get_raw_financial_rows(conn)
            row = rows[0]
            expected_keys = [
                "company_id",
                "sales",
                "net_profit",
                "operating_profit",
                "equity_capital",
                "reserves",
                "borrowings",
                "total_assets",
                "operating_cashflow",
                "investing_activity",
            ]
            for key in expected_keys:
                assert key in row, f"Missing key: {key}"
        finally:
            conn.close()


class TestComputeRowMetrics:
    """Tests for compute_row_metrics()."""

    def test_returns_dict_with_expected_keys(self):
        """Should return a dict with all financial_ratios columns."""
        metrics = compute_row_metrics({
            "company_id": "TEST",
            "year": "2023",
            "net_profit": 100,
            "sales": 1000,
            "operating_profit": 200,
            "equity_capital": 100,
            "reserves": 200,
            "borrowings": 50,
            "total_assets": 500,
            "other_income": 30,
            "interest": 20,
            "investments": 0,
            "operating_cashflow": 150,
            "investing_activity": -50,
            "eps": 5.0,
            "book_value": 30.0,
            "dividend_payout": 25.0,
        })

        expected_keys = [
            "company_id",
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "total_debt_cr",
            "cash_from_operations_cr",
        ]
        for key in expected_keys:
            assert key in metrics, f"Missing key: {key}"

    def test_computes_ratios_correctly(self):
        """Should compute correct ratio values."""
        metrics = compute_row_metrics({
            "company_id": "TEST",
            "year": "2023",
            "net_profit": 100,
            "sales": 1000,
            "operating_profit": 200,
            "equity_capital": 100,
            "reserves": 200,
            "borrowings": 50,
            "total_assets": 500,
            "other_income": 30,
            "interest": 20,
            "investments": 0,
            "operating_cashflow": 150,
            "investing_activity": -50,
            "eps": 5.0,
            "book_value": 30.0,
            "dividend_payout": 25.0,
        })

        # net_profit_margin_pct = (100 / 1000) * 100 = 10.0%
        assert metrics["net_profit_margin_pct"] == 10.0

        # operating_profit_margin_pct = (200 / 1000) * 100 = 20.0%
        assert metrics["operating_profit_margin_pct"] == 20.0

        # return_on_equity_pct = 100 / (100 + 200) * 100 = 33.33%
        from math import isclose
        assert isclose(metrics["return_on_equity_pct"], 33.333333333333336)

        # debt_to_equity = 50 / (100 + 200) = 0.1667
        assert isclose(metrics["debt_to_equity"], 50 / 300)

        # interest_coverage = (200 + 30) / 20 = 11.5
        assert metrics["interest_coverage"] == 11.5

        # asset_turnover = 1000 / 500 = 2.0
        assert metrics["asset_turnover"] == 2.0

        # free_cash_flow_cr = 150 - (-(-50)) = 150 - 50 = 100
        # capex = -investing_activity = -(-50) = 50
        # fcf = 150 - 50 = 100
        assert metrics["free_cash_flow_cr"] == 100.0
        assert metrics["capex_cr"] == 50.0

        # Pass-through values
        assert metrics["earnings_per_share"] == 5.0
        assert metrics["book_value_per_share"] == 30.0
        assert metrics["dividend_payout_ratio_pct"] == 25.0
        assert metrics["total_debt_cr"] == 50
        assert metrics["cash_from_operations_cr"] == 150.0

    def test_none_inputs_handled(self):
        """None/zero values should produce None or handled defaults."""
        metrics = compute_row_metrics({
            "company_id": "TEST",
            "year": "2023",
            "net_profit": None,
            "sales": None,
            "operating_profit": None,
            "equity_capital": None,
            "reserves": None,
            "borrowings": None,
            "total_assets": None,
            "other_income": None,
            "interest": None,
            "investments": None,
            "operating_cashflow": None,
            "investing_activity": None,
            "eps": None,
            "book_value": None,
            "dividend_payout": None,
        })

        assert metrics["net_profit_margin_pct"] is None
        assert metrics["operating_profit_margin_pct"] is None
        assert metrics["return_on_equity_pct"] is None
        assert metrics["debt_to_equity"] is None
        assert metrics["interest_coverage"] is None
        assert metrics["asset_turnover"] is None
        assert metrics["free_cash_flow_cr"] is None
        assert metrics["capex_cr"] is None
        assert metrics["earnings_per_share"] is None
        assert metrics["book_value_per_share"] is None
        assert metrics["dividend_payout_ratio_pct"] is None

    def test_negative_values_handled(self):
        """Negative values should produce valid negative ratios."""
        metrics = compute_row_metrics({
            "company_id": "TEST",
            "year": "2023",
            "net_profit": -50,
            "sales": 1000,
            "operating_profit": -100,
            "equity_capital": 100,
            "reserves": 200,
            "borrowings": 50,
            "total_assets": 500,
            "other_income": 10,
            "interest": 20,
            "investments": 0,
            "operating_cashflow": -80,
            "investing_activity": -30,
            "eps": -2.0,
            "book_value": 25.0,
            "dividend_payout": 0.0,
        })

        # Negative net profit -> negative margins
        assert metrics["net_profit_margin_pct"] == -5.0
        assert metrics["operating_profit_margin_pct"] == -10.0
        assert metrics["return_on_equity_pct"] < 0
        assert metrics["free_cash_flow_cr"] < 0


class TestPopulateFinancialRatios:
    """Tests for populate_financial_ratios()."""

    def test_dry_run_returns_row_count(self):
        """Dry run should return row count without inserting."""
        conn = get_connection()
        try:
            count = populate_financial_ratios(conn, dry_run=True)
            assert isinstance(count, int)
            assert count > 0
        finally:
            conn.close()

    def test_insertion_succeeds(self):
        """Insertion should succeed and return the expected row count."""
        conn = create_test_database()
        try:
            dry_count = populate_financial_ratios(conn, dry_run=True)

            actual_count = populate_financial_ratios(conn)
            assert actual_count == dry_count
            assert actual_count > 0

            # Verify rows were inserted
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM financial_ratios")
            db_count = cursor.fetchone()[0]
            assert db_count == actual_count

            # Verify inserted data has valid company_ids
            cursor.execute(
                "SELECT company_id, year, net_profit_margin_pct FROM financial_ratios LIMIT 5"
            )
            inserted_rows = cursor.fetchall()
            for row in inserted_rows:
                assert row[0] is not None  # company_id
        finally:
            conn.close()

    def test_inserted_values_are_correct(self):
        """Verify that specific companies have correct computed values."""
        conn = create_test_database()
        try:
            populate_financial_ratios(conn)

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT company_id,
                       net_profit_margin_pct,
                       operating_profit_margin_pct,
                       return_on_equity_pct,
                       debt_to_equity,
                       asset_turnover
                FROM financial_ratios
                WHERE company_id = 'TCS'
                  AND year = '2023'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "TCS 2023 row should exist"
            _, npm, opm, roe, dte, at_ratio = row

            # net_profit_margin_pct = 20000 / 100000 * 100 = 20.0%
            from math import isclose
            assert npm is not None and isclose(npm, 20.0)

            # operating_profit_margin_pct = 25000 / 100000 * 100 = 25.0%
            assert opm is not None and isclose(opm, 25.0)

            # return_on_equity_pct = 20000 / (5000 + 30000) * 100 = ~57.14%
            assert roe is not None and isclose(roe, 20000 / 35000 * 100)

            # debt_to_equity = 2000 / (5000 + 30000) = ~0.0571
            assert dte is not None and isclose(dte, 2000 / 35000)

            # asset_turnover = 100000 / 80000 = 1.25
            assert at_ratio is not None and isclose(at_ratio, 1.25)
        finally:
            conn.close()

    def test_null_values_are_stored_correctly(self):
        """Rows with missing data should store NULL for those columns."""
        conn = create_test_database()
        try:
            populate_financial_ratios(conn)

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM financial_ratios
                WHERE company_id = 'TESTCORP'
                  AND year = '2022'
                  AND net_profit_margin_pct IS NULL
                  AND operating_profit_margin_pct IS NULL
                """
            )
            null_rows = cursor.fetchone()[0]
            # The TESTCORP 2022 row has all NULL inputs, so it should produce
            # at least one row with NULL ratios
            assert null_rows >= 1
        finally:
            conn.close()