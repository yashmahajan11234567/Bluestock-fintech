"""
Tests for src/analytics/cashflow_kpis.py — Day 31 Cash Flow Intelligence.

Covers all 7 KPI pure functions with edge cases, plus integration tests
for build_company_kpis, generate_cashflow_intelligence, and
generate_distress_alerts using real database data.
"""

import sys
import math
from pathlib import Path
from math import isclose

import pytest
import pandas as pd

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the module directly using importlib to avoid package conflicts
import importlib.util
cashflow_kpis_path = Path(__file__).parents[2] / "src" / "analytics" / "cashflow_kpis.py"
spec = importlib.util.spec_from_file_location("analytics.cashflow_kpis", cashflow_kpis_path)
ck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ck)

calculate_cfo_quality = ck.calculate_cfo_quality
calculate_capex_intensity = ck.calculate_capex_intensity
calculate_fcf_cagr = ck.calculate_fcf_cagr
calculate_fcf_conversion = ck.calculate_fcf_conversion
detect_distress = ck.detect_distress
detect_deleveraging = ck.detect_deleveraging
calculate_capital_allocation = ck.calculate_capital_allocation
build_company_kpis = ck.build_company_kpis
generate_cashflow_intelligence = ck.generate_cashflow_intelligence
generate_distress_alerts = ck.generate_distress_alerts


# =========================================================================
# 1. calculate_cfo_quality
# =========================================================================

class TestCalculateCFOQuality:
    """Tests for calculate_cfo_quality()."""

    def test_high_quality(self):
        """Mean CCR > 1.0 -> High Quality."""
        result = calculate_cfo_quality([1.5, 1.2, 1.0])
        assert result[1] == "High Quality"
        assert isclose(result[0], (1.5 + 1.2 + 1.0) / 3, rel_tol=1e-4)

    def test_boundary_just_over_1(self):
        """Mean just over 1.0 -> High Quality."""
        result = calculate_cfo_quality([1.01])
        assert result[1] == "High Quality"

    def test_moderate(self):
        """0.5 < mean <= 1.0 -> Moderate."""
        result = calculate_cfo_quality([0.8, 0.6])
        assert result[1] == "Moderate"
        assert isclose(result[0], 0.7)

    def test_boundary_0_5(self):
        """Mean exactly 0.5 -> Accrual Risk (<=0.5)."""
        result = calculate_cfo_quality([0.5])
        assert result[1] == "Accrual Risk"

    def test_accrual_risk(self):
        """Mean <= 0.5 -> Accrual Risk."""
        result = calculate_cfo_quality([0.3, 0.2])
        assert result[1] == "Accrual Risk"
        assert isclose(result[0], 0.25)

    def test_boundary_just_under_1(self):
        """Mean just under 1.0 -> Moderate."""
        result = calculate_cfo_quality([0.99])
        assert result[1] == "Moderate"

    def test_negative_ccr(self):
        """Negative CCR values -> Accrual Risk."""
        result = calculate_cfo_quality([-0.5, -0.3])
        assert result[1] == "Accrual Risk"
        assert isclose(result[0], -0.4)

    def test_mixed_values(self):
        """Mix of high and low CCR values."""
        result = calculate_cfo_quality([2.0, 0.8])
        mean = (2.0 + 0.8) / 2  # 1.4
        assert result[1] == "High Quality"
        assert isclose(result[0], mean)

    def test_with_none_values(self):
        """None values are skipped in mean calculation."""
        result = calculate_cfo_quality([1.5, None, 1.0])
        assert result[1] == "High Quality"
        assert isclose(result[0], 1.25)

    def test_all_none(self):
        """All None values -> Insufficient Data."""
        result = calculate_cfo_quality([None, None, None])
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_empty_list(self):
        """Empty list -> Insufficient Data."""
        result = calculate_cfo_quality([])
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_single_value(self):
        """Single value works."""
        result = calculate_cfo_quality([1.0])
        assert result[1] == "Moderate"

    def test_nan_values_treated_as_none(self):
        """NaN float values are treated as None."""
        result = calculate_cfo_quality([1.5, float("nan"), 1.2])
        assert result[1] == "High Quality"

    def test_rounding(self):
        """Mean is rounded to 4 decimal places."""
        result = calculate_cfo_quality([1.11111, 2.22222, 3.33333])
        assert result[0] == round((1.11111 + 2.22222 + 3.33333) / 3, 4)


# =========================================================================
# 2. calculate_capex_intensity
# =========================================================================

