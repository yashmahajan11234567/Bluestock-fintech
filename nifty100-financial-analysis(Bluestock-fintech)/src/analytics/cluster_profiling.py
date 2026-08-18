"""
Cluster profiling for financial analysis - Day 37.

Implements cluster profiling, correlation heatmap, outlier detection,
and portfolio statistics based on Day 36 clustering results.
"""

import os
import sys

import numpy as np
import pandas as pd

# Ensure src/ is importable so that sibling analytics modules resolve
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.analytics.clustering import build_feature_dataframe
from src.dashboard.utils.db import (
    get_company_list,
    get_financial_ratios,
    get_sectors,
)

# Canonical KPIs for correlation, outlier detection, and portfolio statistics
CANONICAL_KPIS = [
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


def build_kpi_matrix() -> pd.DataFrame:
    """Build a DataFrame with the canonical 10 KPIs for all companies.

    Returns:
        DataFrame with columns: company_id, broad_sector, and the 10 KPIs.
        Each company has exactly one row (latest available financial_ratios)."""
    companies = get_company_list()
    sectors = get_sectors()

    # Create a mapping from company_id to broad_sector
    sector_map = {}
    for sector_row in sectors:
        cid = sector_row["company_id"]
        sector = sector_row["broad_sector"]
        sector_map[cid] = sector

    rows = []
    for company in companies:
        company_id = company["company_id"]
        broad_sector = sector_map.get(company_id, "UNKNOWN")

        # Get financial ratios dataframe and take the first (latest) row
        fr_df = get_financial_ratios(company_id)
        if fr_df.empty:
            # If no financial ratios, create row with NaN values
            row_data = {
                "company_id": company_id,
                "broad_sector": broad_sector,
            }
            for kpi in CANONICAL_KPIS:
                row_data[kpi] = np.nan
            rows.append(row_data)
            continue

        # Take the first row (latest due to DESC ordering in get_financial_ratios)
        latest_row = fr_df.iloc[0]

        row_data = {
            "company_id": company_id,
            "broad_sector": broad_sector,
        }

        # Extract each KPI, converting to float and handling NaN/inf
        for kpi in CANONICAL_KPIS:
            val = _safe_float(latest_row.get(kpi))
            row_data[kpi] = val

        rows.append(row_data)

    df = pd.DataFrame(rows)
    return df


def _safe_float(value) -> float | None:
    """Convert a value to float, returning None for NaN/inf/None/errors."""
    if value is None:
        return None
    try:
        f = float(value)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def build_cluster_profiles() -> pd.DataFrame:
    """Build cluster profiles by joining cluster labels with feature data.

    Returns:
        DataFrame with one row per cluster (0-4) containing mean and median
        values for the five clustering features, plus company count and cluster name."""
    # Get the frozen cluster labels from Day 36
    cluster_labels_path = os.path.join(_PROJECT_ROOT, "output", "cluster_labels.csv")
    cluster_labels = pd.read_csv(cluster_labels_path)

    # Verify we have exactly 92 companies and cluster IDs 0-4
    if len(cluster_labels) != 92:
        raise ValueError(
            f"Expected 92 companies in cluster_labels.csv, got {len(cluster_labels)}"
        )

    expected_cluster_ids = {0, 1, 2, 3, 4}
    actual_cluster_ids = set(cluster_labels["cluster_id"].unique())
    if actual_cluster_ids != expected_cluster_ids:
        raise ValueError(
            f"Expected cluster IDs {expected_cluster_ids}, got {actual_cluster_ids}"
        )

    # Get the feature dataframe (reusing Day 36 logic)
    feature_df = build_feature_dataframe()

    # Join cluster labels with feature data on company_id
    merged_df = pd.merge(
        cluster_labels[["company_id", "cluster_id", "cluster_name"]],
        feature_df,
        on="company_id",
        how="left",
    )

    # Group by cluster_id to calculate statistics
    feature_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # Calculate mean and median for each feature
    grouped = merged_df.groupby("cluster_id")

    # Start with basic cluster info
    cluster_info = (
        grouped[["company_id", "cluster_name"]]
        .agg(
            {
                "company_id": "count",
                "cluster_name": "first",  # Take the first cluster_name (should be same for all in cluster)
            }
        )
        .rename(columns={"company_id": "company_count"})
    )

    # Calculate means
    means = grouped[feature_cols].mean()
    means = means.add_suffix("_mean")

    # Calculate medians
    medians = grouped[feature_cols].median()
    medians = medians.add_suffix("_median")

    # Combine all statistics
    profiles = pd.concat([cluster_info, means, medians], axis=1)

    # Reset index to make cluster_id a column
    profiles = profiles.reset_index()

    # Reorder columns to match specification
    column_order = [
        "cluster_id",
        "cluster_name",
        "company_count",
        "return_on_equity_pct_mean",
        "return_on_equity_pct_median",
        "debt_to_equity_mean",
        "debt_to_equity_median",
        "revenue_cagr_5yr_mean",
        "revenue_cagr_5yr_median",
        "fcf_cagr_5yr_mean",
        "fcf_cagr_5yr_median",
        "operating_profit_margin_pct_mean",
        "operating_profit_margin_pct_median",
    ]

    profiles = profiles[column_order]

    # Rename columns to match specification exactly
    column_rename_map = {
        "return_on_equity_pct_mean": "roe_mean",
        "return_on_equity_pct_median": "roe_median",
        "debt_to_equity_mean": "de_mean",
        "debt_to_equity_median": "de_median",
        "revenue_cagr_5yr_mean": "rev_cagr_mean",
        "revenue_cagr_5yr_median": "rev_cagr_median",
        "fcf_cagr_5yr_mean": "fcf_cagr_mean",
        "fcf_cagr_5yr_median": "fcf_cagr_median",
        "operating_profit_margin_pct_mean": "opm_mean",
        "operating_profit_margin_pct_median": "opm_median",
    }

    profiles = profiles.rename(columns=column_rename_map)

    # Ensure cluster IDs are sorted
    profiles = profiles.sort_values("cluster_id").reset_index(drop=True)

    return profiles


def build_correlation_matrix() -> pd.DataFrame:
    """Build Pearson correlation matrix for the 10 canonical KPIs.

    Returns:
        DataFrame with 10x10 correlation matrix (KPIs as both index and columns).
        Uses pairwise-complete observations to handle missing values."""
    # Get KPI matrix
    kpi_df = build_kpi_matrix()

    # Extract just the KPI columns
    kpi_columns = kpi_df[CANONICAL_KPIS]

    # Calculate Pearson correlation with pairwise complete observations
    correlation_matrix = kpi_columns.corr(method="pearson")

    return correlation_matrix


def save_correlation_heatmap(
    correlation_matrix: pd.DataFrame, output_path: str
) -> None:
    """Save correlation matrix as a heatmap using seaborn and matplotlib.

    Args:
        correlation_matrix: DataFrame with correlation values
        output_path: Path to save the heatmap image"""
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend for server/headless execution
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Set up the plot
    plt.figure(figsize=(10, 8))

    # Create heatmap with annotations
    sns.heatmap(
        correlation_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )

    plt.title("Correlation Heatmap of Canonical KPIs (Pearson)", fontsize=16, pad=20)
    plt.tight_layout()

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def build_outlier_report() -> pd.DataFrame:
    """Build outlier report using Z-scores within each broad_sector.

    Returns:
        DataFrame with one row per company containing:
        - company_id, broad_sector
        - Z-scores for each of the 10 KPIs (_z suffix)
        - is_outlier (boolean)
        - outlier_metrics (semicolon-separated KPI names where |z| > 3)"""
    # Get KPI matrix
    kpi_df = build_kpi_matrix()

    # Make a copy to work with
    outlier_df = kpi_df.copy()

    # Initialize Z-score columns
    z_score_columns = [f"{kpi}_z" for kpi in CANONICAL_KPIS]
    for col in z_score_columns:
        outlier_df[col] = np.nan

    # Calculate Z-scores within each broad_sector
    for sector in outlier_df["broad_sector"].unique():
        sector_mask = outlier_df["broad_sector"] == sector
        sector_data = outlier_df.loc[sector_mask, CANONICAL_KPIS]

        # Skip if sector has no data or all NaN
        if sector_data.empty or sector_data.isnull().all().all():
            continue

        # Calculate sector mean and std (population std = ddof=0)
        sector_means = sector_data.mean(skipna=True)
        sector_stds = sector_data.std(skipna=True, ddof=0)  # Population std

        # Calculate Z-scores for each KPI in this sector
        for kpi in CANONICAL_KPIS:
            mean_val = sector_means[kpi]
            std_val = sector_stds[kpi]

            # Handle zero standard deviation
            if std_val == 0 or np.isnan(std_val):
                z_score = 0.0
            else:
                # For each company in sector, calculate z = (value - mean) / std
                sector_company_mask = sector_mask & outlier_df[kpi].notna()
                if sector_company_mask.any():
                    z_scores = (
                        outlier_df.loc[sector_company_mask, kpi] - mean_val
                    ) / std_val
                    outlier_df.loc[sector_company_mask, f"{kpi}_z"] = z_scores

    # Determine outliers: any KPI with |z| > 3
    outlier_conditions = []
    for kpi in CANONICAL_KPIS:
        z_col = f"{kpi}_z"
        outlier_conditions.append(np.abs(outlier_df[z_col]) > 3)

    # Combine conditions: outlier if ANY KPI exceeds threshold
    outlier_df["is_outlier"] = (
        np.logical_or.reduce(outlier_conditions) if outlier_conditions else False
    )

    # Build outlier_metrics string
    def get_outlier_metrics(row):
        metrics = []
        for kpi in CANONICAL_KPIS:
            z_col = f"{kpi}_z"
            z_val = row[z_col]
            if not np.isnan(z_val) and np.abs(z_val) > 3:
                metrics.append(kpi)
        return ";".join(metrics)

    outlier_df["outlier_metrics"] = outlier_df.apply(get_outlier_metrics, axis=1)

    # Select and order columns as specified
    z_columns = [f"{kpi}_z" for kpi in CANONICAL_KPIS]
    output_columns = (
        ["company_id", "broad_sector"] + z_columns + ["is_outlier", "outlier_metrics"]
    )

    result_df = outlier_df[output_columns].copy()

    # Sort by company_id for consistent ordering
    result_df = result_df.sort_values("company_id").reset_index(drop=True)

    return result_df


def build_portfolio_stats() -> pd.DataFrame:
    """Build portfolio statistics for the 10 canonical KPIs.

    Returns:
        DataFrame with one row per KPI containing:
        - kpi: KPI name
        - P10, P25, P50, P75, P90: percentiles
        - mean: arithmetic mean
        - std: sample standard deviation (ddof=1)"""
    # Get KPI matrix
    kpi_df = build_kpi_matrix()

    # Extract just the KPI columns
    kpi_columns = kpi_df[CANONICAL_KPIS]

    # Calculate statistics for each KPI
    stats_list = []

    for kpi in CANONICAL_KPIS:
        series = kpi_columns[kpi].dropna()  # Exclude NaN values

        if len(series) == 0:
            # All values are NaN
            stats = {
                "kpi": kpi,
                "P10": np.nan,
                "P25": np.nan,
                "P50": np.nan,
                "P75": np.nan,
                "P90": np.nan,
                "mean": np.nan,
                "std": np.nan,
            }
        else:
            # Calculate percentiles
            p10, p25, p50, p75, p90 = np.percentile(series, [10, 25, 50, 75, 90])

            # Calculate mean and std (sample std = ddof=1)
            mean_val = np.mean(series)
            std_val = np.std(series, ddof=1)  # Sample standard deviation

            stats = {
                "kpi": kpi,
                "P10": p10,
                "P25": p25,
                "P50": p50,
                "P75": p75,
                "P90": p90,
                "mean": mean_val,
                "std": std_val,
            }

        stats_list.append(stats)

    # Create DataFrame
    stats_df = pd.DataFrame(stats_list)

    # Reorder columns as specified
    column_order = ["kpi", "P10", "P25", "P50", "P75", "P90", "mean", "std"]
    stats_df = stats_df[column_order]

    return stats_df


def main() -> None:
    """Main orchestration function for Day 37 cluster profiling."""
    print("Starting Day 37: Cluster Profiling & Statistics")
    print("=" * 50)

    # 1. Cluster Profiling
    print("\n1. Building cluster profiles...")
    try:
        cluster_profiles = build_cluster_profiles()
        print(f"   ✓ Cluster profiles shape: {cluster_profiles.shape}")

        # Save to output/cluster_profiles.csv
        output_dir = os.path.join(_PROJECT_ROOT, "output")
        os.makedirs(output_dir, exist_ok=True)
        profiles_path = os.path.join(output_dir, "cluster_profiles.csv")
        cluster_profiles.to_csv(profiles_path, index=False)
        print(f"   ✓ Saved to {profiles_path}")

        # Display summary
        print("\n   Cluster Profiles:")
        print(cluster_profiles.to_string(index=False))

    except Exception as e:
        print(f"   ✗ Error building cluster profiles: {e}")
        return

    # 2. Correlation Heatmap
    print("\n2. Building correlation matrix and heatmap...")
    try:
        correlation_matrix = build_correlation_matrix()
        print(f"   ✓ Correlation matrix shape: {correlation_matrix.shape}")

        # Validate correlation matrix
        if correlation_matrix.shape != (10, 10):
            raise ValueError(
                f"Expected 10x10 correlation matrix, got {correlation_matrix.shape}"
            )

        # Check diagonal is approximately 1
        diagonal_vals = np.diag(correlation_matrix.values)
        if not np.allclose(diagonal_vals, 1.0, rtol=1e-10):
            print(f"   ⚠ Warning: Diagonal not exactly 1.0: {diagonal_vals}")

        # Check symmetry
        if not np.allclose(
            correlation_matrix.values, correlation_matrix.values.T, rtol=1e-10
        ):
            print("   ⚠ Warning: Correlation matrix not symmetric")

        # Save heatmap
        reports_dir = os.path.join(_PROJECT_ROOT, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        heatmap_path = os.path.join(reports_dir, "correlation_heatmap.png")
        save_correlation_heatmap(correlation_matrix, heatmap_path)
        print(f"   ✓ Heatmap saved to {heatmap_path}")

        # Display correlation matrix summary
        print("\n   Correlation Matrix Summary:")
        print(f"   Min correlation: {correlation_matrix.min().min():.3f}")
        print(f"   Max correlation: {correlation_matrix.max().max():.3f}")
        print(f"   Mean correlation: {correlation_matrix.mean().mean():.3f}")

    except Exception as e:
        print(f"   ✗ Error building correlation matrix/heatmap: {e}")
        return

    # 3. Outlier Detection
    print("\n3. Building outlier report...")
    try:
        outlier_report = build_outlier_report()
        print(f"   ✓ Outlier report shape: {outlier_report.shape}")

        # Save to output/outlier_report.csv
        outlier_path = os.path.join(output_dir, "outlier_report.csv")
        outlier_report.to_csv(outlier_path, index=False)
        print(f"   ✓ Saved to {outlier_path}")

        # Display outlier summary
        outlier_count = outlier_report["is_outlier"].sum()
        total_companies = len(outlier_report)
        print("\n   Outlier Summary:")
        print(f"   Total companies: {total_companies}")
        print(
            f"   Outliers detected: {outlier_count} ({outlier_count/total_companies*100:.1f}%)"
        )

        if outlier_count > 0:
            print("\n   Outlier details:")
            outlier_details = outlier_report[outlier_report["is_outlier"]][
                ["company_id", "outlier_metrics"]
            ]
            print(outlier_details.to_string(index=False))

    except Exception as e:
        print(f"   ✗ Error building outlier report: {e}")
        return

    # 4. Portfolio Statistics
    print("\n4. Building portfolio statistics...")
    try:
        portfolio_stats = build_portfolio_stats()
        print(f"   ✓ Portfolio stats shape: {portfolio_stats.shape}")

        # Save to output/portfolio_stats.csv
        portfolio_path = os.path.join(output_dir, "portfolio_stats.csv")
        portfolio_stats.to_csv(portfolio_path, index=False)
        print(f"   ✓ Saved to {portfolio_path}")

        # Display portfolio stats
        print("\n   Portfolio Statistics:")
        print(portfolio_stats.to_string(index=False, float_format=".3f"))

    except Exception as e:
        print(f"   ✗ Error building portfolio statistics: {e}")
        return

    print("\n" + "=" * 50)
    print("Day 37 implementation completed successfully!")


if __name__ == "__main__":
    main()
