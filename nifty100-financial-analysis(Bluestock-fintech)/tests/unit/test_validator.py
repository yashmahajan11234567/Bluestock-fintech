"""
Tests for validator.py — DQ-01 through DQ-04 validation rules.
"""

import pytest
import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parents[2] / 'src'))

from etl.validator import (
    check_primary_key_uniqueness,
    check_composite_key_uniqueness,
    check_foreign_key_integrity,
    check_balance_sheet_equation,
    check_operating_profit_margin,
    check_positive_sales,
    check_positive_total_assets,
    check_net_cash_flow_consistency,
    check_dividend_payout_validation,
    check_url_validation,
    check_year_validation,
    check_duplicate_stock_prices,
    check_eps_sign_consistency,
    check_tax_percentage_validation,
    check_dataset_coverage_validation,
    check_critical_nulls,
)


@pytest.fixture
def db_conn():
    """In-memory SQLite database with schema + base test data for all DQ checks."""
    conn = sqlite3.connect(':memory:')
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_path = Path(__file__).parents[2] / 'db' / 'schema.sql'
    with open(schema_path, 'r') as f:
        for statement in f.read().split(';'):
            stmt = statement.strip()
            if stmt:
                try:
                    conn.execute(stmt)
                except sqlite3.Error:
                    pass

    cursor = conn.cursor()

    # Companies (needed for FK checks)
    cursor.execute("""
        INSERT INTO companies (id, company_name, face_value, book_value)
        VALUES ('C1', 'Company One', 10.0, 50.0)
    """)
    cursor.execute("""
        INSERT INTO companies (id, company_name, face_value, book_value)
        VALUES ('C2', 'Company Two', 5.0, 30.0)
    """)

    # profitandloss — DQ-02 target
    cursor.execute("""
        INSERT INTO profitandloss (id, company_id, year, sales, net_profit, eps)
        VALUES (1, 'C1', '2023', 1000, 200, 10.0)
    """)
    cursor.execute("""
        INSERT INTO profitandloss (id, company_id, year, sales, net_profit, eps)
        VALUES (2, 'C2', '2023', 500, 50, 5.0)
    """)

    # balancesheet — DQ-02 and DQ-04 target
    # Balanced: assets=380 = fixed_assets(250)+cwip(50)+investments(50)+other_asset(30)
    #           liabilities=80 = borrowings(50)+other_liabilities(30)
    #           equation: 380 = 80 + equity_capital(100) + reserves(200)
    cursor.execute("""
        INSERT INTO balancesheet (id, company_id, year,
            equity_capital, reserves, borrowings, other_liabilities, total_liabilities,
            fixed_assets, cwip, investments, other_asset, total_assets)
        VALUES (1, 'C1', '2023',
            100, 200, 50, 30, 80,
            250, 50, 50, 30, 380)
    """)

    # cashflow
    cursor.execute("""
        INSERT INTO cashflow (id, company_id, year, operating_activity, investing_activity,
                              financing_activity, net_cash_flow)
        VALUES (1, 'C1', '2023', 150, -50, -30, 70)
    """)

    # financial_ratios — DQ-02 target
    cursor.execute("""
        INSERT INTO financial_ratios (id, company_id, year, earnings_per_share, dividend_payout_ratio_pct)
        VALUES (1, 'C1', '2023', 10.0, 30.0)
    """)

    # documents — DQ-02 target (uses Year, not year)
    cursor.execute("""
        INSERT INTO documents (id, company_id, Year, Annual_Report)
        VALUES (1, 'C1', 2023, 'http://example.com/report.pdf')
    """)

    # FK target tables with valid data
    cursor.execute("""
        INSERT INTO sectors (company_id, broad_sector, index_weight_pct, market_cap_category)
        VALUES ('C1', 'Technology', 0.05, 'Large Cap')
    """)
    cursor.execute("""
        INSERT INTO stock_prices (company_id, date, close_price)
        VALUES ('C1', '2023-12-31', 105.0)
    """)
    cursor.execute("""
        INSERT INTO analysis (company_id, compounded_sales_growth, compounded_profit_growth)
        VALUES ('C1', '10%', '15%')
    """)

    conn.commit()
    yield conn
    conn.close()


