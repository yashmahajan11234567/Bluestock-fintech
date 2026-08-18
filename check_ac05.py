import sqlite3
import re

def parse_year(year_str):
    """Extract year from string like 'Mar 2023' or 'Dec 2012'."""
    # Assuming format: month space year
    parts = year_str.strip().split()
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    # Fallback: try to find any 4-digit number
    match = re.search(r'\b(\d{4})\b', year_str)
    if match:
        return int(match.group(1))
    return None

def check_ac05():
    conn = sqlite3.connect('nifty100-financial-analysis(Bluestock-fintech)/db/nifty100.db')
    c = conn.cursor()

    # Get TCS profitandloss data
    c.execute("""
        SELECT year, sales
        FROM profitandloss
        WHERE company_id = 'TCS'
        ORDER BY year
    """)
    rows = c.fetchall()
    print(f"TCS profitandloss rows: {len(rows)}")
    if not rows:
        print("No data for TCS")
        conn.close()
        return

    # Parse years and sales
    parsed = []
    for year_str, sales in rows:
        year = parse_year(year_str)
        if year is not None and sales is not None:
            parsed.append((year, sales))
        else:
            print(f"Could not parse: year_str={year_str}, sales={sales}")

    if not parsed:
        print("No parsable data")
        conn.close()
        return

    # Sort by year
    parsed.sort(key=lambda x: x[0])
    years = [y for y, _ in parsed]
    sales = [s for _, s in parsed]

    print(f"Years: {years}")
    print(f"Sales: {sales}")

    # Check if we have at least 2 years
    if len(years) < 2:
        print("Need at least 2 years to compute CAGR")
        conn.close()
        return

    # Compute CAGR for the entire period
    start_year = years[0]
    end_year = years[-1]
    num_years = end_year - start_year
    if num_years <= 0:
        print("Invalid year range")
        conn.close()
        return

    start_sales = sales[0]
    end_sales = sales[-1]

    if start_sales == 0:
        print("Start sales is zero, cannot compute CAGR")
        conn.close()
        return

    cagr = ((end_sales / start_sales) ** (1 / num_years) - 1) * 100
    print(f"\nManual CAGR calculation:")
    print(f"  Start year: {start_year}, sales: {start_sales}")
    print(f"  End year:   {end_year}, sales: {end_sales}")
    print(f"  Number of years: {num_years}")
    print(f"  CAGR: {cagr:.2f}%")

    # Get the analysis table value for TCS
    c.execute("""
        SELECT compounded_sales_growth
        FROM analysis
        WHERE company_id = 'TCS'
    """)
    analysis_row = c.fetchone()
    if analysis_row:
        analysis_value = analysis_row[0]
        print(f"\nAnalysis table value: {analysis_value}")
        # Extract percentage from string like '10 Years:     11%'
        match = re.search(r'(\d+\.?\d*)%', analysis_value)
        if match:
            analysis_cagr = float(match.group(1))
            print(f"  Extracted CAGR: {analysis_cagr}%")
            diff = abs(cagr - analysis_cagr)
            print(f"  Difference: {diff:.2f}%")
            if diff <= 0.1:
                print("  RESULT: PASS (within 0.1%)")
            else:
                print("  RESULT: FAIL (difference > 0.1%)")
        else:
            print("  Could not extract percentage from analysis value")
    else:
        print("No analysis row for TCS")

    conn.close()

if __name__ == "__main__":
    check_ac05()