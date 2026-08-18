"""
KMeans clustering for financial analysis - Day 36.

Implements KMeans clustering on five financial features:
1. return_on_equity_pct
2. debt_to_equity
3. revenue_cagr_5yr
4. fcf_cagr_5yr
5. operating_profit_margin_pct

Follows the exact specification for Sprint 6, Day 36.
"""

import math
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

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow import free_cash_flow
from src.analytics.cashflow_kpis import calculate_fcf_cagr
from src.dashboard.utils.db import (
    get_cashflow_data,
    get_company_list,
    get_financial_ratios,
    get_pl,
    get_sectors,
)

# Constants for the five features
FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def _safe_float(value) -> float | None:
    """Convert a value to float, returning None for NaN/inf/None/errors."""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _compute_revenue_cagr_5yr(company_id: str) -> float | None:
    """
    Compute 5-year revenue CAGR using the existing project's convention.

    Uses profitandloss.sales and the calculate_cagr function.
    Requires a positive starting value for CAGR.
    """
    pl_df = get_pl(company_id)
    if pl_df.empty or len(pl_df) < 6:
        return None

    # Get the most recent year and the year 5 years prior
    pl_df = pl_df.copy()
    pl_df["year"] = pd.to_numeric(pl_df["year"], errors="coerce")
    pl_df = pl_df.dropna(subset=["year"])
    pl_df = pl_df.sort_values("year", ascending=False)

    if len(pl_df) < 6:
        return None

    # Most recent year (index 0) and 5 years prior (index 5)
    latest_year = int(pl_df.iloc[0]["year"])
    past_year = latest_year - 5

    # Find the row for past_year
    past_row = pl_df[pl_df["year"] == past_year]
    if past_row.empty:
        return None

    latest_sales = _safe_float(pl_df.iloc[0]["sales"])
    past_sales = _safe_float(past_row.iloc[0]["sales"])

    if latest_sales is None or past_sales is None:
        return None
    if past_sales <= 0:
        return None

    return calculate_cagr(past_sales, latest_sales, 5)


def _compute_fcf_cagr_5yr(company_id: str) -> float | None:
    """
    Compute 5-year FCF CAGR using the existing project's convention.

    Replicates the logic from cashflow_kpis.py's build_company_kpis for the fcf_cagr_5yr KPI.
    """
    cf_df = get_cashflow_data(company_id)
    if cf_df.empty:
        return None

    # Get up to 5 years of cash flow data (most recent first)
    cf_df = cf_df.copy()
    cf_df["year"] = pd.to_numeric(cf_df["year"], errors="coerce")
    cf_df = cf_df.dropna(subset=["year"])
    cf_df = cf_df.sort_values("year", ascending=False)

    n_years = min(5, len(cf_df))
    cf_subset = cf_df.head(n_years)

    if len(cf_subset) < 2:
        return None

    # Extract OCF and investing activity values
    ocf_values = [_safe_float(v) for v in cf_subset["operating_activity"].tolist()]
    investing_values = [
        _safe_float(v) for v in cf_subset["investing_activity"].tolist()
    ]
    cf_years = [int(y) if pd.notna(y) else None for y in cf_subset["year"].tolist()]

    # Get financial ratios for capex_cr
    fr_df = get_financial_ratios(company_id)

    # latest_investing is the investing_activity of the most recent year (index 0)
    latest_investing = investing_values[0] if investing_values else None

    fcf_values = []
    for i, year in enumerate(cf_years):
        ocf = ocf_values[i] if i < len(ocf_values) else None
        capex = None

        if not fr_df.empty:
            fr_row = fr_df[fr_df["year"] == year]
            if not fr_row.empty:
                capex = _safe_float(fr_row.iloc[0]["capex_cr"])

        if ocf is not None and capex is not None:
            fcf = free_cash_flow(ocf, capex)
            fcf_values.append(fcf)
        elif ocf is not None and latest_investing is not None:
            # Fallback: use investing_activity as a proxy for capex if no capex_cr
            # Note: This uses the same latest_investing (most recent year) for every year, as in the original code.
            fcf = free_cash_flow(
                ocf, abs(latest_investing) if latest_investing < 0 else latest_investing
            )
            fcf_values.append(fcf)
        else:
            fcf_values.append(None)

    # Use the existing function which handles positive FCF values and year alignment
    return calculate_fcf_cagr(fcf_values, cf_years)


