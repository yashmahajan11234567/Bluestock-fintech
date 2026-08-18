#!/usr/bin/env python3
"""
Script to fix the CAGR calculation bug in src/screener/engine.py by moving
the pl_full.copy() to BEFORE the profitandloss modification.
"""

import os
import re

def fix_engine_file():
    file_path = os.path.join('src', 'screener', 'engine.py')

    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()

    # Find the profit and loss section and restructure it
    # We need to:
    # 1. Load profitandloss
    # 2. Immediately make a copy for CAGR calculation (pl_full)
    # 3. Then modify profitandloss for latest year tracking
    # 4. Then continue with CAGR calculation using pl_full

    # Pattern to match the profit and loss section
    pattern = r'(\s+# Profit and loss\n\s+profitandloss = pd\.read_excel\(os\.path\.join\(base_path, \'profitandloss\.xlsx\'\), header=1\)\n\s+if \'id\' in profitandloss\.columns:\n\s+profitandloss = profitandloss\.drop\(columns=\[\'id\'\]\)\n\s+if \'year\' in profitandloss\.columns:\n\s+profitandloss\[\'_year_int\'\] = profitandloss\[\'year\'\]\.apply\(_parse_year_to_int\)\n\s+profitandloss = profitandloss\.sort_values\(\[\'company_id\', \'_year_int\'\]\), ascending=\[True, False\]\n\s+profitandloss = profitandloss\.drop_duplicates\(subset=\[\'company_id\'\]\), keep=\'first\'\n\s+profitandloss = profitandloss\.drop\(columns=\[\'_year_int\'\]\)\n\s+else:\n\s+profitandloss = profitandloss\.drop_duplicates\(subset=\[\'company_id\'\]\), keep=\'first\'\n\s+)# Compute CAGR from profitandloss history \(all years\)\n\s+# We need to keep a copy with all years for CAGR calculation\n\s+pl_full = profitandloss\.copy\(\)\n'

    # Replacement: move the pl_full.copy() to right after loading profitandloss
    replacement = r'# Profit and loss\n\1    # Compute CAGR from profitandloss history (all years)\n    # We need to keep a copy with all years for CAGR calculation\n    pl_full = profitandloss.copy()\n'

    # Apply the replacement
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Write the fixed file
    with open(file_path, 'w') as f:
        f.write(new_content)

    print("Fixed the CAGR calculation bug in", file_path)
    print("Moved pl_full.copy() to BEFORE profitandloss modification")

if __name__ == "__main__":
    fix_engine_file()