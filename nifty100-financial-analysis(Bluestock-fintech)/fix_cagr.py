#!/usr/bin/env python3
"""
Script to fix the CAGR calculation bug in src/screener/engine.py
"""

import os

def fix_engine_file():
    file_path = os.path.join('src', 'screener', 'engine.py')

    # Read the current file
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Find the lines we need to modify
    # We need to move the pl_full.copy() to BEFORE the profitandloss modification

    # Current problematic section (lines 38-50 based on 0-indexing, but let's find it dynamically)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for the profitandloss modification section
        if "profitandloss = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)" in line:
            # Add the read line
            new_lines.append(line)
            i += 1

            # Add the next few lines until we get to the year modification
            while i < len(lines) and not ("if 'year' in profitandloss.columns:" in lines[i]):
                new_lines.append(lines[i])
                i += 1

            # Now we're at the year modification section
            # We need to copy pl_full BEFORE modifying profitandloss
            # But we also need to keep the modification logic

            # Let's backup profitandloss before modification, then modify, then restore for pl_full
            # Actually, simpler: copy pl_full first, then modify profitandloss

            # Add the year modifcation lines but we'll handle the copy separately
            while i < len(lines) and not ("# Compute CAGR from profitandloss history (all years)" in lines[i]):
                new_lines.append(lines[i])
                i += 1

            # Now insert the pl_full copy BEFORE the year modification
            new_lines.append("    # Compute CAGR from profitandloss history (all years)\n")
            new_lines.append("    # We need to keep a copy with all years for CAGR calculation\n")
            new_lines.append("    pl_full = profitandloss.copy()\n")

            # Skip the original pl_full copy line (we already added it)
            while i < len(lines) and not ("pl_full = profitandloss.copy()" in lines[i]):
                i += 1
            # Skip that line
            i += 1

            # Continue with the rest
            continue

        new_lines.append(line)
        i += 1

    # Write the fixed file
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

    print("Fixed the CAGR calculation bug in", file_path)

if __name__ == "__main__":
    fix_engine_file()