def _get_latest_financial_ratio(company_id: str, field: str) -> float | None:
    """Get the latest value for a financial ratio field."""
    fr_df = get_financial_ratios(company_id)
    if fr_df.empty:
        return None
    # fr_df is already sorted descending by year, so first row is latest
    val = _safe_float(fr_df.iloc[0][field])
    return val


def build_feature_dataframe() -> pd.DataFrame:
    """Build a DataFrame with one row per company containing the five features.

    Returns:
        DataFrame with columns: company_id, broad_sector, and the five features."""
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
        broad_sector = sector_map.get(company_id)

        # Get the five features
        roe = _get_latest_financial_ratio(company_id, "return_on_equity_pct")
        debt_eq = _get_latest_financial_ratio(company_id, "debt_to_equity")
        op_margin = _get_latest_financial_ratio(
            company_id, "operating_profit_margin_pct"
        )
        revenue_cagr = _compute_revenue_cagr_5yr(company_id)
        fcf_cagr = _compute_fcf_cagr_5yr(company_id)

        rows.append(
            {
                "company_id": company_id,
                "broad_sector": broad_sector,
                "return_on_equity_pct": roe,
                "debt_to_equity": debt_eq,
                "revenue_cagr_5yr": revenue_cagr,
                "fcf_cagr_5yr": fcf_cagr,
                "operating_profit_margin_pct": op_margin,
            }
        )

    df = pd.DataFrame(rows)
    return df


