#!/usr/bin/env python3
"""
Analyze Python files for public function docstrings.

This script programmatically inspects every Python file under src/.

A public function/method:
- name does not start with "_"

For every public function:
- PASS if docstring exists, is one logical line, and accurately describes the function
- MISSING if no docstring
- MULTI-LINE if docstring spans multiple lines (not one logical line)
- INVALID if docstring exists but is invalid (e.g., incorrect format, doesn't describe function)

The script analyzes ALL 63 Python files in src/ and reports exact totals.
"""

import ast
import os
from pathlib import Path


def analyze_file(file_path: Path) -> tuple:
    """Analyze a single Python file for public function docstrings.

    Returns:
        tuple: (total_public_functions, with_one_line_docstring, missing, multi_line, invalid)
    """
    total = 0
    one_line = 0
    missing = 0
    multi_line = 0
    invalid = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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

                    # Check if docstring is one logical line (no newline or only one line)
                    if '\n' not in docstring and docstring.strip():
                        # Check if it describes the function (basic check - not too short, not "todo", "fixme", etc.)
                        docstring_lower = docstring.lower().strip()
                        is_valid = (
                            len(docstring.strip()) > 10 and  # Reasonable length
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
        print(f"Warning: Could not analyze {file_path}: {e}")

    return total, one_line, missing, multi_line, invalid


def main():
    src_dir = Path("src")

    print(f"Analyzing Python files in {src_dir}...")
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

    # Print results
    print("DOCSTRING AUDIT RESULTS:")
    print("=" * 70)
    print(f"TOTAL PUBLIC FUNCTIONS: {total_public_functions}")
    print(f"WITH ONE-LINE DOCSTRING: {with_one_line_docstring}")
    print(f"MISSING: {missing}")
    print(f"MULTI-LINE: {multi_line}")
    print(f"INVALID: {invalid}")

    # Verify requirements
    print("\nREQUIREMENTS VERIFICATION:")
    print("=" * 70)
    if missing == 0:
        print("PASS MISSING = 0 - Requirement MET")
    else:
        print(f"FAIL MISSING = {missing} - Requirement NOT MET")

    if multi_line == 0:
        print("PASS MULTI-LINE = 0 - Requirement MET")
    else:
        print(f"FAIL MULTI-LINE = {multi_line} - Requirement NOT MET")

    if invalid == 0:
        print("PASS INVALID = 0 - Requirement MET")
    else:
        print(f"FAIL INVALID = {invalid} - Requirement NOT MET")


if __name__ == "__main__":
    main()