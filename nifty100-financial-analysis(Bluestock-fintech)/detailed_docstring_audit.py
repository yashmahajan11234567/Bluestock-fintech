#!/usr/bin/env python3
"""
Detailed docstring audit for Day 44 QA Fix Round 2.

Produces the exact list of:
- Missing docstring public functions
- Multi-line docstring public functions
- Invalid docstring public functions

Across ALL Python files in src/.

Protected files are flagged but NOT excluded from the report.
"""

import ast
import os
from pathlib import Path


PROTECTED_FILES = {
    # Day 36
    'src/analytics/clustering.py',
    # Day 37
    'src/analytics/cluster_profiling.py',
    # Day 38
    'src/api/main.py',
    'src/api/routers/health.py',
    # Day 39
    'src/api/routers/companies.py',
    'src/api/schemas/company.py',
    # Day 40
    'src/api/routers/screener.py',
    'src/api/routers/sectors.py',
    'src/api/routers/peers.py',
    'src/api/schemas/screener.py',
    'src/api/schemas/sector.py',
    'src/api/schemas/peer.py',
    # Day 41
    'src/api/routers/valuation.py',
    'src/api/schemas/valuation.py',
    # Day 43
    'src/dashboard/utils/db.py',
}

# Normalize to handle both forward and backslash paths
PROTECTED_FILES = {p.replace('/', os.sep) for p in PROTECTED_FILES}


def check_docstring(docstring):
    """Classify a docstring.

    Returns: 'valid', 'missing', 'multi_line', or 'invalid'
    """
    if docstring is None:
        return 'missing'

    if '\n' in docstring:
        return 'multi_line'

    stripped = docstring.strip()
    if not stripped:
        return 'invalid'

    if len(stripped) <= 10:
        return 'invalid'

    lower = stripped.lower()
    if (lower.startswith('todo') or
        lower.startswith('fixme') or
        lower.startswith('hack') or
        'placeholder' in lower or
        'to be implemented' in lower):
        return 'invalid'

    return 'valid'


def analyze_file(filepath):
    """Analyze a single file, return list of issues."""
    issues = []

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except Exception:
        return issues

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private functions
            if node.name.startswith('_'):
                continue

            # Get the docstring
            docstring = None
            if (node.body and
                isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
                docstring = node.body[0].value.value

            status = check_docstring(docstring)

            if status != 'valid':
                issues.append({
                    'file': filepath,
                    'function': node.name,
                    'line': node.lineno,
                    'status': status,
                    'docstring': repr(docstring) if docstring else None,
                    'protected': str(filepath) in PROTECTED_FILES,
                })

    return issues


def main():
    src_dir = Path("src")
    issues = []

    for py_file in sorted(src_dir.rglob("*.py")):
        file_issues = analyze_file(py_file)
        issues.extend(file_issues)

    # Categorize
    missing = [i for i in issues if i['status'] == 'missing']
    multi_line = [i for i in issues if i['status'] == 'multi_line']
    invalid = [i for i in issues if i['status'] == 'invalid']

    # Split protected vs non-protected
    missing_np = [i for i in missing if not i['protected']]
    multi_line_np = [i for i in multi_line if not i['protected']]
    invalid_np = [i for i in invalid if not i['protected']]

    missing_p = [i for i in missing if i['protected']]
    multi_line_p = [i for i in multi_line if i['protected']]
    invalid_p = [i for i in invalid if i['protected']]

    print("=" * 80)
    print("DETAILED DOCSTRING AUDIT")
    print("=" * 80)

    print(f"\n--- NON-PROTECTED ISSUES ---")
    print(f"\nMISSING DOCSTRINGS ({len(missing_np)}):")
    print("-" * 80)
    for i in missing_np:
        print(f"  {i['file']}:{i['line']} - {i['function']}")

    print(f"\nMULTI-LINE DOCSTRINGS ({len(multi_line_np)}):")
    print("-" * 80)
    for i in multi_line_np:
        print(f"  {i['file']}:{i['line']} - {i['function']}")

    print(f"\nINVALID DOCSTRINGS ({len(invalid_np)}):")
    print("-" * 80)
    for i in invalid_np:
        print(f"  {i['file']}:{i['line']} - {i['function']}")
        if i['docstring']:
            print(f"    Current: {i['docstring']}")

    print(f"\n--- PROTECTED EXCTIONS (DO NOT MODIFY) ---")
    print(f"\nMISSING ({len(missing_p)}):")
    for i in missing_p:
        print(f"  {i['file']}:{i['line']} - {i['function']}")
    print(f"\nMULTI-LINE ({len(multi_line_p)}):")
    for i in multi_line_p:
        print(f"  {i['file']}:{i['line']} - {i['function']}")
    print(f"\nINVALID ({len(invalid_p)}):")
    for i in invalid_p:
        print(f"  {i['file']}:{i['line']} - {i['function']}")

    print(f"\n{'=' * 80}")
    print(f"NON-PROTECTED: {len(missing_np)} missing + {len(multi_line_np)} multi-line + {len(invalid_np)} invalid = {len(missing_np)+len(multi_line_np)+len(invalid_np)}")
    print(f"PROTECTED: {len(missing_p)} missing + {len(multi_line_p)} multi-line + {len(invalid_p)} invalid = {len(missing_p)+len(multi_line_p)+len(invalid_p)}")


if __name__ == '__main__':
    main()
