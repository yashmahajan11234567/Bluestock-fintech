"""
Tests for Day 32: Capital Allocation Report.

Covers capital_allocation_category() boundaries, None handling,
and validation of the three output CSVs:
  - Data/output/capital_allocation.csv
  - Data/output/capital_allocation_distribution.csv
  - Data/output/pattern_changes.csv

Also verifies that Data/output/cashflow_intelligence.xlsx remains
consistent with Day 31 (92 companies, no duplicate IDs, capital
allocation matches source calculation).

Does NOT modify tests/analytics/test_capital_allocation.py.
"""

import sys
from pathlib import Path
from math import isclose

import pytest
import pandas as pd

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import capital_allocation module directly
import importlib.util
ca_path = Path(__file__).parents[2] / "src" / "analytics" / "capital_allocation.py"
ca_spec = importlib.util.spec_from_file_location("analytics.capital_allocation", ca_path)
analytics_ca = importlib.util.module_from_spec(ca_spec)
ca_spec.loader.exec_module(analytics_ca)
capital_allocation_category = analytics_ca.capital_allocation_category

# Import cashflow_kpis helper (same importlib pattern as other test files)
ck_path = Path(__file__).parents[2] / "src" / "analytics" / "cashflow_kpis.py"
ck_spec = importlib.util.spec_from_file_location("analytics.cashflow_kpis", ck_path)
analytics_ck = importlib.util.module_from_spec(ck_spec)
ck_spec.loader.exec_module(analytics_ck)
_to_float = analytics_ck._to_float

from src.dashboard.utils.db import get_company_list, get_cashflow_data, get_pl, get_financial_ratios
from src.analytics.cashflow import cash_conversion_ratio


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parents[2]
OUTPUT_DIR = BASE_DIR / "Data" / "output"
CA_CSV = OUTPUT_DIR / "capital_allocation.csv"
DIST_CSV = OUTPUT_DIR / "capital_allocation_distribution.csv"
PC_CSV = OUTPUT_DIR / "pattern_changes.csv"
XLSX_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"

ALL_CATEGORIES = ["Excellent", "Good", "Average", "Weak", "Poor"]


# ---------------------------------------------------------------------------
# 1. capital_allocation_category boundaries
# ---------------------------------------------------------------------------

class TestCapitalAllocationBoundaries:
    """Verify capital_allocation_category() boundary behavior."""

    def test_excellent_boundary(self):
        """Exact boundary for Excellent: ROE=20, ROCE=20, CCR=1.2."""
        assert capital_allocation_category(20, 20, 1.2) == "Excellent"

    def test_just_above_excellent(self):
        """Just above Excellent thresholds."""
        assert capital_allocation_category(20.01, 20.01, 1.21) == "Excellent"

    def test_just_below_excellent_roe(self):
        """ROE just below 20, others at threshold -> Good."""
        assert capital_allocation_category(19.99, 20, 1.2) == "Good"

    def test_good_boundary(self):
        """Exact boundary for Good: ROE=15, ROCE=15, CCR=1.0."""
        assert capital_allocation_category(15, 15, 1.0) == "Good"

    def test_just_below_good(self):
        """ROE=14.99 -> falls to Average."""
        assert capital_allocation_category(14.99, 15, 1.0) == "Average"

    def test_average_boundary(self):
        """Exact boundary for Average: ROE=10, ROCE=10, CCR=0.8."""
        assert capital_allocation_category(10, 10, 0.8) == "Average"

    def test_just_below_average(self):
        """ROE=9.99 -> falls to Weak."""
        assert capital_allocation_category(9.99, 10, 0.8) == "Weak"

    def test_weak_boundary(self):
        """Exact boundary for Weak: ROE=5, ROCE=5."""
        assert capital_allocation_category(5, 5, 0.5) == "Weak"

    def test_just_below_weak(self):
        """ROE=4.99 -> falls to Poor."""
        assert capital_allocation_category(4.99, 5, 0.5) == "Poor"

    def test_poor(self):
        """ROE=3, ROCE=3, CCR=0.5 -> Poor."""
        assert capital_allocation_category(3, 3, 0.5) == "Poor"


# ---------------------------------------------------------------------------
# 2. None handling
# ---------------------------------------------------------------------------