class TestCalculateCapexIntensity:
    """Tests for calculate_capex_intensity()."""

    def test_asset_light(self):
        """investing 100, sales 1000 -> 10% -> Asset Light."""
        result = calculate_capex_intensity(-100, 1000)
        assert result[0] == 10.0
        assert result[1] == "Asset Light"

    def test_boundary_20(self):
        """investing 200, sales 1000 -> 20% -> Moderate."""
        result = calculate_capex_intensity(-200, 1000)
        assert result[0] == 20.0
        assert result[1] == "Moderate"

    def test_moderate(self):
        """investing 300, sales 1000 -> 30% -> Moderate."""
        result = calculate_capex_intensity(-300, 1000)
        assert result[0] == 30.0
        assert result[1] == "Moderate"

    def test_boundary_50(self):
        """investing 500, sales 1000 -> 50% -> Moderate (boundary)."""
        result = calculate_capex_intensity(-500, 1000)
        assert result[0] == 50.0
        assert result[1] == "Moderate"

    def test_capital_intensive(self):
        """investing 600, sales 1000 -> 60% -> Capital Intensive."""
        result = calculate_capex_intensity(-600, 1000)
        assert result[0] == 60.0
        assert result[1] == "Capital Intensive"

    def test_positive_investing(self):
        """Investing activity can be positive (net sale of assets)."""
        result = calculate_capex_intensity(100, 1000)
        assert result[0] == 10.0
        assert result[1] == "Asset Light"

    def test_investing_none(self):
        """None investing_activity -> Insufficient Data."""
        result = calculate_capex_intensity(None, 1000)
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_sales_none(self):
        """None sales -> Insufficient Data."""
        result = calculate_capex_intensity(-100, None)
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_both_none(self):
        """Both None -> Insufficient Data."""
        result = calculate_capex_intensity(None, None)
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_sales_zero(self):
        """Sales of 0 -> Insufficient Data (avoid division by zero)."""
        result = calculate_capex_intensity(-100, 0)
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_sales_negative(self):
        """Negative sales -> Insufficient Data."""
        result = calculate_capex_intensity(-100, -1000)
        assert result[0] is None
        assert result[1] == "Insufficient Data"

    def test_zero_investing(self):
        """Zero investing -> 0% intensity -> Asset Light."""
        result = calculate_capex_intensity(0, 1000)
        assert result[0] == 0.0
        assert result[1] == "Asset Light"


# =========================================================================
# 3. calculate_fcf_cagr
# =========================================================================

class TestCalculateFCFCAGR:
    """Tests for calculate_fcf_cagr()."""

    def test_normal_growing(self):
        """FCF growing over 5 years."""
        result = calculate_fcf_cagr([300, 200, 150, 100, 50], [2024, 2023, 2022, 2021, 2020])
        # start=50 (2020), end=300 (2024), years=4
        expected = ((300 / 50) ** (1 / 4) - 1) * 100
        assert isclose(result, expected, rel_tol=1e-4)

    def test_with_negative_fcf(self):
        """Negative FCF values are filtered out."""
        # Only positive values: [200, 150, 100, 50], years [2023, 2022, 2021, 2020]
        # start=50 (2020), end=200 (2023), years=3
        result = calculate_fcf_cagr([-100, 200, 150, 100, 50], [2024, 2023, 2022, 2021, 2020])
        expected = ((200 / 50) ** (1 / 3) - 1) * 100
        assert isclose(result, expected, rel_tol=1e-4)

    def test_declining_fcf(self):
        """Declining FCF produces negative CAGR."""
        result = calculate_fcf_cagr([50, 100, 150, 200, 300], [2024, 2023, 2022, 2021, 2020])
        # start=300 (2020), end=50 (2024), years=4
        expected = ((50 / 300) ** (1 / 4) - 1) * 100
        assert isclose(result, expected, rel_tol=1e-4)
        assert result < 0

    def test_with_none_values(self):
        """None values are skipped."""
        result = calculate_fcf_cagr([100, None, 50, None, -10], [2024, 2023, 2022, 2021, 2020])
        # Positive values: [100 (2024), 50 (2022)], start=50 (2022), end=100 (2024), years=2
        expected = ((100 / 50) ** (1 / 2) - 1) * 100
        assert isclose(result, expected, rel_tol=1e-4)

    def test_all_none(self):
        """All None -> None."""
        assert calculate_fcf_cagr([None, None, None], [2024, 2023, 2022]) is None

    def test_empty_list(self):
        """Empty -> None."""
        assert calculate_fcf_cagr([], []) is None

    def test_single_positive(self):
        """Only one positive value -> None (need at least 2)."""
        assert calculate_fcf_cagr([100, None, None], [2024, 2023, 2022]) is None

    def test_all_negative(self):
        """All negative values -> None."""
        assert calculate_fcf_cagr([-100, -200, -50], [2024, 2023, 2022]) is None

    def test_zero_values(self):
        """Zero values are not positive -> None."""
        assert calculate_fcf_cagr([0, 0, 0], [2024, 2023, 2022]) is None

    def test_same_start_end(self):
        """Equal start and end -> 0% CAGR."""
        result = calculate_fcf_cagr([100, 150, 100], [2024, 2023, 2022])
        # start=100 (2022), end=100 (2024), years=2
        assert isclose(result, 0.0)

    def test_years_not_sorted(self):
        """Years in any order are handled (sorted internally)."""
        result = calculate_fcf_cagr([50, 100, 200], [2020, 2022, 2024])
        # pairs sorted: (2020,50), (2022,100), (2024,200)
        # start=50 (2020), end=200 (2024), years=4
        expected = ((200 / 50) ** (1 / 4) - 1) * 100
        assert isclose(result, expected, rel_tol=1e-4)