# =============================================================================
# DQ-01: Primary Key Uniqueness
# =============================================================================

def test_dq01_clean_data_returns_no_failures(db_conn):
    """When all primary keys are unique, no failures are reported."""
    failures = check_primary_key_uniqueness(db_conn)
    assert failures == []


# =============================================================================
# DQ-02: Composite Key (company_id, year) Uniqueness
# =============================================================================

def test_dq02_clean_data_returns_no_failures(db_conn):
    """When (company_id, year) combos are unique across all tables, no failures."""
    failures = check_composite_key_uniqueness(db_conn)
    assert failures == []


def test_dq02_duplicate_in_profitandloss(db_conn):
    """A duplicate (company_id, year) in profitandloss is detected."""
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO profitandloss (id, company_id, year, sales)
        VALUES (99, 'C1', '2023', 999)
    """)
    db_conn.commit()

    failures = check_composite_key_uniqueness(db_conn)
    matching = [f for f in failures if f['table'] == 'profitandloss']
    assert len(matching) >= 1
    assert matching[0]['rule_id'] == 'DQ-02'
    assert matching[0]['severity'] == 'CRITICAL'
    assert 'C1' in matching[0]['value']
    assert '2023' in matching[0]['value']


def test_dq02_duplicate_in_balancesheet(db_conn):
    """A duplicate (company_id, year) in balancesheet is detected."""
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO balancesheet (id, company_id, year, total_assets)
        VALUES (99, 'C1', '2023', 999)
    """)
    db_conn.commit()

    failures = check_composite_key_uniqueness(db_conn)
    matching = [f for f in failures if f['table'] == 'balancesheet']
    assert len(matching) >= 1


def test_dq02_duplicate_with_null_year(db_conn):
    """Duplicate (company_id, NULL) combos are detected."""
    cursor = db_conn.cursor()
    # Insert two rows with same company_id and NULL year
    cursor.execute("""
        INSERT INTO profitandloss (id, company_id, year, sales)
        VALUES (91, 'C1', NULL, 100)
    """)
    cursor.execute("""
        INSERT INTO profitandloss (id, company_id, year, sales)
        VALUES (92, 'C1', NULL, 200)
    """)
    db_conn.commit()

    failures = check_composite_key_uniqueness(db_conn)
    matching = [f for f in failures if f['table'] == 'profitandloss']
    assert len(matching) >= 1


# =============================================================================
# DQ-03: Foreign Key Integrity
# =============================================================================

def test_dq03_all_foreign_keys_valid(db_conn):
    """When all company_id values reference existing companies, no failures."""
    failures = check_foreign_key_integrity(db_conn)
    assert failures == []


