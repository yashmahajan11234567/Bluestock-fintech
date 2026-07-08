import pandas as pd

performance = pd.read_csv("data/processed/07_scheme_performance_clean.csv")

risk = input("Enter Risk Appetite (Low / Moderate / High): ").strip().title()

recommendations = (
    performance[
        performance["risk_grade"].str.title() == risk
    ]
    .sort_values("sharpe_ratio", ascending=False)
    .head(3)
)

print("\nTop 3 Recommended Funds:\n")

print(
    recommendations[
        [
            "scheme_name",
            "fund_house",
            "risk_grade",
            "sharpe_ratio",
            "return_3yr_pct"
        ]
    ]
)