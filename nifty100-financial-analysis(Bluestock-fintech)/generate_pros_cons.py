from src.nlp.pros_cons_generator import generate_output
import warnings
warnings.filterwarnings('ignore')

print("Generating pros/cons for all companies...")
df = generate_output()
print(f"Total signals: {len(df)}")
print(f"Unique companies: {df['company_id'].nunique()}")

# Show coverage
from src.nlp.pros_cons_generator import get_company_list, validate_company_coverage
companies = get_company_list()
print(f"Total companies in universe: {len(companies)}")

issues = validate_company_coverage(df)
print(f"Companies with zero pros: {len(issues['companies_with_zero_pros'])}")
print(f"Companies with zero cons: {len(issues['companies_with_zero_cons'])}")
print(f"Companies with no signals: {len(issues['companies_with_no_signals'])}")

if issues['companies_with_zero_pros']:
    print(f"  Zero pros: {issues['companies_with_zero_pros']}")
if issues['companies_with_zero_cons']:
    print(f"  Zero cons: {issues['companies_with_zero_cons']}")
if issues['companies_with_no_signals']:
    print(f"  No signals: {issues['companies_with_no_signals']}")

# Show sample
print("\nSample signals:")
print(df.head(20).to_string())