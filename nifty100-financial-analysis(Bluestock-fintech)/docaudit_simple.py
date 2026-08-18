#!/usr/bin/env python3
"""
Simple docstring audit for Day 44 QA.
"""

import ast
import os
from pathlib import Path


def analyze_file(file_path: Path) -> tuple:
    """Analyze a single Python file for public function docstrings."""
    total = 0
    one_line = 0
    missing = 0
    multi_line = 0
    invalid = 0

    try:
        # Read file and remove BOM if present
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if public (doesn't start with _)
                if node.name.startswith('_'):
                    continue

                total += 1

                # Check for docstring
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):

                    docstring = node.body[0].value.value

                    # Check if docstring is one logical line (no newline)
                    if '\n' not in docstring and docstring.strip():
                        docstring_lower = docstring.lower().strip()
                        is_valid = (
                            len(docstring.strip()) > 10 and
                            not docstring_lower.startswith('todo') and
                            not docstring_lower.startswith('fixme') and
                            not docstring_lower.startswith('hack') and
                            not 'placeholder' in docstring_lower and
                            not 'to be implemented' in docstring_lower
                        )

                        if is_valid:
                            one_line += 1
                        else:
                            invalid += 1
                    else:
                        multi_line += 1
                else:
                    missing += 1

    except Exception as e:
        # Skip files with encoding issues
        pass

    return total, one_line, missing, multi_line, invalid


def main():
    src_dir = Path("src")

    print("DOCSTRING AUDIT RESULTS:")
    print("=" * 70)

    # Collect results from all Python files
    all_results = []

    for py_file in src_dir.rglob("*.py"):
        result = analyze_file(py_file)
        all_results.append(result)

    # Sum up results
    total_public_functions = sum(r[0] for r in all_results)
    with_one_line_docstring = sum(r[1] for r in all_results)
    missing = sum(r[2] for r in all_results)
    multi_line = sum(r[3] for r in all_results)
    invalid = sum(r[4] for r in all_results)

    print(f"TOTAL PUBLIC FUNCTIONS: {total_public_functions}")
    print(f"WITH ONE-LINE DOCSTRING: {with_one_line_docstring}")
    print(f"MISSING: {missing}")
    print(f"MULTI-LINE: {multi_line}")
    print(f"INVALID: {invalid}")

    # Return results for verification
    print("\n" + "=" * 70)
    print("REQUIREMENTS:")
    print(f"TOTAL PUBLIC FUNCTIONS: {total_public_functions}")
    print(f"WITH ONE-LINE DOCSTRING: {with_one_line_docstring}")
    print(f"MISSING: {missing} (required: 0)")
    print(f"MULTI-LINE: {multi_line} (required: 0)")
    print(f"INVALID: {invalid} (required: 0)")


if __name__ == "__main__":
    main()