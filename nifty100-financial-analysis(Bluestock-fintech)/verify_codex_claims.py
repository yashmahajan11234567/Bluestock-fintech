#!/usr/bin/env python3
"""
Independent verification of Codex's Day 44 function fix claims.

This script verifies the exact 14 functions Codex claimed were fixed.
"""

import ast
from pathlib import Path


def check_function_docstring(file_path, function_name):
    """Check if a function has a one-line docstring."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Get docstring
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):

                    docstring = node.body[0].value.value
                    is_one_line = '\n' not in docstring

                    return {
                        'found': True,
                        'has_docstring': bool(docstring),
                        'is_one_line': is_one_line,
                        'docstring': docstring,
                        'line': node.lineno,
                        'compliant': is_one_line and bool(docstring)
                    }
                else:
                    return {
                        'found': True,
                        'has_docstring': False,
                        'is_one_line': False,
                        'docstring': None,
                        'line': node.lineno,
                        'compliant': False
                    }
    except Exception as e:
        return {'found': False, 'error': str(e)}


def main():
    print("="*80)
    print("INDEPENDENT VERIFICATION OF CODEX'S DAY 44 FIX CLAIMS")
    print("="*80)

    # Codex's claimed fixes from the report
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

    print("\nCODEx'S CLAIMED FIXES TO VERIFY:")
    print("-"*80)

    total_claimed = 0
    total_verified = 0
    verification_results = []

    for file_path_str, function_name in claimed_fixes:
        filepath = Path(file_path_str)

        print(f"\n📁 File: {filepath}")
        print(f"   Function: {function_name}()")

        if not filepath.exists():
            print(f"   ❌ FILE NOT FOUND")
            verification_results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'FAIL - FILE NOT FOUND',
                'compliant': False
            })
            total_claimed += 1
            all_passed = False
            continue

        result = check_function_docstring(filepath, function_name)

        if not result['found']:
            print(f"   ❌ FUNCTION NOT FOUND")
            error = f"Function not found: {result.get('error', 'Unknown error')}"
            verification_results.append({
                'file': file_path_str,
                'function': function_name,
                'status': f'FAIL - {error}',
                'compliant': False
            })
            all_passed = False
        else:
            status = '✅ PASS' if result['compliant'] else '❌ FAIL'
            compliant = result['compliant']
            all_passed = all_passed and compliant if 'all_passed' in locals() else compliant

            print(f"   {status}")
            print(f"   Line: {result.get('line', 'N/A')}")
            if result['has_docstring']:
                doc_preview = result['docstring'][:60] + '...' if len(result['docstring']) > 60 else result['docstring']
                print(f"   Docstring: '{doc_preview}'")
                print(f"   One-line: {'✅' if result['is_one_line'] else '❌'}")
            else:
                print(f"   Docstring: None")

            verification_results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'PASS' if compliant else 'FAIL',
                'compliant': compliant,
                'has_docstring': result.get('has_docstring', False),
                'is_one_line': result.get('is_one_line', False)
            })

            total_claimed += 1
            if compliant:
                total_verified += 1

    # Final Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    print(f"\nTotal claimed fixes: {total_claimed}")
    print(f"✅ Successfully verified: {total_verified}")
    print(f"❌ Failed verification: {total_claimed - total_verified}")

    if all_passed:
        print(f"\n🎉 SUCCESS: All Codex claims verified!")
        print("Codex's report appears accurate and complete.")
    else:
        print(f"\n⚠️  FAILURE: Some Codex claims not verified")
        print("Codex's report may be incomplete or inaccurate.")
        print("\nFailed verifications:")
        for result in verification_results:
            if not result['compliant']:
                print(f"  - {result['file']} - {result['function']}()")

    # Detailed report
    print("\n" + "="*80)
    print("DETAILED VERIFICATION REPORT")
    print("="*80)

    for result in verification_results:
        status_icon = "✅" if result['compliant'] else "❌"
        print(f"{status_icon} {result['file']} - {result['function']}()")

    # Save results
    report_path = Path("codex_verification_report.md")
    with open(report_path, 'w') as f:
        f.write("# Codex Day 44 Fix Verification Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total claimed fixes**: {total_claimed}\n")
        f.write(f"**Successfully verified**: {total_verified}\n")
        f.write(f"**Verification rate**: {total_verified/total_claimed*100:.1f}%\n\n")

        for result in verification_results:
            status = "✅ PASS" if result['compliant'] else "❌ FAIL"
            f.write(f"- {result['file']} - {result['function']}(): {status}\n")

    print(f"\n📄 Detailed report saved to: {report_path}")

    return all_passed

if __name__ == "__main__":
    main()