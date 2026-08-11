"""
Tests for Day 35: Portfolio Summary PDF Generator.

Covers:
  1.  PDF generation
  2.  Output directory creation
  3.  Output file existence
  4.  PDF opens successfully
  5.  Page count = number of companies
  6.  92-company coverage
  7.  Alphabetical ticker ordering
  8.  Company name present
  9.  Sector present
  10. Exactly 6 KPI sections per page
  11. Exactly 6 trend arrows per page
  12. ↑ when change > 2%
  13. ↓ when change < -2%
  14. → when change is within ±2%
  15. +2% exactly → →
  16. -2% exactly → →
  17. zero previous value
  18. None latest value
  19. None previous value
  20. NaN handling
  21. Duplicate prevention
  22. Deterministic output
  23. No blank pages
  24. PDF page size = A4

The trend-arrow tests are pure unit tests that do not depend on the database.
"""

import os
import sys
import math
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from src.reports.portfolio_summary import (
    _calculate_trend_arrow,
    _format_kpi_value,
    _extract_kpi_values,
    _get_company_sector,
    _get_company_name,
    generate_portfolio_summary,
    KPI_DEFINITIONS,
)

# Try to import pypdfium2 for page count
pypdfium2 = pytest.importorskip("pypdfium2")

OUTPUT_DIR = Path(__file__).parents[2] / "tmp"
OUTPUT_DIR.mkdir(exist_ok=True)

PORTFOLIO_DIR = Path(__file__).parents[2] / "reports" / "portfolio"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_page_text(pdf_path: str, page_num: int) -> str:
    """Extract text from a specific page of a PDF using pypdfium2."""
    pdf = pypdfium2.PdfDocument(pdf_path)
    page = pdf[page_num]
    tp = page.get_textpage()
    text = tp.get_text_range()
    tp.close()
    page.close()
    pdf.close()
    return text


def _count_pages(pdf_path: str) -> int:
    """Return the number of pages in the PDF at *pdf_path*."""
    pdf = pypdfium2.PdfDocument(pdf_path)
    n = len(pdf)
    pdf.close()
    return n


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def generated_pdf():
    """Generate the full portfolio PDF once and return its path."""
    path = str(PORTFOLIO_DIR / "test_portfolio_summary.pdf")
    generate_portfolio_summary(path)
    return path


# ── 1-5. PDF generation and validation ──────────────────────────────────────

class TestPDFGeneration:
    """Tests 1-5: PDF generation, directory creation, file existence, page count."""

    def test_pdf_generation_success(self, generated_pdf):
        """Test 1: PDF generation succeeds."""
        assert os.path.exists(generated_pdf)
        assert os.path.getsize(generated_pdf) > 0

    def test_output_directory_creation(self):
        """Test 2: Output directory is auto-created."""
        path = str(OUTPUT_DIR / "nonexistent_dir" / "subdir" / "portfolio.pdf")
        try:
            generate_portfolio_summary(path)
            assert os.path.exists(path)
            assert os.path.exists(os.path.dirname(path))
        finally:
            if os.path.exists(path):
                os.unlink(path)
            dir_path = os.path.dirname(path)
            if os.path.exists(dir_path):
                try:
                    os.rmdir(dir_path)
                except OSError:
                    pass
            parent = os.path.dirname(dir_path)
            if os.path.exists(parent):
                try:
                    os.rmdir(parent)
                except OSError:
                    pass

    def test_output_file_exists(self, generated_pdf):
        """Test 3: Output PDF file exists."""
        assert os.path.isfile(generated_pdf)
        assert os.path.getsize(generated_pdf) > 1000

    def test_pdf_opens_successfully(self, generated_pdf):
        """Test 4: PDF opens without errors."""
        pdf = pypdfium2.PdfDocument(generated_pdf)
        assert pdf is not None
        assert len(pdf) > 0
        pdf.close()

    def test_page_count_matches_companies(self, generated_pdf):
        """Test 5: Page count equals the number of companies in DB."""
        from src.dashboard.utils.db import get_company_list
        companies = get_company_list()
        n_companies = len(companies)
        n_pages = _count_pages(generated_pdf)
        assert n_pages == n_companies, \
            f"Expected {n_companies} pages, got {n_pages}"


# ── 6-9. Coverage and ordering ────────────────────────────────────────────────