def test_dq03_invalid_company_id_detected():
    """A row referencing a non-existent company_id is flagged."""
    # Use a connection without FK enforcement so we can create orphaned rows.
    # The schema.sql file contains PRAGMA foreign_keys = ON, so we skip PRAGMA
    # statements to keep enforcement off for this test.
    conn = sqlite3.connect(':memory:')
    schema_path = Path(__file__).parents[2] / 'db' / 'schema.sql'
    with open(schema_path, 'r') as f:
        for statement in f.read().split(';'):
            stmt = statement.strip()
            if stmt and not stmt.upper().startswith('PRAGMA'):
                try:
                    conn.execute(stmt)
                except sqlite3.Error:
                    pass

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO companies (id, company_name) VALUES ('VALID', 'Valid Company')
    """)
    cursor.execute("""
        INSERT INTO sectors (company_id, broad_sector, market_cap_category)
        VALUES ('GHOST', 'Finance', 'Micro Cap')
    """)
    conn.commit()

    failures = check_foreign_key_integrity(conn)
    conn.close()

    matching = [f for f in failures if f['table'] == 'sectors']
    assert len(matching) >= 1
    assert matching[0]['rule_id'] == 'DQ-03'
    assert matching[0]['severity'] == 'CRITICAL'
    assert 'GHOST' in str(matching[0]['value'])


def test_dq03_no_companies_table_returns_no_fk_failures():
    """When companies table is empty, any FK row is flagged as invalid."""
    conn = sqlite3.connect(':memory:')
    schema_path = Path(__file__).parents[2] / 'db' / 'schema.sql'
    with open(schema_path, 'r') as f:
        for statement in f.read().split(';'):
            stmt = statement.strip()
            if stmt and not stmt.upper().startswith('PRAGMA'):
                try:
                    conn.execute(stmt)
                except sqlite3.Error:
                    pass

    cursor = conn.cursor()
    # Insert a valid company first so all FK references are valid at insert time
    cursor.execute("INSERT INTO companies (id, company_name) VALUES ('TEMP', 'Temp Co')")
    cursor.execute("""
        INSERT INTO sectors (company_id, broad_sector, market_cap_category)
        VALUES ('TEMP', 'Finance', 'Large Cap')
    """)
    conn.commit()

    # Delete the company to create orphaned rows (no FK enforcement since we skipped PRAGMA)
    cursor.execute("DELETE FROM companies WHERE id = 'TEMP'")
    conn.commit()

    failures = check_foreign_key_integrity(conn)
    conn.close()

    matching = [f for f in failures if f['table'] == 'sectors']
    assert len(matching) >= 1
    assert matching[0]['rule_id'] == 'DQ-03'


# =============================================================================
# DQ-04: Balance Sheet Equation
# =============================================================================

def test_dq04_balanced_equation_returns_no_failures(db_conn):
    """When assets=liabilities+equity and sub-components sum correctly, no failures."""
    failures = check_balance_sheet_equation(db_conn)
    assert failures == []


def test_dq04_total_assets_mismatch(db_conn):
    """When total_assets doesn't match sum of asset components, it's flagged."""
    cursor = db_conn.cursor()
    # Set total_assets to a value different from sum of components (250+50+50+30 = 380)
    cursor.execute("""
        UPDATE balancesheet SET total_assets = 999 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_balance_sheet_equation(db_conn)
    matching = [f for f in failures if f['column'] == 'total_assets']
    assert len(matching) == 1
    assert matching[0]['rule_id'] == 'DQ-04'
    assert matching[0]['severity'] == 'WARNING'


