from src.reports.tearsheet import generate_tearsheet
from src.dashboard.utils.db import get_company_list
import os
import warnings
warnings.filterwarnings('ignore')

companies = get_company_list()
print(f"Total companies: {len(companies)}")

output_dir = "reports/tearsheets"
os.makedirs(output_dir, exist_ok=True)

success_count = 0
fail_count = 0
for company in companies:
    company_id = company['company_id']
    output_path = os.path.join(output_dir, f"{company_id}.pdf")
    try:
        generate_tearsheet(company_id, output_path)
        success_count += 1
        if success_count % 10 == 0:
            print(f"Generated {success_count} tearsheets...")
    except Exception as e:
        print(f"FAILED {company_id}: {e}")
        fail_count += 1

print(f"\nComplete! Success: {success_count}, Failed: {fail_count}")

# Verify file sizes
import os
files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
print(f"\nTotal PDFs generated: {len(files)}")

sizes = []
for f in files:
    path = os.path.join(output_dir, f)
    size = os.path.getsize(path)
    sizes.append(size)
    if size < 30000:
        print(f"WARNING: {f} is only {size} bytes (< 30KB)")

print(f"Min size: {min(sizes)} bytes")
print(f"Max size: {max(sizes)} bytes")
print(f"Avg size: {sum(sizes)/len(sizes):.0f} bytes")