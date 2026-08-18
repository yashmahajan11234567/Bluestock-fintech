#!/usr/bin/env python3
"""
Final independent verification of Codex's Day 44 function fix claims.

This script verifies the exact 14 functions Codex claimed were fixed in Day 44.
"""

import ast
from pathlib import Path
from datetime import datetime


def analyze_function_docstring(file_path, function_name):
    """Analyze a specific function for its docstring compliance."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Extract docstring
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):

                    docstring = node.body[0].value.value

                    # Determine compliance
                    has_docstring = bool(docstring)
                    is_one_line = has_docstring and '\n' not in docstring.strip()

                    # Check if docstring accurately describes purpose (basic validation)
                    is_accurate = False
                    if is_one_line:
                        doc_lower = docstring.lower().strip()
                        # Basic accuracy check - not empty, not placeholder
                        if (len(docstring.strip()) > 10 and  # Reasonable length
                            not doc_lower.startswith('todo') and
                            not doc_lower.startswith('fixme') and
                            not doc_lower.startswith('hack') and
                            not 'placeholder' in doc_lower and
                            not 'to be implemented' in doc_lower and
                            not 'unimplemented' in doc_lower):
                            is_accurate = True

                    return {
                        'found': True,
                        'compliant': has_docstring and is_one_line and is_accurate,
                        'has_docstring': has_docstring,
                        'is_one_line': is_one_line,
                        'is_accurate': is_accurate,
                        'docstring': docstring,
                        'line': node.lineno,
                        'issue': None
                    }
                else:
                    return {
                        'found': True,
                        'compliant': False,
                        'has_docstring': False,
                        'is_one_line': False,
                        'is_accurate': False,
                        'docstring': None,
                        'line': node.lineno,
                        'issue': 'Missing docstring'
                    }
    except Exception as e:
        return {'found': False, 'error': str(e), 'compliant': False}


def main():
    print("="*80)
    print("FINAL INDEPENDENT VERIFICATION OF CODEX'S DAY 44 FIX CLAIMS")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Codex's exact claims
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

    print("\n📋 CODEX'S CLAIMED FIXES:")
    print("-"*80)

    for i, (file_path, func_name) in enumerate(claimed_fixes, 1):
        print(f"{i}. {file_path} - {func_name}()")

    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)

    results = []
    all_verified = True

    for i, (file_path_str, func_name) in enumerate(claimed_fixes, 1):
        filepath = Path(file_path_str)

        print(f"\n{i}. 📁 {file_path_str}")
        print(f"   Function: {func_name}()")
        print(f"   Status: Checking...")

        if not filepath.exists():
            print(f"   ❌ FILE NOT FOUND")
            results.append({
                'file': file_path_str,
                'function': func_name,
                'status': 'FAIL',
                'compliant': False,
                'error': 'File not found'
            })
            all_verified = False
            continue

        result = analyze_function_docstring(filepath, func_name)

        if not result['found']:
            print(f"   ❌ FUNCTION NOT FOUND")
            print(f"   Error: {result.get('error', 'Unknown')}")
            results.append({
                'file': file_path_str,
                'function': func_name,
                'status': 'FAIL',
                'compliant': False,
                'error': result.get('error', 'Function not found')
            })
            all_verified = False
        else:
            status = "✅ PASS" if result['compliant'] else "❌ FAIL"
            issue = result.get('issue', '')

            print(f"   {status}")
            if result['has_docstring']:
                doc_preview = result['docstring'][:50] + '...' if len(result['docstring']) > 50 else result['docstring']
                print(f"   Docstring: '{doc_preview}'")
                print(f"   One-line: {'✅' if result['is_one_line'] else '❌'}")
                print(f"   Accurate: {'✅' if result['is_accurate'] else '❌'}")
            else:
                print(f"   Docstring: None")
                if issue:
                    print(f"   Issue: {issue}")

            results.append({
                'file': file_path_str,
                'function': func_name,
                'status': 'PASS' if result['compliant'] else 'FAIL',
                'compliant': result['compliant'],
                'has_docstring': result['has_docstring'],
                'is_one_line': result['is_one_line'],
                'is_accurate': result['is_accurate'],
                'issue': issue
            })

            if not result['compliant']:
                all_verified = False

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    total_claimed = len(claimed_fixes)
    total_verified = sum(1 for r in results if r['compliant'])
    total_failed = total_claimed - total_verified

    print(f"\nTotal claimed fixes: {total_claimed}")
    print(f"✅ Successfully verified: {total_verified}")
    print(f"❌ Verification failed: {total_failed}")

    if total_verified == total_claimed:
        print(f"\n🎉 SUCCESS: All Codex claims have been independently verified!")
        print("Codex's report accurately reflects the Day 44 fixes.")
        final_verdict = "PASS WITH CONFIRMED VERIFICATION"
    else:
        print(f"\n⚠️  INCONSISTENCY: {total_failed} claimed fixes not verified")
        print("Codex's report appears inaccurate or incomplete.")
        print("\nFailed verifications:")
        for result in results:
            if not result['compliant']:
                issue = f" - {result['issue']}" if result.get('issue') else ""
                print(f"  - {result['file']} - {result['function']}(){issue}")
        final_verdict = "FAIL - VERIFICATION INCONSISTENT WITH CODEX REPORT"

    # Generate comprehensive report
    print("\n" + "="*80)
    print("DETAILED VERIFICATION REPORT")
    print("="*80)

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['compliant'] else "❌ FAIL"
        print(f"{i}. {result['file']} - {result['function']}(): {status}")
        if result.get('issue'):
            print(f"   Issue: {result['issue']}")

    # Save detailed report
    report_path = Path("final_codex_verification_report.md")
    with open(report_path, 'w') as f:
        f.write("# Codex Day 44 Fix Verification - Final Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Repository: nifty100-financial-analysis(Bluestock-fintech)\n\n")

        f.write(f"## Executive Summary\n")
        f.write(f"- **Total claimed fixes**: {total_claimed}\n")
        f.write(f"- **Successfully verified**: {total_verified}\n")
        f.write(f"- **Verification rate**: {total_verified/total_claimed*100:.1f}%\n")
        f.write(f"- **Final verdict**: {final_verdict}\n\n")

        f.write(f"## Verification Results\n")
        for result in results:
            status = "✅ PASS" if result['compliant'] else "❌ FAIL"
            f.write(f"- **{result['file']}** - **{result['function']}()**: {status}\n")
            if result.get('issue'):
                f.write(f"  - Issue: {result['issue']}\n")

        f.write(f"\n## Conclusion\n")
        if final_verdict.startswith("SUCCESS") or "PASS" in final_verdict:
            f.write(f"✅ All claimed fixes have been independently verified. "
                   f"Codex's report is accurate and complete.\n")
        else:
            f.write(f"❌ {total_failed} claimed fixes could not be independently verified. "
                   f"Codex's report appears incomplete or inaccurate.\n")

    print(f"\n📄 Detailed verification report saved to: {report_path}")

    return all_verified

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)