def test_dq04_total_liabilities_mismatch(db_conn):
    """When total_liabilities doesn't match sum of liability components, it's flagged."""
    cursor = db_conn.cursor()
    # Set total_liabilities to something other than 50+30=80
    cursor.execute("""
        UPDATE balancesheet SET total_liabilities = 200 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_balance_sheet_equation(db_conn)
    matching = [f for f in failures if f['column'] == 'total_liabilities']
    assert len(matching) == 1


def test_dq04_equation_mismatch(db_conn):
    """When assets != liabilities + equity, it's flagged."""
    cursor = db_conn.cursor()
    # Change reserves so equity changes but total_assets stays same
    cursor.execute("""
        UPDATE balancesheet SET reserves = 500 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_balance_sheet_equation(db_conn)
    matching = [f for f in failures if f['column'] == 'balance_sheet_equation']
    assert len(matching) == 1


# =============================================================================
# DQ-05: Operating Profit Margin
# =============================================================================

def test_dq05_opm_matches_calculation(db_conn):
    """When opm_percentage equals (operating_profit / sales) * 100, no failures."""
    cursor = db_conn.cursor()
    # operating_profit=200, sales=1000 → calculated OPM = 20.0%
    cursor.execute("""
        UPDATE profitandloss
        SET operating_profit = 200, opm_percentage = 20.0
        WHERE id = 1
    """)
    db_conn.commit()

    failures = check_operating_profit_margin(db_conn)
    assert failures == []


def test_dq05_opm_mismatch_detected(db_conn):
    """When stored opm_percentage differs from calculated value, it's flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss
        SET operating_profit = 200, opm_percentage = 99.9
        WHERE id = 1
    """)
    db_conn.commit()

    failures = check_operating_profit_margin(db_conn)
    matching = [f for f in failures if f['table'] == 'profitandloss']
    assert len(matching) == 1
    assert matching[0]['rule_id'] == 'DQ-05'
    assert matching[0]['severity'] == 'WARNING'
    assert matching[0]['column'] == 'opm_percentage'


def test_dq05_null_values_skipped(db_conn):
    """Rows where operating_profit or opm_percentage is NULL are skipped."""
    cursor = db_conn.cursor()
    # Set opm_percentage to NULL — row should be skipped
    cursor.execute("""
        UPDATE profitandloss
        SET operating_profit = 200, opm_percentage = NULL
        WHERE id = 1
    """)
    db_conn.commit()

    failures = check_operating_profit_margin(db_conn)
    # Second row (id=2, C2) also has NULL operating_profit/opm_percentage
    # so no rows should trigger the check
    assert failures == []


# =============================================================================
# DQ-06: Positive Sales
# =============================================================================

def test_dq06_positive_sales_no_failures(db_conn):
    """When all sales values are positive, no failures."""
    failures = check_positive_sales(db_conn)
    assert failures == []


def test_dq06_negative_sales_detected(db_conn):
    """A negative sales value is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET sales = -500 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_positive_sales(db_conn)
    assert len(failures) == 1
    assert failures[0]['rule_id'] == 'DQ-06'
    assert failures[0]['severity'] == 'WARNING'
    assert failures[0]['column'] == 'sales'
    assert failures[0]['value'] == -500


# =============================================================================
# DQ-07: Positive Total Assets
# =============================================================================

def test_dq07_positive_assets_no_failures(db_conn):
    """When total_assets is positive, no failures."""
    failures = check_positive_total_assets(db_conn)
    assert failures == []


def test_dq07_zero_total_assets_detected(db_conn):
    """total_assets of zero is flagged as non-positive."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE balancesheet SET total_assets = 0 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_positive_total_assets(db_conn)
    assert len(failures) == 1
    assert failures[0]['rule_id'] == 'DQ-07'


def test_dq07_negative_total_assets_detected(db_conn):
    """A negative total_assets value is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE balancesheet SET total_assets = -100 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_positive_total_assets(db_conn)
    assert len(failures) == 1


# =============================================================================
# DQ-08: Net Cash Flow Consistency
# =============================================================================

def test_dq08_cash_flow_matches_components(db_conn):
    """When net_cash_flow equals sum of activities, no failures."""
    # Fixture: operating=150, investing=-50, financing=-30 → sum=70 → net=70
    failures = check_net_cash_flow_consistency(db_conn)
    assert failures == []


def test_dq08_cash_flow_mismatch_detected(db_conn):
    """When net_cash_flow differs from the sum of activities, it's flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE cashflow SET net_cash_flow = 999 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_net_cash_flow_consistency(db_conn)
    assert len(failures) == 1
    assert failures[0]['rule_id'] == 'DQ-08'
    assert failures[0]['severity'] == 'WARNING'
    assert failures[0]['column'] == 'net_cash_flow'


# =============================================================================
# DQ-09: Dividend Payout Validation
# =============================================================================

def test_dq09_dividend_payout_matches(db_conn):
    """When dividend_payout matches financial_ratios.dividend_payout_ratio_pct, no failures."""
    cursor = db_conn.cursor()
    # Set dividend_payout to match financial_ratios value (30.0)
    cursor.execute("""
        UPDATE profitandloss
        SET dividend_payout = 30.0
        WHERE id = 1
    """)
    db_conn.commit()

    failures = check_dividend_payout_validation(db_conn)
    assert failures == []


def test_dq09_dividend_payout_mismatch_detected(db_conn):
    """When dividend_payout differs from dividend_payout_ratio_pct, it's flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss
        SET dividend_payout = 99.0
        WHERE id = 1
    """)
    db_conn.commit()

    failures = check_dividend_payout_validation(db_conn)
    assert len(failures) == 1
    assert failures[0]['rule_id'] == 'DQ-09'
    assert failures[0]['severity'] == 'WARNING'
    assert failures[0]['column'] == 'dividend_payout'
    assert '99.0' in str(failures[0]['value']) or '99' in str(failures[0]['value'])


def test_dq09_null_dividend_skipped(db_conn):
    """Rows where dividend_payout is NULL are not checked (no JOIN match)."""
    # Fixture already has dividend_payout=NULL for all rows
    failures = check_dividend_payout_validation(db_conn)
    assert failures == []


# =============================================================================
# DQ-10: URL Validation
# =============================================================================

def test_dq10_valid_urls_no_failures(db_conn):
    """When all Annual_Report URLs start with http:// or https://, no failures."""
    # Fixture has 'http://example.com/report.pdf' — valid
    failures = check_url_validation(db_conn)
    assert failures == []


def test_dq10_invalid_url_detected(db_conn):
    """A URL that doesn't start with http:// or https:// is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE documents SET Annual_Report = 'not-a-url' WHERE id = 1
    """)
    db_conn.commit()

    failures = check_url_validation(db_conn)
    assert len(failures) == 1
    assert failures[0]['rule_id'] == 'DQ-10'
    assert failures[0]['severity'] == 'WARNING'
    assert failures[0]['table'] == 'documents'
    assert failures[0]['column'] == 'Annual_Report'
    assert failures[0]['value'] == 'not-a-url'


def test_dq10_null_url_skipped(db_conn):
    """Rows where Annual_Report is NULL or empty are not checked."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE documents SET Annual_Report = NULL WHERE id = 1
    """)
    db_conn.commit()

    failures = check_url_validation(db_conn)
    assert failures == []