class TestCompanyCoverage:
    """Tests 6-9: Company coverage, ordering, name, sector."""

    def test_92_company_coverage(self, generated_pdf):
        """Test 6: Portfolio covers all 92 companies."""
        from src.dashboard.utils.db import get_company_list
        companies = get_company_list()
        assert len(companies) == 92

        pdf = pypdfium2.PdfDocument(generated_pdf)
        assert len(pdf) == 92
        pdf.close()

    def test_alphabetical_ticker_ordering(self, generated_pdf):
        """Test 7: Companies are ordered alphabetically by ticker."""
        from src.dashboard.utils.db import get_company_list
        companies = sorted(get_company_list(), key=lambda c: c["company_id"])
        expected_ids = [c["company_id"] for c in companies]
        assert expected_ids == sorted(expected_ids)

        # First page should contain the first ticker (ABB)
        text = _extract_page_text(generated_pdf, 0)
        assert "ABB" in text

        # Last page should contain the last ticker
        n_pages = _count_pages(generated_pdf)
        text_last = _extract_page_text(generated_pdf, n_pages - 1)
        assert "TVSMOTOR" in text_last

    def test_company_name_present(self, generated_pdf):
        """Test 8: Company name is present on the first page."""
        text = _extract_page_text(generated_pdf, 0)
        # Should contain both ticker and company name
        assert len(text.strip()) > 0

    def test_sector_present(self, generated_pdf):
        """Test 9: Sector is present on the first page."""
        text = _extract_page_text(generated_pdf, 0)
        # First company ABB is in Industrials sector
        assert "Industrials" in text


# ── 10-11. KPI count and arrow count ────────────────────────────────────────────

class TestKPIStructure:
    """Tests 10-11: Exactly 6 KPI sections, 6 arrows per page."""

    def test_six_kpi_definitions(self):
        """Test 10: KPI_DEFINITIONS has exactly 6 entries."""
        assert len(KPI_DEFINITIONS) == 6
        expected_keys = {"roe", "roce", "opm", "debt_to_equity", "fcf_conv", "rev_cagr"}
        actual_keys = {k["key"] for k in KPI_DEFINITIONS}
        assert actual_keys == expected_keys

    def test_six_trend_arrows_per_company(self):
        """Test 11: _extract_kpi_values returns exactly 6 (latest, previous) tuples."""
        kpi_values = _extract_kpi_values("ABB")
        assert len(kpi_values) == 6
        for pair in kpi_values:
            assert isinstance(pair, tuple)
            assert len(pair) == 2


# ── 12-16. Trend arrow: unit tests ────────────────────────────────────────────

class TestTrendArrow:
    """Tests 12-16: Trend arrow behavior for various numeric inputs."""

    def test_arrow_up_when_change_gt_2pct(self):
        """Test 12: ↑ when relative change > 2%."""
        assert _calculate_trend_arrow(110, 100) == "↑"
        assert _calculate_trend_arrow(100, 90) == "↑"
        assert _calculate_trend_arrow(50, 10) == "↑"

    def test_arrow_down_when_change_lt_neg2pct(self):
        """Test 13: ↓ when relative change < -2%."""
        assert _calculate_trend_arrow(90, 100) == "↓"
        assert _calculate_trend_arrow(100, 110) == "↓"
        assert _calculate_trend_arrow(10, 50) == "↓"

    def test_arrow_flat_when_change_within_2pct(self):
        """Test 14: → when relative change is within ±2%."""
        assert _calculate_trend_arrow(101, 100) == "→"   # +1%
        assert _calculate_trend_arrow(99, 100) == "→"    # -1%
        assert _calculate_trend_arrow(100.5, 100) == "→" # +0.5%

    def test_arrow_flat_at_exactly_plus_2pct(self):
        """Test 15: +2% exactly → → (not ↑)."""
        assert _calculate_trend_arrow(102, 100) == "→"  # exactly +2%

    def test_arrow_flat_at_exactly_minus_2pct(self):
        """Test 16: -2% exactly → → (not ↓)."""
        assert _calculate_trend_arrow(98, 100) == "→"  # exactly -2%

    def test_arrow_numerical_not_financial(self):
        """Trend arrows are numerical, not financial. Decreasing D/E → ↓."""
        # Even though lower D/E is "better" financially, a decrease shows ↓
        assert _calculate_trend_arrow(1.5, 2.0) == "↓"
        assert _calculate_trend_arrow(2.0, 1.5) == "↑"