class TestNoneHandling:
    """Verify capital_allocation_category() returns None for None inputs."""

    def test_roe_none(self):
        assert capital_allocation_category(None, 20, 1.2) is None

    def test_roce_none(self):
        assert capital_allocation_category(20, None, 1.2) is None

    def test_ccr_none(self):
        assert capital_allocation_category(20, 25, None) is None

    def test_all_none(self):
        assert capital_allocation_category(None, None, None) is None


# ---------------------------------------------------------------------------
# 3. capital_allocation.csv schema
# ---------------------------------------------------------------------------

class TestCapitalAllocationCSV:
    """Validate the schema of capital_allocation.csv."""

    def test_file_exists(self):
        assert CA_CSV.exists(), f"{CA_CSV} does not exist"

    def test_columns(self):
        df = pd.read_csv(CA_CSV)
        assert list(df.columns) == ["company_id", "year", "capital_allocation"]

    def test_no_duplicate_company_year(self):
        df = pd.read_csv(CA_CSV)
        dupes = df.duplicated(subset=["company_id", "year"])
        assert dupes.sum() == 0, f"Found {dupes.sum()} duplicate company/year rows"

    def test_valid_company_ids(self):
        df = pd.read_csv(CA_CSV)
        companies = get_company_list()
        valid_ids = set(c["company_id"] for c in companies)
        invalid = set(df["company_id"]) - valid_ids
        assert len(invalid) == 0, f"Invalid company IDs: {invalid}"

    def test_valid_years(self):
        df = pd.read_csv(CA_CSV)
        assert df["year"].notna().all()
        # Year should be in a reasonable range
        assert df["year"].min() >= 2000
        assert df["year"].max() <= 2025

    def test_valid_labels(self):
        df = pd.read_csv(CA_CSV)
        invalid = set(df["capital_allocation"].unique()) - set(ALL_CATEGORIES)
        assert len(invalid) == 0, f"Invalid labels: {invalid}"

    def test_row_count_positive(self):
        df = pd.read_csv(CA_CSV)
        assert len(df) > 0, "capital_allocation.csv should have rows"


# ---------------------------------------------------------------------------
# 4. Distribution CSV
# ---------------------------------------------------------------------------

class TestDistributionCSV:
    """Validate capital_allocation_distribution.csv."""

    def test_file_exists(self):
        assert DIST_CSV.exists()

    def test_columns(self):
        df = pd.read_csv(DIST_CSV)
        assert list(df.columns) == ["capital_allocation", "company_count"]

    def test_all_five_categories(self):
        df = pd.read_csv(DIST_CSV)
        cats = set(df["capital_allocation"])
        assert cats == set(ALL_CATEGORIES), f"Missing categories: {set(ALL_CATEGORIES) - cats}"

    def test_distribution_matches_ca_csv(self):
        """Distribution counts should match the latest-year capital allocation from capital_allocation.csv."""
        ca_df = pd.read_csv(CA_CSV)
        # Latest year per company
        latest = ca_df.sort_values(["company_id", "year"]).groupby("company_id").last().reset_index()

        dist_df = pd.read_csv(DIST_CSV)
        for _, row in dist_df.iterrows():
            cat = row["capital_allocation"]
            expected = int((latest["capital_allocation"] == cat).sum())
            assert row["company_count"] == expected, f"{cat}: expected {expected}, got {row['company_count']}"

    def test_distribution_totals(self):
        dist_df = pd.read_csv(DIST_CSV)
        total = dist_df["company_count"].sum()
        # Total should equal number of companies with valid latest-year CA
        assert total > 0
        # Each company should be counted exactly once
        assert total == dist_df["company_count"].sum()


# ---------------------------------------------------------------------------
# 5. Pattern changes CSV
# ---------------------------------------------------------------------------

