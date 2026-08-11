"""
Tests for Day 34: Sector Report PDF Generator.

Covers:
  1.  PDF generation success
  2.  Output file existence
  3.  At least 1 page generated
  4.  All 10 sectors can be generated
  5.  Invalid sector raises ValueError
  6.  Output directory auto-creation
  7.  All 8 metrics computed per sector
  8.  Company list is dynamic (not hardcoded)

Uses pypdfium2 for page-count verification.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from src.reports.sector_report import (
    generate_sector_report,
    generate_all_sector_reports,
    _get_company_sector_map,
    _get_company_metrics,
    _compute_sector_aggregates,
    METRIC_NAMES,
)

# Try to import pypdfium2 for page count
pypdfium2 = pytest.importorskip("pypdfium2")

OUTPUT_DIR = Path(__file__).parents[2] / "tmp"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Helper ────────────────────────────────────────────────────────────────

def _count_pages(pdf_path: str) -> int:
    """Return the number of pages in the PDF at *pdf_path*."""
    pdf = pypdfium2.PdfDocument(pdf_path)
    n = len(pdf)
    pdf.close()
    return n


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_sector():
    """Pick a sector that exists in the DB."""
    sectors = _get_company_sector_map()
    sector = list(set(sectors.values()))[0]
    return sector


# ── 1-4. PDF generation and validation ────────────────────────────────────

class TestPDFGeneration:
    """Tests 1-4: PDF generation, file existence, page count, all sectors."""

    def test_pdf_generation_success(self, sample_sector):
        """Test 1: PDF generation succeeds for a valid sector."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result = generate_sector_report(sample_sector, path)
            assert result == path
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_pdf_file_exists(self, sample_sector):
        """Test 2: Output PDF file exists after generation."""
        path = str(OUTPUT_DIR / f"test_{sample_sector}.pdf")
        try:
            generate_sector_report(sample_sector, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_pdf_has_at_least_one_page(self, sample_sector):
        """Test 3: Generated PDF has at least 1 page."""
        path = str(OUTPUT_DIR / f"test_pages_{sample_sector}.pdf")
        try:
            generate_sector_report(sample_sector, path)
            n_pages = _count_pages(path)
            assert n_pages >= 1
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_all_sectors_generate(self):
        """Test 4: All 10 sectors can be generated without error."""
        all_results = generate_all_sector_reports(str(OUTPUT_DIR / "test_all_sectors"))
        assert len(all_results) == 10
        for sector, path in all_results.items():
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
            assert _count_pages(path) >= 1
        # Cleanup
        for path in all_results.values():
            if os.path.exists(path):
                os.unlink(path)
        dir_path = OUTPUT_DIR / "test_all_sectors"
        if dir_path.exists():
            dir_path.rmdir()


# ── 5-6. Error handling and edge cases ────────────────────────────────────

class TestErrorHandling:
    """Tests 5-6: Invalid sector, missing output directory."""

    def test_invalid_sector_raises_valueerror(self):
        """Test 5: Invalid sector name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid sector"):
            generate_sector_report("NonExistentSector", "/tmp/nonexistent_test.pdf")

    def test_missing_output_dir_auto_created(self, sample_sector):
        """Test 6: Output directory is auto-created."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "subdir", "subdir2", f"test_{sample_sector}.pdf")
            generate_sector_report(sample_sector, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0


# ── 7-8. Metrics and data integrity ────────────────────────────────────────

class TestMetrics:
    """Tests 7-8: 8 metrics computed, company list is dynamic."""

    def test_eight_metrics_defined(self):
        """Test 7: Exactly 8 metric names are defined."""
        assert len(METRIC_NAMES) == 8

    def test_company_metrics_has_eight_values(self, sample_sector):
        """Test 7: Each company returns 8 metric values."""
        sectors = _get_company_sector_map()
        companies_in_sector = [cid for cid, sec in sectors.items() if sec == sample_sector]
        if not companies_in_sector:
            pytest.skip(f"No companies in sector {sample_sector}")
        cid = companies_in_sector[0]
        values = _get_company_metrics(cid)
        assert len(values) == 8
        # At least one value should be non-None
        assert any(v is not None for v in values), \
            f"All 8 metrics are None for company {cid}"

    def test_sector_aggregates_has_eight_metrics(self, sample_sector):
        """Test 7: Sector aggregate has 8 metrics."""
        agg = _compute_sector_aggregates(sample_sector)
        assert len(agg["metrics"]) == 8
        assert agg["sector"] == sample_sector
        assert agg["company_count"] > 0
        assert len(agg["companies"]) == agg["company_count"]

    def test_company_list_is_dynamic(self):
        """Test 8: Company count matches DB (92 companies, not hardcoded)."""
        sectors = _get_company_sector_map()
        total_companies = len(sectors)
        assert total_companies == 92  # Known count from the DB
        # Verify sectors have correct count
        from collections import Counter
        sector_counts = Counter(sectors.values())
        assert len(sector_counts) == 10  # Known sector count
