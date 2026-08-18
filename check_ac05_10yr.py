import sqlite3
import re

def parse_year(year_str):
    parts = year_str.strip().split()
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    match = re.search(r'\b(\d{4})\b', year_str)
    if match:
        return int(match.group(1))
    return None

def check_ac05_10yr():
    conn = sqlite3.connect('nifty100-financial-analysis(Bluestock-fintech)/db/nifty100.db')
    c = conn.cursor()

    c.execute("""
        SELECT year, sales
        FROM profitandloss
        WHERE company_id = 'TCS'
        ORDER BY year
    """)
    rows = c.fetchall()
    print(f"Total rows for TCS: {len(rows)}")

    parsed = []
    for year_str, sales in rows:
        if year_str == 'TTM':
            continue
        year = parse_year(year_str)
        if year is not None and sales is not None:
            parsed.append((year, sales))
        else:
            print(f"Could not parse: year_str={year_str}, sales={sales}")

    if not parsed:
        print("No parsable data")
        conn.close()
        return

    parsed.sort(key=lambda x: x[0])
    years = [y for y, _ in parsed]
    sales = [s for _, s in parsed]
    print(f"Years: {years}")
    print(f"Sales: {sales}")

    # We need at least 11 years to have a 10-year span (from year0 to year10 inclusive is 11 years?)
    # Actually, 10-year CAGR means from 10 years ago to now, which is 10 years of growth.
    # If we have data for years [2015,2016,...,2024] that's 10 years? Let's think:
    # To compute CAGR over 10 years, we need start and end values that are 10 years apart.
    # For example, from 2014 to 2024 is 10 years? Actually, from end of 2014 to end of 2024 is 10 years.
    # But we have fiscal year ending March? The year string is like 'Mar 2015' etc.
    # We'll assume the year represents the fiscal year ending in that year.
    # So to get 10-year CAGR, we take the oldest and most recent in the last 10 years of data.
    # If we have data for 2015 through 2024 inclusive, that's 10 years? Let's count: 2015,2016,2017,2018,2019,2020,2021,2022,2023,2024 -> that's 10 years.
    # So we need the earliest year in the last 10 years of data.

    if len(years) < 10:
        print(f"Not enough years of data: {len(years)}")
        conn.close()
        return

    # Take the last 10 years of data
    last_10 = parsed[-10:]
    years_10 = [y for y, _ in last_10]
    sales_10 = [s for _, s in last_10]
    print(f"\nLast 10 years: {years_10}")
    print(f"Sales: {sales_10}")

    start_year = years_10[0]
    end_year = years_10[-1]
    num_years = end_year - start_year
    print(f"Start year: {start_year}, End year: {end_year}, Number of years: {num_years}")

    start_sales = sales_10[0]
    end_sales = sales_10[-1]

    if start_sales == 0:
        print("Start sales is zero")
        conn.close()
        return

    cagr = ((end_sales / start_sales) ** (1 / num_years) - 1) * 100
    print(f"\nManual 10-year CAGR calculation:")
    print(f"  Start year: {start_year}, sales: {start_sales}")
    print(f"  End year:   {end_year}, sales: {end_sales}")
    print(f"  Number of years: {num_years}")
    print(f"  CAGR: {cagr:.2f}%")

    # Get analysis table value
    c.execute("""
        SELECT compounded_sales_growth
        FROM analysis
        WHERE company_id = 'TCS'
    """)
    analysis_row = c.fetchone()
    if analysis_row:
        analysis_value = analysis_row[0]
        print(f"\nAnalysis table value: {analysis_value}")
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
    check_ac05_10yr()