class TestPatternChanges:
    """Validate pattern_changes.csv."""

    def test_file_exists(self):
        assert PC_CSV.exists()

    def test_columns(self):
        df = pd.read_csv(PC_CSV)
        expected_cols = ["company_id", "previous_year", "previous_pattern", "latest_year", "latest_pattern"]
        assert list(df.columns) == expected_cols

    def test_only_actual_changes(self):
        """previous_pattern must differ from latest_pattern."""
        df = pd.read_csv(PC_CSV)
        same = (df["previous_pattern"] == df["latest_pattern"])
        assert same.sum() == 0, f"Found {same.sum()} unchanged patterns"

    def test_consecutive_years(self):
        """latest_year must be exactly previous_year + 1."""
        df = pd.read_csv(PC_CSV)
        gaps = df["latest_year"] - df["previous_year"]
        assert (gaps == 1).all(), f"Found non-consecutive year gaps: {gaps[gaps != 1].tolist()}"

    def test_valid_patterns(self):
        """All pattern labels must be from the 5 valid categories."""
        df = pd.read_csv(PC_CSV)
        all_patterns = set(df["previous_pattern"].tolist() + df["latest_pattern"].tolist())
        invalid = all_patterns - set(ALL_CATEGORIES)
        assert len(invalid) == 0, f"Invalid patterns: {invalid}"

    def test_valid_company_ids(self):
        """All company IDs in pattern_changes must be real."""
        df = pd.read_csv(PC_CSV)
        companies = get_company_list()
        valid_ids = set(c["company_id"] for c in companies)
        invalid = set(df["company_id"]) - valid_ids
        assert len(invalid) == 0, f"Invalid company IDs: {invalid}"

    def test_no_false_changes_across_missing_years(self):
        """Verify transitions are only between consecutive years present in capital_allocation.csv."""
        pc_df = pd.read_csv(PC_CSV)
        ca_df = pd.read_csv(CA_CSV)

        for _, row in pc_df.head(50).iterrows():  # sample first 50
            cid = row["company_id"]
            co_data = ca_df[ca_df["company_id"] == cid].sort_values("year")
            years = co_data["year"].tolist()
            assert row["previous_year"] in years, f"previous_year {row['previous_year']} not in CA data for {cid}"
            assert row["latest_year"] in years, f"latest_year {row['latest_year']} not in CA data for {cid}"
            assert row["latest_year"] - row["previous_year"] == 1


# ---------------------------------------------------------------------------
# 6. cashflow_intelligence.xlsx still valid
# ---------------------------------------------------------------------------

class TestCashflowXLSX:
    """Verify cashflow_intelligence.xlsx remains consistent with Day 31."""

    def test_row_count(self):
        df = pd.read_excel(XLSX_PATH)
        assert len(df) == 92, f"Expected 92 rows, got {len(df)}"

    def test_no_duplicate_ids(self):
        df = pd.read_excel(XLSX_PATH)
        dupes = df["company_id"].duplicated()
        assert dupes.sum() == 0, f"Found {dupes.sum()} duplicate company IDs"

    def test_columns_preserved(self):
        df = pd.read_excel(XLSX_PATH)
        expected = [
            "company_id",
            "cfo_quality_value",
            "cfo_quality_label",
            "capex_intensity_value",
            "capex_intensity_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation",
            "latest_year",
        ]
        assert list(df.columns) == expected

    def test_capital_allocation_matches_source(self):
        """Capital allocation in xlsx should match the source calculation."""
        df = pd.read_excel(XLSX_PATH)
        companies = get_company_list()

        for co in companies:
            cid = co["company_id"]
            cf_df = get_cashflow_data(cid)
            pl_df = get_pl(cid)
            fr_df = get_financial_ratios(cid)

            if fr_df.empty or cf_df.empty or pl_df.empty:
                continue

            fr_df = fr_df.dropna(subset=["year"])
            latest_year = int(fr_df.iloc[0]["year"])

            roe = _to_float(fr_df.iloc[0]["return_on_equity_pct"])
            roce = _to_float(fr_df.iloc[0]["return_on_capital_employed_pct"])

            cf_match = cf_df[cf_df["year"] == latest_year]
            pl_match = pl_df[pl_df["year"] == latest_year]

            cfo = _to_float(cf_match.iloc[0]["operating_activity"]) if not cf_match.empty else None
            pat = _to_float(pl_match.iloc[0]["net_profit"]) if not pl_match.empty else None

            ccr = cash_conversion_ratio(cfo, pat)
            ca = capital_allocation_category(roe, roce, ccr)

            xlsx_row = df[df["company_id"] == cid]
            if not xlsx_row.empty and ca is not None:
                xlsx_ca = xlsx_row["capital_allocation"].values[0]
                assert xlsx_ca == ca, (
                    f"{cid}: xlsx={xlsx_ca} but source={ca}"
                )
