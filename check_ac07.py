import sys
sys.path.insert(0, 'nifty100-financial-analysis(Bluestock-fintech)/src')

from screener.engine import run_screener, get_quality_compounder_filters

def check_ac07():
    print("Running Quality Compounder preset...")
    filters = get_quality_compounder_filters()
    print(f"Filters: {filters}")

    results = run_screener(filters=filters)

    if results is None:
        print("Results is None")
        return False

    print(f"Number of results: {len(results)}")

    if len(results) == 0:
        print("No results - checking if this is an error")
        return False

    # Check if between 10-50 companies
    if 10 <= len(results) <= 50:
        print(f"PASS: Found {len(results)} companies (within 10-50 range)")

        # Show first few results
        print("\nFirst 5 results:")
        display_cols = ['company_id', 'company_name', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr', 'compounded_sales_growth']
        display_cols = [c for c in display_cols if c in results.columns]
        print(results[display_cols].head())

        return True
    else:
        print(f"FAIL: Found {len(results)} companies (outside 10-50 range)")
        return False

if __name__ == "__main__":
    check_ac07()