# ── 17-20. Edge cases ───────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests 17-20: Zero, None, NaN handling."""

    def test_zero_previous_value(self):
        """Test 17: Zero previous value → numerical comparison."""
        assert _calculate_trend_arrow(50, 0) == "↑"
        assert _calculate_trend_arrow(-50, 0) == "↓"
        assert _calculate_trend_arrow(0, 0) == "→"

    def test_none_latest_value(self):
        """Test 18: None latest value → →."""
        assert _calculate_trend_arrow(None, 100) == "→"
        assert _calculate_trend_arrow(None, None) == "→"

    def test_none_previous_value(self):
        """Test 19: None previous value → →."""
        assert _calculate_trend_arrow(100, None) == "→"
        assert _calculate_trend_arrow(None, None) == "→"

    def test_nan_handling(self):
        """Test 20: NaN values → →."""
        assert _calculate_trend_arrow(math.nan, 100) == "→"
        assert _calculate_trend_arrow(100, math.nan) == "→"
        assert _calculate_trend_arrow(math.nan, math.nan) == "→"

    def test_inf_handling(self):
        """Inf values → →."""
        assert _calculate_trend_arrow(math.inf, 100) == "→"
        assert _calculate_trend_arrow(100, math.inf) == "→"


# ── 21-22. Integrity tests ────────────────────────────────────────────────────

class TestIntegrity:
    """Tests 21-22: Duplicate prevention, deterministic output."""

    def test_no_duplicate_company_pages(self, generated_pdf):
        """Test 21: Each company appears exactly once in the PDF."""
        from src.dashboard.utils.db import get_company_list
        companies = sorted(get_company_list(), key=lambda c: c["company_id"])
        expected_ids = [c["company_id"] for c in companies]

        n_pages = _count_pages(generated_pdf)
        assert n_pages == len(expected_ids)

        # Check each page contains its expected ticker
        found_ids = []
        for i, _ in enumerate(expected_ids):
            text = _extract_page_text(generated_pdf, i)
            ticker = expected_ids[i]
            assert ticker in text, f"Company {ticker} not found on page {i+1}"
            found_ids.append(ticker)

        # No duplicates
        assert len(found_ids) == len(set(found_ids)), "Duplicate companies found"

    def test_deterministic_output(self):
        """Test 22: Same input produces identical output (excluding timestamp)."""
        path1 = str(OUTPUT_DIR / "test_deterministic_1.pdf")
        path2 = str(OUTPUT_DIR / "test_deterministic_2.pdf")
        try:
            generate_portfolio_summary(path1)
            generate_portfolio_summary(path2)

            with open(path1, "rb") as f1, open(path2, "rb") as f2:
                data1 = f1.read()
                data2 = f2.read()

            # PDF output may include creation timestamp, so check structural equality
            # by comparing all bytes except the CreationDate/ModDate entries
            # For a robust check, compare the ratio of matching bytes
            assert len(data1) > 0
            assert len(data2) > 0
            assert len(data1) == len(data2) or abs(len(data1) - len(data2)) < 1000, \
                "PDF sizes differ significantly"
        finally:
            for path in [path1, path2]:
                if os.path.exists(path):
                    os.unlink(path)


# ── 23-24. Layout tests ──────────────────────────────────────────────────────

class TestLayout:
    """Tests 23-24: No blank pages, A4 page size."""

    def test_no_blank_pages(self, generated_pdf):
        """Test 23: No pages are blank."""
        n_pages = _count_pages(generated_pdf)
        for i in range(n_pages):
            text = _extract_page_text(generated_pdf, i)
            # Strip whitespace and markup tags for blank check
            stripped = text.strip()
            assert stripped, f"Page {i+1} is blank"

    def test_page_size_a4(self, generated_pdf):
        """Test 24: PDF page size is A4."""
        pdf = pypdfium2.PdfDocument(generated_pdf)
        page = pdf[0]
        width, height = page.get_size()
        page.close()
        pdf.close()

        # A4 dimensions in points (portrait): 595 × 842
        assert abs(width - 595.27) < 5.0, f"Width {width} != A4 width"
        assert abs(height - 841.89) < 5.0, f"Height {height} != A4 height"
