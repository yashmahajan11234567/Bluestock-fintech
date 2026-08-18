#!/usr/bin/env python3
"""
Verify Codex's 14 specific function fix claims.

Codex claims these functions were fixed in Day 44:
1. src/screener/engine.py - 7 functions
2. src/etl/loader.py - run_etl
3. src/nlp/pros_cons_generator.py - 3 functions
4. src/api/routers/documents.py - 1 function
5. src/api/routers/portfolio.py - 1 function
6. src/dashboard/_pages/_07_capital.py - 1 function

All should be missing → one-line docstrings before Day 44.
"""

import ast
from pathlib import Path


def get_public_functions(file_path):
    """Get all public functions from a file (not starting with underscore)."""
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('_'):
                    continue

                # Get docstring
                docstring = None
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    docstring = node.body[0].value.value

                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': docstring,
                    'is_one_line': docstring is not None and '\n' not in docstring,
                    'file': file_path.name
                })
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return functions


def analyze_file(filepath, expected_fixes):
    """Analyze a file and verify claimed fixes."""
    print(f"\n{'='*70}")
    print(f"ANALYZING: {filepath}")
    print(f"{'='*70}")

    functions = get_public_functions(filepath)

    # Find expected functions
    expected_function_names = []
    for fix in expected_fixes:
        if 'file_path' in fix and Path(fix['file_path']) == Path(filepath):
            expected_function_names.append(fix['function_name'])

    print(f"\nExpected to be fixed: {expected_function_names}")

    fixed_count = 0
    errors = []

    for func in functions:
        if func['name'] in expected_function_names:
            if func['is_one_line'] and func['docstring']:
                fixed_count += 1
                print(f"✓ FIXED: {func['name']}() - one-line docstring")
                print(f"  Docstring: '{func['docstring']}'")
            else:
                if not func['docstring']:
                    status = "MISSING"
                elif not func['is_one_line']:
                    status = "MULTI-LINE"
                else:
                    status = "OTHER ISSUE"

                errors.append(f"{func['name']}() - {status}")
                print(f"✗ NOT FIXED: {func['name']}() - {status}")
                if func['docstring']:
                    print(f"  Current docstring (len={len(func['docstring'])}): '{func['docstring'][:100]}...'")
                else:
                    print(f"  No docstring")

    print(f"\nSUMMARY for {filepath.name}:")
    print(f"  Expected to be fixed: {len(expected_function_names)}")
    print(f"  ✓ Actually fixed: {fixed_count}")
    print(f"  ✗ Not fixed: {len(expected_function_names) - fixed_count}")

    return {
        'expected': len(expected_function_names),
        'fixed': fixed_count,
        'errors': errors,
        'file': str(filepath)
    }


def main():
    print("VERIFICATION OF CODEX'S 14 SPECIFIC FIXES")
    print("="*70)

    # Expected fixes based on Codex report
    expected_fixes = [
        # src/screener/engine.py - 7 functions
        {'file_path': 'src/screener/engine.py', 'function_name': 'load_screener_data'},
        {'file_path': 'src/screener/engine.py', 'function_name': 'apply_filters'},
        {'file_path': 'src/screener/engine.py', 'function_name': '_winsorize_and_scale'},
        {'file_path': 'src/screener/engine.py', 'function_name': 'run_screener'},
        {'file_path': 'src/screener/engine.py', 'function_name': '_parse_cagr_strings'},
        {'file_path': 'src/screener/engine.py', 'function_name': 'get_quality_compounder_filters'},
        {'file_path': 'src/screener/engine.py', 'function_name': 'generate_screener_output'},

        # src/etl/loader.py - run_etl
        {'file_path': 'src/etl/loader.py', 'function_name': 'run_etl'},

        # src/nlp/pros_cons_generator.py - 3 functions
        {'file_path': 'src/nlp/pros_cons_generator.py', 'function_name': 'generate_pros_cons'},
        {'file_path': 'src/nlp/pros_cons_generator.py', 'function_name': 'generate_peer_pros_cons'},
        {'file_path': 'src/nlp/pros_cons_generator.py', 'function_name': 'generate_company_pros_cons'},

        # src/api/routers/documents.py - 1 function
        {'file_path': 'src/api/routers/documents.py', 'function_name': 'get_documents'},

        # src/api/routers/portfolio.py - 1 function
        {'file_path': 'src/api/routers/portfolio.py', 'function_name': 'get_portfolio'},

        # src/dashboard/_pages/_07_capital.py - 1 function
        {'file_path': 'src/dashboard/_pages/_07_capital.py', 'function_name': 'render_capital_page'},
    ]

    # Analyze each claimed fix
    results = []
    for fix in expected_fixes:
        filepath = Path(fix['file_path'])
        if filepath.exists():
            result = analyze_file(filepath, [fix])
            results.append(result)
        else:
            print(f"\n{'='*70}")
            print(f"ERROR: File not found: {filepath}")
            print(f"{'='*70}")
            results.append({
                'expected': 1,
                'fixed': 0,
                'errors': [f"File not found: {filepath}"],
                'file': str(filepath)
            })

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY OF CODEX'S 14 FIXES")
    print(f"{'='*70}")

    total_expected = sum(r['expected'] for r in results)
    total_fixed = sum(r['fixed'] for r in results)

    print(f"\nTotal expected to be fixed: {total_expected}")
    print(f"✓ Actually fixed: {total_fixed}")
    print(f"✗ Not fixed: {total_expected - total_fixed}")

    if total_fixed == total_expected:
        print(f"\n✅ SUCCESS: All {total_expected} claimed fixes verified!")
        print("Codex's report appears accurate.")
    else:
        print(f"\n❌ FAILURE: {total_expected - total_fixed} fixes not verified")
        print("Codex's report appears inaccurate or incomplete.")

    # List all errors
    print(f"\n{'='*70}")
    print("UNVERIFIED/FIXED CLAIMS")
    print(f"{'='*70}")

    all_errors = []
    for result in results:
        if result['errors']:
            print(f"\n{result['file']}:")
            for error in result['errors']:
                print(f"  ✗ {error}")
                all_errors.append(error)

    if all_errors:
        print(f"\n{'='*70}")
        print("CONCLUSION: NOT ALL CODEX CLAIMS VERIFIED")
        print(f"{'='*70}")
        print(f"Total errors: {len(all_errors)}")
        return False
    else:
        print(f"\n{'='*70}")
        print("CONCLUSION: ALL CODEX CLAIMS VERIFIED")
        print(f"{'='*70}")
        print("Codex's report is accurate.")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)