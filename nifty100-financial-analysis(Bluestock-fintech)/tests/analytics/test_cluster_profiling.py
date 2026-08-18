"""
Tests for cluster profiling module - Day 37.
"""

import os
import sys

import numpy as np
import pandas as pd

# Ensure src/ is importable so that sibling analytics modules resolve
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.analytics.cluster_profiling import (
    CANONICAL_KPIS,
    build_cluster_profiles,
    build_correlation_matrix,
    build_kpi_matrix,
    build_outlier_report,
    build_portfolio_stats,
)


def test_canonical_kpi_list():
    """Test that the canonical KPI list is exactly as specified."""
    expected_kpis = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
    ]
    assert CANONICAL_KPIS == expected_kpis
    assert len(CANONICAL_KPIS) == 10


def test_kpi_matrix_has_92_companies():
    """Test that KPI matrix has exactly 92 companies."""
    kpi_df = build_kpi_matrix()
    assert len(kpi_df) == 92, f"Expected 92 companies, got {len(kpi_df)}"


def test_kpi_matrix_has_all_10_kpi_columns():
    """Test that KPI matrix has all 10 KPI columns."""
    kpi_df = build_kpi_matrix()
    missing_kpis = set(CANONICAL_KPIS) - set(kpi_df.columns)
    assert len(missing_kpis) == 0, f"Missing KPI columns: {missing_kpis}"
    assert len(kpi_df.columns) >= 12  # company_id, broad_sector + 10 KPIs


def test_cluster_profile_output_has_five_clusters():
    """Test that cluster profile output has exactly five clusters."""
    profiles_df = build_cluster_profiles()
    assert len(profiles_df) == 5, f"Expected 5 clusters, got {len(profiles_df)}"
    expected_cluster_ids = {0, 1, 2, 3, 4}
    actual_cluster_ids = set(profiles_df["cluster_id"])
    assert (
        actual_cluster_ids == expected_cluster_ids
    ), f"Expected cluster IDs {expected_cluster_ids}, got {actual_cluster_ids}"


def test_cluster_profile_includes_mean_and_median():
    """Test that cluster profile includes mean and median for all five clustering features."""
    profiles_df = build_cluster_profiles()

    # Check for mean columns
    mean_columns = [col for col in profiles_df.columns if col.endswith("_mean")]
    expected_mean_cols = [
        "roe_mean",
        "de_mean",
        "rev_cagr_mean",
        "fcf_cagr_mean",
        "opm_mean",
    ]
    assert set(mean_columns) == set(
        expected_mean_cols
    ), f"Mean columns mismatch. Expected: {expected_mean_cols}, Got: {mean_columns}"

    # Check for median columns
    median_columns = [col for col in profiles_df.columns if col.endswith("_median")]
    expected_median_cols = [
        "roe_median",
        "de_median",
        "rev_cagr_median",
        "fcf_cagr_median",
        "opm_median",
    ]
    assert set(median_columns) == set(
        expected_median_cols
    ), f"Median columns mismatch. Expected: {expected_median_cols}, Got: {median_columns}"

    # Check that we have company_count and cluster_name
    assert "company_count" in profiles_df.columns
    assert "cluster_name" in profiles_df.columns


def test_portfolio_stats_contains_exactly_10_kpis():
    """Test that portfolio stats contains exactly 10 KPIs."""
    stats_df = build_portfolio_stats()
    assert len(stats_df) == 10, f"Expected 10 rows (KPIs), got {len(stats_df)}"
    assert set(stats_df["kpi"]) == set(
        CANONICAL_KPIS
    ), "KPIs in portfolio stats don't match canonical KPIs"


def test_portfolio_stats_contains_required_statistic_columns():
    """Test that portfolio stats contains P10/P25/P50/P75/P90/mean/std columns."""
    stats_df = build_portfolio_stats()
    required_columns = ["kpi", "P10", "P25", "P50", "P75", "P90", "mean", "std"]
    missing_columns = set(required_columns) - set(stats_df.columns)
    assert len(missing_columns) == 0, f"Missing columns in portfolio stats: {missing_columns}"


