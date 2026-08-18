#!/usr/bin/env python3
"""
Independent verification of Codex's 14 specific function fix claims.

This script checks the exact functions Codex claims were fixed in Day 44:
1. src/screener/engine.py - 7 functions
2. src/etl/loader.py - run_etl
3. src/nlp/pros_cons_generator.py - 3 functions
4. src/api/routers/documents.py - 1 function
5. src/api/routers/portfolio.py - 1 function
6. src/dashboard/_pages/_07_capital.py - 1 function

All should have been changed from missing/multi-line/invalid to one-line docstrings.
"""

import ast
from pathlib import Path


def get_function_docstring(file_path, function_name):
    """Get the docstring of a specific function from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == function_name:
                    # Get docstring
                    if (node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        docstring = node.body[0].value.value
                        return {
                            'name': node.name,
                            'docstring': docstring,
                            'is_one_line': '\n' not in docstring,
                            'line': node.lineno,
                            'has_docstring': bool(docstring)
                        }
                    else:
                        return {
                            'name': node.name,
                            'docstring': None,
                            'is_one_line': False,
                            'line': node.lineno,
                            'has_docstring': False
                        }
    except Exception as e:
        print(f"Error analyzing {file_path} for {function_name}: {e}")

    return None


def verify_codex_fixes():
    """Verify all 14 fixes claimed by Codex."""
    print("="*80)
    print("INDEPENDENT VERIFICATION OF CODEX'S 14 FIX CLAIMS")
    print("="*80)

    # Codex's claimed fixes
    claimed_fixes = [
        # src/screener/engine.py - 7 functions
        ('src/screener/engine.py', 'load_screener_data'),
        ('src/screener/engine.py', 'apply_filters'),
        ('src/screener/engine.py', '_winsorize_and_scale'),
        ('src/screener/engine.py', 'run_screener'),
        ('src/screener/engine.py', '_parse_cagr_strings'),
        ('src/screener/engine.py', 'get_quality_compounder_filters'),
        ('src/screener/engine.py', 'generate_screener_output'),

        # src/etl/loader.py - run_etl
        ('src/etl/loader.py', 'run_etl'),

        # src/nlp/pros_cons_generator.py - 3 functions
        ('src/nlp/pros_cons_generator.py', 'generate_pros_cons'),
        ('src/nlp/pros_cons_generator.py', 'generate_peer_pros_cons'),
        ('src/nlp/pros_cons_generator.py', 'generate_company_pros_cons'),

        # src/api/routers/documents.py - 1 function
        ('src/api/routers/documents.py', 'get_documents'),

        # src/api/routers/portfolio.py - 1 function
        ('src/api/routers/portfolio.py', 'get_portfolio'),

        # src/dashboard/_pages/_07_capital.py - 1 function
        ('src/dashboard/_pages/_07_capital.py', 'render_capital_page'),
    ]

    results = []
    all_passed = True

    for file_path_str, function_name in claimed_fixes:
        filepath = Path(file_path_str)
        if not filepath.exists():
            print(f"\n❌ MISSING: {filepath} - File not found!")
            results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'FAIL',
                'error': 'File not found'
            })
            all_passed = False
            continue

        result = get_function_docstring(filepath, function_name)
        if result is None:
            print(f"\n❌ ERROR: {file_path_str} - Function '{function_name}' not found!")
            results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'FAIL',
                'error': 'Function not found'
            })
            all_passed = False
            continue

        # Check if compliant (one-line docstring)
        is_compliant = result['has_docstring'] and result['is_one_line']

        status = '✅ PASS' if is_compliant else '❌ FAIL'
        docstring_preview = result['docstring'][:60] + '...' if result['docstring'] and len(result['docstring']) > 60 else result['docstring'] or 'None'

        print(f"\n{status} {file_path_str}")
        print(f"  Function: {result['name']}()")
        print(f"  Line: {result['line']}")
        print(f"  Docstring: '{docstring_preview}'")
        print(f"  One-line: {result['is_one_line']}")

        if not is_compliant:
            if not result['has_docstring']:
                error = "Missing docstring"
            elif not result['is_one_line']:
                error = "Multi-line docstring"
            else:
                error = "Other issue"

            print(f"  ❌ Issue: {error}")
            results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'FAIL',
                'error': error,
                'current_docstring': result['docstring']
            })
            all_passed = False
        else:
            results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'PASS',
                'error': None
            })

    # Summary
    print(f"\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")

    total_claimed = len(claimed_fixes)
    total_passed = sum(1 for r in results if r['status'] == 'PASS')
    total_failed = sum(1 for r in results if r['status'] == 'FAIL')

    print(f"\nTotal claimed fixes: {total_claimed}")
    print(f"✅ Successfully verified: {total_passed}")
    print(f"❌ Failed verification: {total_failed}")

    if all_passed:
        print(f"\n🎉 SUCCESS: All {total_claimed} claimed fixes are verified!")
        print("Codex's report is accurate.")
        return True
    else:
        print(f"\n⚠️  FAILURE: {total_failed} of {total_claimed} claimed fixes not verified")
        print("Codex's report is inaccurate or incomplete.")
        print("\nFailed fixes:")
        for result in results:
            if result['status'] == 'FAIL':
                print(f"  - {result['file']} - {result['function']}: {result['error']}")
        return False


if __name__ == "__main__":
    success = verify_codex_fixes()
    exit(0 if success else 1)