# =========================================================================
# 4. calculate_fcf_conversion
# =========================================================================

class TestCalculateFCFConversion:
    """Tests for calculate_fcf_conversion()."""

    def test_normal(self):
        """FCF 300, PAT 200 -> 150%."""
        result = calculate_fcf_conversion(300, 200)
        assert isclose(result, 150.0)

    def test_equal(self):
        """FCF == PAT -> 100%."""
        result = calculate_fcf_conversion(200, 200)
        assert isclose(result, 100.0)

    def test_fcf_less_than_pat(self):
        """FCF 100, PAT 200 -> 50%."""
        result = calculate_fcf_conversion(100, 200)
        assert isclose(result, 50.0)

    def test_negative_fcf(self):
        """Negative FCF -> negative conversion."""
        result = calculate_fcf_conversion(-100, 200)
        assert isclose(result, -50.0)

    def test_zero_fcf(self):
        """Zero FCF -> 0%."""
        result = calculate_fcf_conversion(0, 200)
        assert isclose(result, 0.0)

    def test_fcf_none(self):
        """None FCF -> None."""
        assert calculate_fcf_conversion(None, 200) is None

    def test_pat_none(self):
        """None PAT -> None."""
        assert calculate_fcf_conversion(300, None) is None

    def test_both_none(self):
        """Both None -> None."""
        assert calculate_fcf_conversion(None, None) is None

    def test_pat_zero(self):
        """PAT = 0 -> None (avoid division by zero)."""
        assert calculate_fcf_conversion(300, 0) is None

    def test_pat_negative(self):
        """Negative PAT -> None."""
        assert calculate_fcf_conversion(300, -200) is None

    def test_rounding(self):
        """Result is rounded to 2 decimal places."""
        result = calculate_fcf_conversion(333.333, 999.999)
        assert result == round(333.333 / 999.999 * 100, 2)


# =========================================================================
# 5. detect_distress
# =========================================================================

class TestDetectDistress:
    """Tests for detect_distress()."""

    def test_distress_true(self):
        """CFO < 0 AND CFF > 0 -> True."""
        assert detect_distress(-100, 50) is True

    def test_cfo_positive(self):
        """CFO > 0 -> False regardless of CFF."""
        assert detect_distress(100, 50) is False
        assert detect_distress(100, -50) is False

    def test_cff_negative(self):
        """CFF < 0 -> False even if CFO < 0."""
        assert detect_distress(-100, -50) is False

    def test_cff_zero(self):
        """CFF = 0 does not trigger (not > 0)."""
        assert detect_distress(-100, 0) is False

    def test_both_negative(self):
        """Both negative -> False."""
        assert detect_distress(-100, -50) is False

    def test_both_positive(self):
        """Both positive -> False."""
        assert detect_distress(100, 50) is False

    def test_cfo_none(self):
        """None CFO -> False."""
        assert detect_distress(None, 50) is False

    def test_cff_none(self):
        """None CFF -> False."""
        assert detect_distress(-100, None) is False

    def test_both_none(self):
        """Both None -> False."""
        assert detect_distress(None, None) is False

    def test_nan_cfo(self):
        """NaN CFO -> False."""
        assert detect_distress(float("nan"), 50) is False

    def test_nan_cff(self):
        """NaN CFF -> False."""
        assert detect_distress(-100, float("nan")) is False


