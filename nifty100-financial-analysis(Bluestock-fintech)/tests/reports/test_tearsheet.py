"""
Tests for Day 33: Company Tearsheet.

Covers:
  1.  PDF generation
  2.  File existence
  3.  Exactly 2 pages
  4.  All 5 test companies
  5.  Invalid company handling
  6.  Missing-data handling
  7.  KPI extraction
  8.  Revenue/Net Profit data
  9.  ROE/ROCE data
  10. Balance Sheet data
  11. Cash Flow data
  12. Pros retrieval
  13. Cons retrieval
  14. Capital allocation retrieval
  15. Long text wrapping
  16. Output path handling

Uses pypdfium2 (already installed) for page-count verification.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from src.reports.tearsheet import (
    generate_tearsheet,
    _get_kpi_data,
    _get_revenue_netprofit_data,
    _get_roe_roce_data,
    _get_balancesheet_data,
    _get_cashflow_waterfall,
    _get_pros,
    _get_cons,
    _get_capital_allocation,
    _get_latest_year,
    _safe_year,
    _truncate_text,
)

# Try to import pypdfium2 for page count
pypdfium2 = pytest.importorskip("pypdfium2")


TEST_COMPANIES = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]

OUTPUT_DIR = Path(__file__).parents[2] / "tmp"


# ── 1-4. PDF generation and validation ──────────────────────────────────

class TestPDFGeneration:
    """Tests 1-4: PDF generation, file existence, 2 pages, 5 companies."""

    def _count_pages(self, pdf_path: str) -> int:
        """Return the number of pages in the PDF at *pdf_path*."""
        pdf = pypdfium2.PdfDocument(pdf_path)
        n = len(pdf)
        pdf.close()
        return n

    def test_pdf_generation_success(self):
        """Test 1: PDF generation succeeds for a valid company."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result = generate_tearsheet("TCS", path)
            assert result == path
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_pdf_file_exists(self):
        """Test 2: Output PDF file exists after generation."""
        path = str(OUTPUT_DIR / "test_tcs.pdf")
        try:
            generate_tearsheet("TCS", path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000  # non-trivial size
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_exactly_two_pages(self):
        """Test 3: PDF has exactly 2 pages."""
        path = str(OUTPUT_DIR / "test_tcs_pages.pdf")
        try:
            generate_tearsheet("TCS", path)
            n = self._count_pages(path)
            assert n == 2, f"Expected 2 pages, got {n}"
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.parametrize("company_id", TEST_COMPANIES)
    def test_all_five_test_companies(self, company_id):
        """Test 4: All 5 test companies generate valid 2-page PDFs."""
        path = str(OUTPUT_DIR / f"test_{company_id}.pdf")
        try:
            generate_tearsheet(company_id, path)
            assert os.path.exists(path)
            n = self._count_pages(path)
            assert n == 2, f"{company_id}: expected 2 pages, got {n}"
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ── 5. Invalid company handling ─────────────────────────────────────────

class TestInvalidCompany:
    """Test 5: Invalid company handling."""

    def test_invalid_company_raises_error(self):
        """Invalid company ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid company_id"):
            generate_tearsheet("INVALID_CO", str(OUTPUT_DIR / "test_invalid.pdf"))

    def test_empty_company_id_raises_error(self):
        """Empty company ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid company_id"):
            generate_tearsheet("", str(OUTPUT_DIR / "test_invalid.pdf"))


# ── 6. Missing-data handling ────────────────────────────────────────────

class TestMissingData:
    """Test 6: Missing-data handling."""

    def test_kpi_data_returns_six_tiles(self):
        """KPI data always returns exactly 6 tiles."""
        tiles = _get_kpi_data("TCS")
        assert len(tiles) == 6
        for val, label, color in tiles:
            assert val is not None
            assert label is not None
            assert color is not None

    def test_kpi_data_with_no_ratios(self):
        """KPI extraction doesn't crash when ratios DB returns empty."""
        tiles = _get_kpi_data("NONEXISTENT")
        assert len(tiles) == 6

    def test_revenue_netprofit_handles_empty(self):
        """Revenue/Net Profit extraction handles empty P&L."""
        years, rev, np = _get_revenue_netprofit_data("NONEXISTENT")
        assert years == []
        assert rev == []
        assert np == []

    def test_roe_roce_handles_empty(self):
        """ROE/ROCE extraction handles empty ratios."""
        years, roe, roce = _get_roe_roce_data("NONEXISTENT")
        assert years == []
        assert roe == []
        assert roce == []

    def test_balancesheet_handles_empty(self):
        """Balance sheet extraction handles empty BS."""
        years, eq_cap, res, br, ol = _get_balancesheet_data("NONEXISTENT")
        assert years == []
        assert eq_cap == []
        assert res == []
        assert br == []
        assert ol == []

    def test_cashflow_waterfall_handles_empty(self):
        """Cash flow waterfall handles empty cashflow."""
        year, comps = _get_cashflow_waterfall("NONEXISTENT")
        assert year == "N/A"
        assert comps == []


# ── 7. KPI extraction ───────────────────────────────────────────────────

class TestKPIExtraction:
    """Test 7: KPI extraction from real data."""

    def test_kpi_labels(self):
        """Verify the 6 KPI labels are correct."""
        tiles = _get_kpi_data("TCS")
        labels = [t[1] for t in tiles]
        expected = ["ROE", "ROCE", "OPM", "Debt-to-Equity", "FCF Conversion", "Revenue CAGR"]
        assert labels == expected

    def test_kpi_values_present(self):
        """Verify KPI values are populated for TCS (not all N/A)."""
        tiles = _get_kpi_data("TCS")
        na_count = sum(1 for t in tiles if t[0] == "N/A")
        assert na_count < 6, "All 6 KPIs are N/A for TCS"

    def test_kpi_colors_are_hex(self):
        """Verify all KPI colors are valid hex strings."""
        tiles = _get_kpi_data("TCS")
        for _, _, color in tiles:
            assert color.startswith("#"), f"Invalid color: {color}"


# ── 8. Revenue/Net Profit data ──────────────────────────────────────────

class TestRevenueNetProfit:
    """Test 8: Revenue and Net Profit data extraction."""

    def test_revenue_netprofit_data_tcs(self):
        """TCS should have P&L data."""
        years, rev, np = _get_revenue_netprofit_data("TCS")
        assert len(years) > 0
        assert len(years) == len(rev) == len(np)

    def test_revenue_netprofit_latest_year(self):
        """Latest year should be 2024 for TCS."""
        years, _, _ = _get_revenue_netprofit_data("TCS")
        assert max(years) == 2024

    def test_revenue_netprofit_max_years(self):
        """Should return at most 10 years of data."""
        years, rev, np = _get_revenue_netprofit_data("TCS")
        assert len(years) <= 10


# ── 9. ROE/ROCE data ────────────────────────────────────────────────────

class TestROEROEData:
    """Test 9: ROE and ROCE data extraction."""

    def test_roe_roce_data_tcs(self):
        """TCS should have ROE/ROCE data."""
        years, roe, roce = _get_roe_roce_data("TCS")
        assert len(years) > 0
        assert len(years) == len(roe) == len(roce)

    def test_roe_roce_max_years(self):
        """Should return at most 10 years."""
        years, _, _ = _get_roe_roce_data("TCS")
        assert len(years) <= 10

    def test_roe_values_not_all_none(self):
        """Not all ROE values should be None for TCS."""
        _, roe, _ = _get_roe_roce_data("TCS")
        non_none = [v for v in roe if v is not None]
        assert len(non_none) > 0


# ── 10. Balance Sheet data ──────────────────────────────────────────────

class TestBalanceSheetData:
    """Test 10: Balance Sheet data extraction."""

    def test_balancesheet_data_tcs(self):
        """TCS should have balance sheet data."""
        years, eq_cap, res, br, ol = _get_balancesheet_data("TCS")
        # Compute total equity from equity_capital and reserves
        eq = [ (a or 0) + (b or 0) for a, b in zip(eq_cap, res) ]
        assert len(years) > 0
        assert len(years) == len(eq) == len(br) == len(ol)

    def test_balancesheet_max_years(self):
        """Should return at most 5 years."""
        years, _, _, _, _ = _get_balancesheet_data("TCS")
        assert len(years) <= 5

    def test_equity_has_values(self):
        """Equity values should be populated for TCS."""
        years, eq_cap, res, br, ol = _get_balancesheet_data("TCS")
        # Compute total equity from equity_capital and reserves
        eq = [ (a or 0) + (b or 0) for a, b in zip(eq_cap, res) ]
        non_none = [v for v in eq if v is not None]
        assert len(non_none) > 0


# ── 11. Cash Flow data ──────────────────────────────────────────────────

class TestCashFlowData:
    """Test 11: Cash Flow data extraction."""

    def test_cashflow_data_tcs(self):
        """TCS should have cash flow data."""
        year, comps = _get_cashflow_waterfall("TCS")
        assert year != "N/A"
        assert len(comps) == 4  # CFO, CFI, CFF, Net Cash Flow

    def test_cashflow_components_labels(self):
        """Cash flow components should have correct labels."""
        _, comps = _get_cashflow_waterfall("TCS")
        labels = [c[0] for c in comps]
        assert labels == ["CFO", "CFI", "CFF", "Net Cash Flow"]


# ── 12. Pros retrieval ──────────────────────────────────────────────────

class TestProsRetrieval:
    """Test 12: Pros retrieval from CSV."""

    def test_pros_returns_list(self):
        """Pros should return a list of strings."""
        pros = _get_pros("TCS")
        assert isinstance(pros, list)
        # TCS may or may not have pros in the CSV
        for p in pros:
            assert isinstance(p, str)

    def test_pros_max_count(self):
        """Should return at most 5 pros."""
        pros = _get_pros("TCS")
        assert len(pros) <= 5


# ── 13. Cons retrieval ──────────────────────────────────────────────────

class TestConsRetrieval:
    """Test 13: Cons retrieval from CSV."""

    def test_cons_returns_list(self):
        """Cons should return a list of strings."""
        cons = _get_cons("TCS")
        assert isinstance(cons, list)
        for c in cons:
            assert isinstance(c, str)

    def test_cons_max_count(self):
        """Should return at most 4 cons."""
        cons = _get_cons("TCS")
        assert len(cons) <= 4


# ── 14. Capital allocation retrieval ──────────────────────────────────────

class TestCapitalAllocationRetrieval:
    """Test 14: Capital allocation retrieval from Day 32 output."""

    def test_capital_allocation_tcs(self):
        """TCS should have a capital allocation category."""
        ca = _get_capital_allocation("TCS")
        valid = {"Excellent", "Good", "Average", "Weak", "Poor"}
        if ca != "N/A":
            assert ca in valid, f"Invalid category: {ca}"

    def test_capital_allocation_invalid_company(self):
        """Invalid company returns N/A."""
        ca = _get_capital_allocation("NONEXISTENT")
        assert ca == "N/A"


# ── 15. Long text wrapping ───────────────────────────────────────────────

class TestLongTextWrapping:
    """Test 15: Long text wrapping for pros/cons."""

    def test_truncate_text_short(self):
        """Short text is not truncated."""
        text = "Short text"
        assert _truncate_text(text, 200) == text

    def test_truncate_text_long(self):
        """Long text is truncated with ellipsis."""
        text = "x" * 300
        result = _truncate_text(text, 200)
        assert len(result) == 200
        assert result.endswith("...")

    def test_truncate_text_exact_boundary(self):
        """Text exactly at max length is not truncated."""
        text = "x" * 200
        assert _truncate_text(text, 200) == text


# ── 16. Output path handling ─────────────────────────────────────────────

class TestOutputPathHandling:
    """Test 16: Output path handling."""

    def test_output_creates_directory(self):
        """Output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "sub", "dir")
            path = os.path.join(subdir, "test.pdf")
            generate_tearsheet("TCS", path)
            assert os.path.exists(path)

    def test_output_overwrites_existing(self):
        """Output overwrites an existing file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        # Write some initial content
        with open(path, "w") as f:
            f.write("dummy")

        generate_tearsheet("TCS", path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000  # not "dummy" anymore

        os.unlink(path)


# ── Helper tests ─────────────────────────────────────────────────────────

class TestHelpers:
    """Tests for helper functions."""

    def test_safe_year_none(self):
        """None input returns None."""
        assert _safe_year(None) is None

    def test_safe_year_float(self):
        """Float year is converted to int."""
        assert _safe_year(2024.0) == 2024

    def test_safe_year_nan(self):
        """NaN returns None."""
        assert _safe_year(float("nan")) is None

    def test_get_latest_year_empty(self):
        """Empty DataFrame returns None."""
        import pandas as pd
        df = pd.DataFrame()
        assert _get_latest_year(df) is None

    def test_get_latest_year_valid(self):
        """Valid DataFrame returns max year."""
        import pandas as pd
        df = pd.DataFrame({"year": [2020, 2022, 2024]})
        assert _get_latest_year(df) == 2024