def impute_sector_median(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing values using sector median, then global median.

    Modifies the DataFrame in place and also returns it.

    Args:
        df: DataFrame with columns for the five features and 'broad_sector'.

    Returns:
        DataFrame with imputed values (no NaN in the five features)."""
    feature_cols = [c for c in FEATURES if c in df.columns]

    # First, impute with sector median
    for col in feature_cols:
        # Compute median per sector
        sector_medians = df.groupby("broad_sector")[col].transform("median")
        # Fill missing values in this column with sector median
        df[col] = df[col].fillna(sector_medians)

    # Then, impute any remaining missing values with global median
    for col in feature_cols:
        global_median = df[col].median()
        df[col] = df[col].fillna(global_median)

    # Verify no NaN remains
    if df[feature_cols].isnull().any().any():
        # This should not happen if there was at least one non-NaN value per column
        # If a column is all NaN, then global median would be NaN and we'd still have NaN
        # In that case, we fail loudly as per requirements
        raise ValueError(
            f"Imputation failed. Some columns still have NaN values: "
            f"{df[feature_cols].columns[df[feature_cols].isnull().any()].tolist()}"
        )

    return df


def compute_elbow_values(X: np.ndarray) -> dict[int, float]:
    """Compute inertia for k from 2 to 10.

    Args:
        X: Standardized feature matrix.

    Returns:
        Dictionary mapping k to inertia."""
    from sklearn.cluster import KMeans

    inertias = {}
    for k in range(2, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        inertias[k] = kmeans.inertia_

    return inertias


def save_elbow_plot(inertias: dict[int, float]) -> None:
    """Save elbow plot to reports/elbow_plot.png.

    Args:
        inertias: Dictionary mapping k to inertia."""
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    ks = list(inertias.keys())
    values = [inertias[k] for k in ks]

    plt.figure(figsize=(8, 6))
    plt.plot(ks, values, "bo-")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("Elbow Method for Optimal k")
    plt.grid(True, linestyle="--", alpha=0.7)

    # Ensure reports directory exists
    reports_dir = os.path.join(_PROJECT_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    plot_path = os.path.join(reports_dir, "elbow_plot.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()


def assign_cluster_names(
    df: pd.DataFrame, feature_means: pd.DataFrame, scaled_feature_means: pd.DataFrame
) -> dict[int, str]:
    """Assign descriptive names to clusters based on their profiles.

    We assign names by identifying extreme clusters first, then assigning the rest.

    Args:
        df: Original DataFrame with features (before scaling).
        feature_means: DataFrame with cluster means of the original features.
        scaled_feature_means: DataFrame with cluster means of the scaled features (cluster centers).

    Returns:
        Dictionary mapping cluster_id to cluster_name."""
    # We'll work with the scaled feature means (z-scores) for comparison
    z_scores = scaled_feature_means.copy()
    cluster_ids = list(z_scores.index)
    # We expect 5 clusters
    if len(cluster_ids) != 5:
        # Fallback to the old method if not 5 clusters (should not happen)
        cluster_names = {}
        for cluster_id in scaled_feature_means.index:
            row = scaled_feature_means.loc[cluster_id]
            roe_high = row["return_on_equity_pct"] > 0.5
            roe_low = row["return_on_equity_pct"] < -0.5
            debt_high = row["debt_to_equity"] > 0.5
            debt_low = row["debt_to_equity"] < -0.5
            rev_growth_high = row["revenue_cagr_5yr"] > 0.5
            rev_growth_low = row["revenue_cagr_5yr"] < -0.5
            fcf_growth_high = row["fcf_cagr_5yr"] > 0.5
            fcf_growth_low = row["fcf_cagr_5yr"] < -0.5
            margin_high = row["operating_profit_margin_pct"] > 0.5
            margin_low = row["operating_profit_margin_pct"] < -0.5

            if (
                roe_high
                and debt_low
                and (rev_growth_high or fcf_growth_high)
                and margin_high
            ):
                name = "High-Quality Compounders"
            elif (
                debt_low
                and margin_high
                and not (rev_growth_high or fcf_growth_high)
                and not (roe_high)
            ):
                name = "Defensive Dividend Payers"
            elif (
                not (rev_growth_high or fcf_growth_high)
                and not (roe_high)
                and not (debt_high)
            ):
                name = "Value Cyclicals"
            elif (
                debt_high
                and (rev_growth_low or fcf_growth_low)
                and margin_low
                and roe_low
            ):
                name = "Distressed or Turnaround"
            elif (
                (rev_growth_high or fcf_growth_high)
                and not roe_high
                and (debt_high or not debt_low)
            ):
                name = "Emerging Growth"
            else:
                abs_vals = row.abs()
                max_feature = abs_vals.idxmax()
                max_value = row[max_feature]
                if max_value > 0:
                    direction = "High"
                else:
                    direction = "Low"
                feature_name = {
                    "return_on_equity_pct": "Return on Equity",
                    "debt_to_equity": "Debt to Equity",
                    "revenue_cagr_5yr": "Revenue Growth",
                    "fcf_cagr_5yr": "FCF Growth",
                    "operating_profit_margin_pct": "Operating Margin",
                }[max_feature]
                name = f"{direction} {feature_name}"
            cluster_names[cluster_id] = name
        return cluster_names

    # We have exactly 5 clusters, proceed with the deterministic naming based on extremes
    names = {}

    # Step 1: Find cluster with highest ROE (z-score)
    max_roe_cluster = z_scores["return_on_equity_pct"].idxmax()
    names[max_roe_cluster] = "High Return on Equity"
    remaining = [cid for cid in cluster_ids if cid != max_roe_cluster]

    # Step 2: From remaining, find cluster with highest Debt/Equity (z-score)
    max_de_cluster = z_scores.loc[remaining, "debt_to_equity"].idxmax()
    names[max_de_cluster] = "High Debt to Equity"
    remaining = [cid for cid in remaining if cid != max_de_cluster]

    # Step 3: From remaining, compute growth score = max(revenue CAGR z-score, FCF CAGR z-score)
    growth_scores = {}
    for cid in remaining:
        growth_scores[cid] = max(
            z_scores.loc[cid, "revenue_cagr_5yr"], z_scores.loc[cid, "fcf_cagr_5yr"]
        )
    max_growth_cluster = max(growth_scores, key=growth_scores.get)
    names[max_growth_cluster] = "Emerging Growth"
    remaining = [cid for cid in remaining if cid != max_growth_cluster]

    # Step 4: Last two clusters, assign based on Operating Margin z-score (higher margin gets "High Margin Value")
    if len(remaining) == 2:
        cid1, cid2 = remaining[0], remaining[1]
        if (
            z_scores.loc[cid1, "operating_profit_margin_pct"]
            >= z_scores.loc[cid2, "operating_profit_margin_pct"]
        ):
            names[cid1] = "High Margin Value"
            names[cid2] = "Moderate Value"
        else:
            names[cid2] = "High Margin Value"
            names[cid1] = "Moderate Value"
    else:
        # This should not happen, but fallback
        for cid in remaining:
            names[cid] = f"Cluster_{cid}"

    return names


def main() -> None:
    """Main orchestration function."""
    print("Building feature DataFrame...")
    df = build_feature_dataframe()

    # Check we have 92 companies
    if len(df) != 92:
        print(f"WARNING: Expected 92 companies, got {len(df)}")

    print("Imputing missing values...")
    df = impute_sector_median(df)

    # Extract features for scaling
    feature_df = df[FEATURES].copy()

    # Standardize features
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_df)

    print("Computing elbow plot (k=2 to 10)...")
    inertias = compute_elbow_values(X_scaled)
    print("Elbow inertias:", inertias)

    print("Saving elbow plot...")
    save_elbow_plot(inertias)

    # Provide a qualitative assessment of the elbow
    # We'll compute the percentage drop in inertia from k to k+1
    # and look for a large drop (the elbow)
    inertias_list = [inertias[k] for k in range(2, 11)]
    drops = []
    for i in range(len(inertias_list) - 1):
        drop = (inertias_list[i] - inertias_list[i + 1]) / inertias_list[i] * 100
        drops.append(drop)

    # The elbow is often where the drop decreases significantly
    # We'll just note if k=5 has a drop that is not the largest but still significant
    print("\nElbow assessment:")
    for i, k in enumerate(range(2, 11)):
        if i == 0:
            drop_str = "N/A"
        else:
            drop_str = f"{drops[i-1]:.1f}%"
        print(f"  k={k}: inertia={inertias[k]:.2f}, drop from previous={drop_str}")

    # Determine if k=5 seems reasonable
    if len(drops) >= 4:  # we have at least up to k=6
        drop_at_4 = drops[2]  # drop from k=4 to k=5
        drop_at_5 = drops[3]  # drop from k=5 to k=6
        if drop_at_4 > 10 and drop_at_5 < drop_at_4:
            print(
                "  NOTE: k=5 shows a significant drop in inertia, suggesting it may be near the elbow."
            )
        else:
            print("  NOTE: The elbow is unclear; k=5 was chosen as per specification.")

    print("\nRunning KMeans with n_clusters=5, random_state=42...")
    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(X_scaled)

    # Add cluster IDs to the main DataFrame
    df["cluster_id"] = cluster_ids

    # Calculate distance from centroid in standardized space
    # For each point, compute Euclidean distance to its cluster centroid
    distances = []
    for idx, point in enumerate(X_scaled):
        cluster_id = cluster_ids[idx]
        centroid = kmeans.cluster_centers_[cluster_id]
        dist = np.linalg.norm(point - centroid)
        distances.append(dist)

    df["distance_from_centroid"] = distances

    # Compute cluster profiles (means of original features) for naming
    cluster_means = df.groupby("cluster_id")[FEATURES].mean()

    # Compute cluster means of scaled features (should be close to the cluster centers)
    scaled_means = pd.DataFrame(
        kmeans.cluster_centers_, columns=FEATURES, index=range(5)
    )

    # Assign cluster names
    print("Assigning cluster names...")
    cluster_names = assign_cluster_names(df, cluster_means, scaled_means)
    df["cluster_name"] = df["cluster_id"].map(cluster_names)

    # Prepare output DataFrame with required columns
    output_df = df[
        ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    ].copy()

    # Ensure output directory exists
    output_dir = os.path.join(_PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "cluster_labels.csv")
    output_df.to_csv(output_path, index=False)

    print(f"\nSuccessfully saved cluster labels to {output_path}")
    print(f"Output shape: {output_df.shape}")
    print(f"Cluster IDs: {sorted(output_df['cluster_id'].unique())}")
    print(f"Number of unique companies: {output_df['company_id'].nunique()}")

    # Print cluster summary
    print("\nCluster summary:")
    for cluster_id in sorted(cluster_names.keys()):
        count = (df["cluster_id"] == cluster_id).sum()
        name = cluster_names[cluster_id]
        print(f"  Cluster {cluster_id} ({name}): {count} companies")

    # Verify deterministic execution
    print("\nVerifying deterministic execution with random_state=42...")
    # Run again and check if cluster IDs are the same (should be)
    kmeans2 = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids2 = kmeans2.fit_predict(X_scaled)
    if np.array_equal(cluster_ids, cluster_ids2):
        print("  PASS: Cluster assignments are deterministic.")
    else:
        print("  FAIL: Cluster assignments are not deterministic.")

    print("\nDay 36 KMeans clustering completed.")


if __name__ == "__main__":
    main()