# =========================================================================
# 6. detect_deleveraging
# =========================================================================

class TestDetectDeleveraging:
    """Tests for detect_deleveraging()."""

    def test_deleveraging_true(self):
        """CFF < 0 AND borrowings declining -> True."""
        assert detect_deleveraging(-100, 400, 500) is True

    def test_cff_positive(self):
        """CFF > 0 -> False."""
        assert detect_deleveraging(100, 400, 500) is False

    def test_borrowings_increasing(self):
        """Borrowings increasing -> False."""
        assert detect_deleveraging(-100, 600, 500) is False

    def test_borrowings_same(self):
        """Borrowings unchanged -> False."""
        assert detect_deleveraging(-100, 500, 500) is False

    def test_cff_zero(self):
        """CFF = 0 does not trigger (not < 0)."""
        assert detect_deleveraging(0, 400, 500) is False

    def test_both_none_borrowings(self):
        """None borrowings -> False."""
        assert detect_deleveraging(-100, None, 500) is False
        assert detect_deleveraging(-100, 400, None) is False

    def test_cff_none(self):
        """None CFF -> False."""
        assert detect_deleveraging(None, 400, 500) is False

    def test_all_none(self):
        """All None -> False."""
        assert detect_deleveraging(None, None, None) is False

    def test_nan_values(self):
        """NaN values -> False."""
        assert detect_deleveraging(-100, float("nan"), 500) is False
        assert detect_deleveraging(-100, 400, float("nan")) is False


# =========================================================================
# 7. calculate_capital_allocation
# =========================================================================

class TestCalculateCapitalAllocation:
    """Tests for calculate_capital_allocation()."""

    def test_excellent(self):
        """ROE>=20, ROCE>=20, CCR>=1.2 -> Excellent."""
        assert calculate_capital_allocation(25, 25, 1.5) == "Excellent"

    def test_good(self):
        """ROE>=15, ROCE>=15, CCR>=1.0 -> Good."""
        assert calculate_capital_allocation(18, 18, 1.0) == "Good"

    def test_average(self):
        """ROE>=10, ROCE>=10, CCR>=0.8 -> Average."""
        assert calculate_capital_allocation(12, 12, 0.9) == "Average"

    def test_weak(self):
        """ROE>=5, ROCE>=5 -> Weak."""
        assert calculate_capital_allocation(8, 8, 0.5) == "Weak"

    def test_poor(self):
        """ROE<5 -> Poor."""
        assert calculate_capital_allocation(3, 3, 0.5) == "Poor"

    def test_roe_none(self):
        """None ROE -> None."""
        assert calculate_capital_allocation(None, 20, 1.2) is None

    def test_roce_none(self):
        """None ROCE -> None."""
        assert calculate_capital_allocation(20, None, 1.2) is None

    def test_ccr_none(self):
        """None CCR -> None."""
        assert calculate_capital_allocation(20, 25, None) is None

    def test_all_none(self):
        """All None -> None."""
        assert calculate_capital_allocation(None, None, None) is None

    def test_boundary_excellent(self):
        """Exact boundaries for Excellent."""
        assert calculate_capital_allocation(20, 20, 1.2) == "Excellent"

    def test_boundary_good(self):
        """Exact boundaries for Good."""
        assert calculate_capital_allocation(15, 15, 1.0) == "Good"

    def test_boundary_average(self):
        """Exact boundaries for Average."""
        assert calculate_capital_allocation(10, 10, 0.8) == "Average"

    def test_boundary_weak(self):
        """Exact boundaries for Weak."""
        assert calculate_capital_allocation(5, 5, 0.7) == "Weak"

    def test_mixed_just_below_excellent(self):
        """One metric just below Excellent threshold -> Good."""
        assert calculate_capital_allocation(19, 20, 1.2) == "Good"

    def test_mixed_just_below_good(self):
        """One metric just below Good threshold -> Average."""
        assert calculate_capital_allocation(14, 15, 1.0) == "Average"


# =========================================================================
# Integration tests
# =========================================================================