# =============================================================================
# DQ-11: Year Validation
# =============================================================================

def test_dq11_years_in_range_no_failures(db_conn):
    """When all years are within [1900, current_year+1], no failures."""
    # Fixture has years 2023 — valid
    failures = check_year_validation(db_conn)
    assert failures == []


def test_dq11_year_too_old_detected(db_conn):
    """A year below 1900 is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET year = 1800 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_year_validation(db_conn)
    matching = [f for f in failures if f['table'] == 'profitandloss']
    assert len(matching) >= 1
    assert matching[0]['rule_id'] == 'DQ-11'
    assert matching[0]['severity'] == 'INFO'
    assert matching[0]['column'] == 'year'


def test_dq11_year_too_new_detected(db_conn):
    """A year beyond current_year+1 is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE balancesheet SET year = 2100 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_year_validation(db_conn)
    matching = [f for f in failures if f['table'] == 'balancesheet']
    assert len(matching) >= 1


def test_dq11_documents_year_out_of_range(db_conn):
    """Year in the documents table (column 'Year') is also validated."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE documents SET Year = 1899 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_year_validation(db_conn)
    matching = [f for f in failures if f['table'] == 'documents']
    assert len(matching) >= 1


# =============================================================================
# DQ-12: Duplicate Stock Prices
# =============================================================================

def test_dq12_unique_stock_prices_no_failures(db_conn):
    """When (company_id, date) pairs are unique, no failures."""
    failures = check_duplicate_stock_prices(db_conn)
    assert failures == []


def test_dq12_duplicate_stock_price_detected(db_conn):
    """A duplicate (company_id, date) in stock_prices is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO stock_prices (company_id, date, close_price)
        VALUES ('C1', '2023-12-31', 999.0)
    """)
    db_conn.commit()

    failures = check_duplicate_stock_prices(db_conn)
    assert len(failures) >= 1
    assert failures[0]['rule_id'] == 'DQ-12'
    assert failures[0]['severity'] == 'CRITICAL'
    assert failures[0]['table'] == 'stock_prices'
    assert '2023-12-31' in str(failures[0]['value'])


# =============================================================================
# DQ-13: EPS Sign Consistency
# =============================================================================

def test_dq13_eps_sign_matches(db_conn):
    """When eps and net_profit have the same sign, and eps matches financial_ratios, no failures."""
    # Fixture: C1 has eps=10.0, net_profit=200 (same sign ✓)
    #          financial_ratios C1 has earnings_per_share=10.0 (matches ✓)
    failures = check_eps_sign_consistency(db_conn)
    assert failures == []


def test_dq13_eps_sign_mismatch_detected(db_conn):
    """When eps is negative but net_profit is positive, it's flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET eps = -10.0 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_eps_sign_consistency(db_conn)
    matching = [f for f in failures if 'sign' in f['message'].lower()]
    assert len(matching) >= 1
    assert matching[0]['rule_id'] == 'DQ-13'
    assert matching[0]['severity'] == 'WARNING'
    assert matching[0]['column'] == 'eps'