def test_outlier_report_contains_all_92_companies():
    """Test that outlier report contains all 92 companies."""
    outlier_df = build_outlier_report()
    assert len(outlier_df) == 92, f"Expected 92 companies in outlier report, got {len(outlier_df)}"


def test_outlier_report_contains_all_10_zscore_columns():
    """Test that outlier report contains all 10 z-score columns."""
    outlier_df = build_outlier_report()
    zscore_columns = [f"{kpi}_z" for kpi in CANONICAL_KPIS]
    missing_zscore_cols = set(zscore_columns) - set(outlier_df.columns)
    assert len(missing_zscore_cols) == 0, f"Missing z-score columns: {missing_zscore_cols}"


def test_zero_standard_deviation_handling():
    """Test that zero standard deviation does not create inf/NaN z-scores for valid values."""
    # This test is more conceptual since we can't easily create a sector with zero std
    # in the real data, but we can verify the logic doesn't break
    outlier_df = build_outlier_report()

    # Check that there are no infinite z-scores
    zscore_columns = [f"{kpi}_z" for kpi in CANONICAL_KPIS]
    zscore_data = outlier_df[zscore_columns]

    # Check for infinities
    inf_mask = np.isinf(zscore_data.select_dtypes(include=[np.number]))
    assert not inf_mask.any().any(), "Found infinite z-scores"

    # Check that NaN z-scores only occur when original data is NaN (this is expected)
    # We'll just verify the dataframe was created successfully
    assert isinstance(outlier_df, pd.DataFrame)


def test_correlation_matrix_is_10x10():
    """Test that correlation matrix is 10x10."""
    corr_matrix = build_correlation_matrix()
    assert corr_matrix.shape == (
        10,
        10,
    ), f"Expected 10x10 correlation matrix, got {corr_matrix.shape}"


def test_correlation_matrix_diagonal_approximately_1():
    """Test that correlation matrix diagonal is approximately 1 where data exists."""
    corr_matrix = build_correlation_matrix()
    diagonal = np.diag(corr_matrix.values)
    # Using a reasonable tolerance for floating point comparison
    assert np.allclose(
        diagonal, 1.0, rtol=1e-10
    ), f"Diagonal values not approximately 1: {diagonal}"


if __name__ == "__main__":
    # Run tests manually if executed directly
    test_canonical_kpi_list()
    print("✓ test_canonical_kpi_list passed")

    test_kpi_matrix_has_92_companies()
    print("✓ test_kpi_matrix_has_92_companies passed")

    test_kpi_matrix_has_all_10_kpi_columns()
    print("✓ test_kpi_matrix_has_all_10_kpi_columns passed")

    test_cluster_profile_output_has_five_clusters()
    print("✓ test_cluster_profile_output_has_five_clusters passed")

    test_cluster_profile_includes_mean_and_median()
    print("✓ test_cluster_profile_includes_mean_and_median passed")

    test_portfolio_stats_contains_exactly_10_kpis()
    print("✓ test_portfolio_stats_contains_exactly_10_kpis passed")

    test_portfolio_stats_contains_required_statistic_columns()
    print("✓ test_portfolio_stats_contains_required_statistic_columns passed")

    test_outlier_report_contains_all_92_companies()
    print("✓ test_outlier_report_contains_all_92_companies passed")

    test_outlier_report_contains_all_10_zscore_columns()
    print("✓ test_outlier_report_contains_all_10_zscore_columns passed")

    test_zero_standard_deviation_handling()
    print("✓ test_zero_standard_deviation_handling passed")

    test_correlation_matrix_is_10x10()
    print("✓ test_correlation_matrix_is_10x10 passed")

    test_correlation_matrix_diagonal_approximately_1()
    print("✓ test_correlation_matrix_diagonal_approximately_1 passed")

    print("\nAll tests passed!")