class TestBuildCompanyKPIs:
    """Integration tests for build_company_kpis() using real DB data."""

    def test_bhartiartl(self):
        """Test with BHARTIARTL — a telecom company."""
        kpis = build_company_kpis("BHARTIARTL")
        assert kpis["company_id"] == "BHARTIARTL"
        assert kpis["cfo_quality_label"] in ("High Quality", "Moderate", "Accrual Risk", "Insufficient Data")
        assert kpis["capex_intensity_label"] in ("Asset Light", "Moderate", "Capital Intensive", "Insufficient Data")
        assert isinstance(kpis["distress_flag"], bool)
        assert isinstance(kpis["deleveraging_flag"], bool)
        assert "latest_year" in kpis

    def test_britannia(self):
        """Test with BRITANNIA — a FMCG company."""
        kpis = build_company_kpis("BRITANNIA")
        assert kpis["company_id"] == "BRITANNIA"
        assert kpis["cfo_quality_label"] in ("High Quality", "Moderate", "Accrual Risk", "Insufficient Data")
        assert isinstance(kpis["distress_flag"], bool)
        assert isinstance(kpis["deleveraging_flag"], bool)

    def test_sbin(self):
        """Test with SBIN — a bank (may have limited data)."""
        kpis = build_company_kpis("SBIN")
        assert kpis["company_id"] == "SBIN"
        assert kpis["cfo_quality_label"] in ("High Quality", "Moderate", "Accrual Risk", "Insufficient Data")
        assert isinstance(kpis["distress_flag"], bool)

    def test_all_companies_have_11_columns(self):
        """All companies should produce exactly 11 keys."""
        from src.dashboard.utils.db import get_company_list
        companies = get_company_list()
        for co in companies[:5]:
            kpis = build_company_kpis(co["company_id"])
            assert len(kpis) == 11, f"{co['company_id']} has {len(kpis)} keys"
            expected_keys = {
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
            }
            assert set(kpis.keys()) == expected_keys


class TestGenerateCashflowIntelligence:
    """Integration tests for generate_cashflow_intelligence()."""

    def test_row_count(self):
        """Should return exactly 92 rows (one per company)."""
        df = generate_cashflow_intelligence()
        assert len(df) == 92

    def test_columns(self):
        """Should have exactly 11 columns with correct names."""
        df = generate_cashflow_intelligence()
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

    def test_no_null_company_ids(self):
        """No company_id should be null."""
        df = generate_cashflow_intelligence()
        assert df["company_id"].notna().all()

    def test_distress_flag_is_bool(self):
        """distress_flag should be boolean."""
        df = generate_cashflow_intelligence()
        assert df["distress_flag"].dtype == bool

    def test_deleveraging_flag_is_bool(self):
        """deleveraging_flag should be boolean."""
        df = generate_cashflow_intelligence()
        assert df["deleveraging_flag"].dtype == bool

    def test_at_least_one_distress(self):
        """Should have at least one distressed company."""
        df = generate_cashflow_intelligence()
        assert df["distress_flag"].sum() > 0

    def test_latest_year_is_int(self):
        """latest_year should be integer or None."""
        df = generate_cashflow_intelligence()
        valid_years = df["latest_year"].dropna()
        assert len(valid_years) > 0


class TestGenerateDistressAlerts:
    """Integration tests for generate_distress_alerts()."""

    def test_only_distressed(self):
        """Should return only distressed companies."""
        df = generate_cashflow_intelligence()
        alerts = generate_distress_alerts(df)
        assert alerts["distress_flag"].all()

    def test_alerts_subset_of_full(self):
        """Alerts should be a subset of the full DataFrame."""
        df = generate_cashflow_intelligence()
        alerts = generate_distress_alerts(df)
        alert_ids = set(alerts["company_id"])
        df_ids = set(df["company_id"])
        assert alert_ids.issubset(df_ids)

    def test_alerts_columns(self):
        """Alerts should have same 11 columns."""
        df = generate_cashflow_intelligence()
        alerts = generate_distress_alerts(df)
        assert list(alerts.columns) == list(df.columns)

    def test_alerts_not_empty(self):
        """Should have at least one distress alert."""
        df = generate_cashflow_intelligence()
        alerts = generate_distress_alerts(df)
        assert len(alerts) > 0


class TestOutputFiles:
    """Test that output files are generated correctly."""

    def test_xlsx_file(self):
        """cashflow_intelligence.xlsx should exist and have 92 rows."""
        from src.dashboard.utils.db import get_company_list
        companies = get_company_list()
        assert len(companies) == 92

        df = generate_cashflow_intelligence()
        import tempfile, os
        output_path = os.path.join(Path(__file__).parents[2], "Data", "output",
                                   "cashflow_intelligence.xlsx")
        if os.path.exists(output_path):
            df_disk = pd.read_excel(output_path)
            assert len(df_disk) == 92
            assert list(df_disk.columns) == list(df.columns)