def test_dq13_eps_cross_table_mismatch_detected(db_conn):
    """When eps differs from financial_ratios.earnings_per_share, it's flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET eps = 99.0 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_eps_sign_consistency(db_conn)
    matching = [f for f in failures if 'mismatch' in f['message'].lower()]
    assert len(matching) >= 1
    assert '99.0' in str(matching[0]['value']) or '99' in str(matching[0]['value'])


# =============================================================================
# DQ-14: Tax Percentage Validation
# =============================================================================

def test_dq14_tax_in_range_no_failures(db_conn):
    """When tax_percentage is between 0 and 100, no failures."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET tax_percentage = 25.5 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_tax_percentage_validation(db_conn)
    assert failures == []


def test_dq14_negative_tax_detected(db_conn):
    """A negative tax_percentage is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET tax_percentage = -5 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_tax_percentage_validation(db_conn)
    assert len(failures) == 1
    assert failures[0]['rule_id'] == 'DQ-14'
    assert failures[0]['severity'] == 'WARNING'
    assert failures[0]['column'] == 'tax_percentage'
    assert failures[0]['value'] == -5


def test_dq14_tax_above_100_detected(db_conn):
    """A tax_percentage above 100 is flagged."""
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE profitandloss SET tax_percentage = 150 WHERE id = 1
    """)
    db_conn.commit()

    failures = check_tax_percentage_validation(db_conn)
    assert len(failures) == 1
    assert failures[0]['value'] == 150


# =============================================================================
# DQ-15: Dataset Coverage Validation
# =============================================================================

def test_dq15_full_coverage_no_failures(db_conn):
    """When all fact tables have data for all companies, no failures."""
    cursor = db_conn.cursor()
    # Add C2 rows to tables that are currently C1-only
    cursor.execute("""
        INSERT INTO balancesheet (id, company_id, year, total_assets)
        VALUES (2, 'C2', '2023', 500)
    """)
    cursor.execute("""
        INSERT INTO cashflow (id, company_id, year, net_cash_flow)
        VALUES (2, 'C2', '2023', 100)
    """)
    cursor.execute("""
        INSERT INTO financial_ratios (id, company_id, year, earnings_per_share)
        VALUES (2, 'C2', '2023', 5.0)
    """)
    db_conn.commit()

    failures = check_dataset_coverage_validation(db_conn)
    assert failures == []


def test_dq15_partial_coverage_detected(db_conn):
    """When a fact table is missing companies, the shortfall is reported."""
    # Fixture: C2 has data in profitandloss but NOT in balancesheet, cashflow, financial_ratios
    failures = check_dataset_coverage_validation(db_conn)
    # At least one table should report incomplete coverage
    assert len(failures) >= 1
    for f in failures:
        assert f['rule_id'] == 'DQ-15'
        assert f['severity'] == 'INFO'
        assert 'coverage' in f['message'].lower() or 'out of' in f['message']


# =============================================================================
# DQ-16: Critical NULL Field Validation
# =============================================================================

def test_dq16_no_critical_nulls(db_conn):
    """When all critical columns are populated, no failures."""
    failures = check_critical_nulls(db_conn)
    assert failures == []


def test_dq16_critical_null_detected(db_conn):
    """A NULL in a nullable critical column is flagged."""
    cursor = db_conn.cursor()
    # profitandloss.sales has no NOT NULL constraint in the schema
    cursor.execute("""
        UPDATE profitandloss SET sales = NULL WHERE id = 1
    """)
    db_conn.commit()

    failures = check_critical_nulls(db_conn)
    matching = [f for f in failures if f['table'] == 'profitandloss' and f['column'] == 'sales']
    assert len(matching) >= 1
    assert matching[0]['rule_id'] == 'DQ-16'
    assert matching[0]['severity'] == 'CRITICAL'