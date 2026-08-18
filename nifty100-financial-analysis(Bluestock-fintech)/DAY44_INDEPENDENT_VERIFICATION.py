#!/usr/bin/env python3
"""
INDEPENDENT VERIFICATION OF DAY 44 QA COMPLIANCE

This script performs complete independent verification of all Day 44 QA requirements,
checking against the actual codebase state rather than relying on Codex reports.
"""

import ast
import subprocess
import re
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """Run a command and return results."""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    print(f"Command: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"✅ SUCCESS")
            if result.stdout:
                preview = result.stdout[:300]
                print(f"Output preview: {preview}...")
        else:
            print(f"❌ FAILED (exit code: {result.returncode})")
            if result.stderr:
                error_preview = result.stderr[:300]
                print(f"Error: {error_preview}...")
            if result.stdout:
                print(f"Output: {result.stdout[:300]}...")

        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT")
        return -1, "", "Command timed out"
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return -1, "", str(e)


def analyze_docstring_compliance(filepath):
    """Analyze a Python file for docstring compliance."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        total = 0
        one_line = 0
        missing = 0
        multi_line = 0
        invalid = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('_'):
                    continue

                total += 1

                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):

                    docstring = node.body[0].value.value

                    if '\n' not in docstring and docstring.strip():
                        # Check if docstring is accurate
                        doc_lower = docstring.lower().strip()
                        if (len(docstring.strip()) > 10 and
                            not doc_lower.startswith('todo') and
                            not doc_lower.startswith('fixme') and
                            not doc_lower.startswith('hack') and
                            not 'placeholder' in doc_lower and
                            not 'to be implemented' in doc_lower):
                            one_line += 1
                        else:
                            invalid += 1
                    else:
                        multi_line += 1
                else:
                    missing += 1

        return total, one_line, missing, multi_line, invalid

    except Exception as e:
        print(f"Warning: Could not analyze {filepath}: {e}")
        return 0, 0, 0, 0, 0


def get_all_python_files(directory):
    """Get all Python files in a directory recursively."""
    python_files = []
    for py_file in Path(directory).rglob("*.py"):
        # Skip cache directories
        if "__pycache__" not in str(py_file):
            python_files.append(py_file)
    return python_files


def check_specific_files():
    """Check the specific files Codex claimed were fixed."""
    print("\n" + "="*80)
    print("CHECKING CODEX'S CLAIMED 14 FIXES")
    print("="*80)

    # Files and functions Codex claimed were fixed
    claimed_fixes = [
        ('src/screener/engine.py', [
            'load_screener_data',
            'apply_filters',
            '_winsorize_and_scale',
            'run_screener',
            '_parse_cagr_strings',
            'get_quality_compounder_filters',
            'generate_screener_output'
        ]),
        ('src/etl/loader.py', ['run_etl']),
        ('src/nlp/pros_cons_generator.py', [
            'generate_pros_cons',
            'generate_peer_pros_cons',
            'generate_company_pros_cons'
        ]),
        ('src/api/routers/documents.py', ['get_documents']),
        ('src/api/routers/portfolio.py', ['get_portfolio']),
        ('src/dashboard/_pages/_07_capital.py', ['render_capital_page']),
    ]

    results = []
    all_compatible = True

    for file_path_str, functions in claimed_fixes:
        filepath = Path(file_path_str)

        print(f"\n{'='*80}")
        print(f"ANALYZING: {file_path_str}")
        print(f"{'='*80}")

        if not filepath.exists():
            print(f"❌ FILE NOT FOUND: {file_path_str}")
            results.append({
                'file': file_path_str,
                'status': 'FAIL',
                'message': 'File not found',
                'functions_checked': len(functions)
            })
            all_compatible = False
            continue

        # Analyze the file
        file_total = 0
        file_one_line = 0
        file_missing = 0
        file_multi_line = 0
        file_invalid = 0
        functions_found = []
        functions_missing_docstring = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Find all functions in the file
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    functions_found.append(node.name)

                    if (node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):

                        docstring = node.body[0].value.value

                        if '\n' not in docstring and docstring.strip():
                            doc_lower = docstring.lower().strip()
                            if (len(docstring.strip()) > 10 and
                                not doc_lower.startswith('todo') and
                                not doc_lower.startswith('fixme') and
                                not doc_lower.startswith('hack') and
                                not 'placeholder' in doc_lower and
                                not 'to be implemented' in doc_lower):
                                file_one_line += 1
                            else:
                                file_invalid += 1
                        else:
                            file_multi_line += 1
                    else:
                        file_missing += 1

            file_total = len(functions_found)

            # Check if claimed functions are in the file
            claimed_in_file = [f for f in functions if f in functions_found]
            claimed_not_in_file = [f for f in functions if f not in functions_found]

            print(f"Functions in file: {file_total}")
            print(f"Functions claimed to be fixed: {len(functions)}")
            print(f"Functions actually in file and claimed: {len(claimed_in_file)}")
            print(f"Functions claimed but not in file: {claimed_not_in_file}")

            if claimed_not_in_file:
                print(f"❌ FUNCTIONS CLAIMED BUT NOT FOUND: {claimed_not_in_file}")
                all_compatible = False

            # Check compliance for functions in file
            if file_missing > 0 or file_multi_line > 0 or file_invalid > 0:
                print(f"❌ NON-COMPLIANT FUNCTIONS:")
                print(f"   Missing docstrings: {file_missing}")
                print(f"   Multi-line docstrings: {file_multi_line}")
                print(f"   Invalid docstrings: {file_invalid}")
                all_compatible = False
            else:
                print(f"✅ ALL FUNCTIONS COMPLIANT")
                print(f"   One-line docstrings: {file_one_line}")

            results.append({
                'file': file_path_str,
                'status': 'PASS' if (len(claimed_not_in_file) == 0 and
                                 file_missing == 0 and
                                 file_multi_line == 0 and
                                 file_invalid == 0) else 'FAIL',
                'message': f'Found {file_total} functions, {file_one_line} compliant',
                'functions_checked': len(functions),
                'functions_in_file': len(functions_found),
                'missing': file_missing,
                'multi_line': file_multi_line,
                'invalid': file_invalid
            })

        except Exception as e:
            print(f"❌ ERROR analyzing {file_path_str}: {e}")
            results.append({
                'file': file_path_str,
                'status': 'FAIL',
                'message': f'Error: {e}',
                'functions_checked': len(functions)
            })
            all_compatible = False

    # Summary
    print(f"\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")

    total_files = len(claimed_fixes)
    passed_files = sum(1 for r in results if r['status'] == 'PASS')
    failed_files = total_files - passed_files

    print(f"\nTotal files claimed to be fixed: {total_files}")
    print(f"✅ Successfully verified: {passed_files}")
    print(f"❌ Verification failed: {failed_files}")

    if all_compatible:
        print(f"\n🎉 SUCCESS: All Codex claims independently verified!")
        print("Codex's report appears accurate.")
        return True
    else:
        print(f"\n⚠️  INCONSISTENCY: Some Codex claims not verified")
        print("Codex's report appears incomplete or inaccurate.")
        print("\nFailed verifications:")
        for result in results:
            if result['status'] == 'FAIL':
                print(f"  - {result['file']}: {result['message']}")
        return False


def analyze_docstring_compliance():
    """Analyze overall docstring compliance across the entire codebase."""
    print("\n" + "="*80)
    print("OVERALL DOCSTRING COMPLIANCE ANALYSIS")
    print("="*80)

    src_dir = Path("src")
    all_python_files = get_all_python_files(src_dir)

    print(f"Analyzing {len(all_python_files)} Python files in src/...")

    total_functions = 0
    total_one_line = 0
    total_missing = 0
    total_multi_line = 0
    total_invalid = 0
    files_with_issues = []

    for py_file in all_python_files:
        total, one_line, missing, multi_line, invalid = analyze_docstring_compliance(py_file)

        total_functions += total
        total_one_line += one_line
        total_missing += missing
        total_multi_line += multi_line
        total_invalid += invalid

        if missing > 0 or multi_line > 0 or invalid > 0:
            files_with_issues.append({
                'file': str(py_file),
                'missing': missing,
                'multi_line': multi_line,
                'invalid': invalid
            })

    # Report results
    print(f"\nDOCSTRING COMPLIANCE SUMMARY:")
    print(f"  TOTAL PUBLIC FUNCTIONS: {total_functions}")
    print(f"  WITH ONE-LINE DOCSTRING: {total_one_line}")
    print(f"  MISSING: {total_missing}")
    print(f"  MULTI-LINE: {total_multi_line}")
    print(f"  INVALID: {total_invalid}")

    # Check requirements
    requirements_met = (total_missing == 0 and total_multi_line == 0 and total_invalid == 0)

    if requirements_met:
        print(f"\n✅ ALL REQUIREMENTS MET")
        print(f"   - Missing docstrings: 0 (required: 0)")
        print(f"   - Multi-line docstrings: 0 (required: 0)")
        print(f"   - Invalid docstrings: 0 (required: 0)")
        return True
    else:
        print(f"\n❌ REQUIREMENTS NOT MET")
        print(f"   - Missing docstrings: {total_missing} (required: 0)")
        print(f"   - Multi-line docstrings: {total_multi_line} (required: 0)")
        print(f"   - Invalid docstrings: {total_invalid} (required: 0)")

        print(f"\nFiles with docstring issues:")
        for issue in files_with_issues[:10]:  # Show first 10
            print(f"  - {issue['file']}: {issue['missing']} missing, {issue['multi_line']} multi-line, {issue['invalid']} invalid")
        if len(files_with_issues) > 10:
            print(f"  ... and {len(files_with_issues) - 10} more files")

        return False


def check_code_quality():
    """Check BLACK and RUFF compliance."""
    print("\n" + "="*80)
    print("CODE QUALITY VERIFICATION")
    print("="*80)

    # BLACK check
    print(f"\n1. BLACK FORMATTING:")
    code, stdout, stderr = run_command(
        "python -m black --check src/ tests/",
        "Running BLACK formatting check"
    )

    if "All done" in stdout:
        print(f"✅ BLACK PASS - All files properly formatted")
        black_status = "PASS"
    else:
        print(f"❌ BLACK FAIL - Formatting issues found")
        black_status = "FAIL"

    # RUFF check
    print(f"\n2. RUFF LINTING:")
    code, stdout, stderr = run_command(
        "python -m ruff check src/ tests/ --output-format=concise",
        "Running RUFF linting check"
    )

    if "All checks passed" in stdout:
        print(f"✅ RUFF PASS - No violations found")
        ruff_status = "PASS"
    else:
        print(f"❌ RUFF FAIL - Violations found")
        ruff_status = "FAIL"

    return black_status, ruff_status


def main():
    print("="*80)
    print("INDEPENDENT DAY 44 QA VERIFICATION")
    print("="*80)
    print(f"Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directory: {Path.cwd()}")
    print("="*80)
    print("NOTE: This script performs independent verification of Day 44 requirements")
    print("and does NOT modify any files.")
    print("="*80)

    # Execute all verification sections
    overall_success = True

    # Section 1: Check Codex's specific claims
    codex_success = check_specific_files()
    overall_success = overall_success and codex_success

    # Section 2: Overall docstring compliance
    doc_success = analyze_docstring_compliance()
    overall_success = overall_success and doc_success

    # Section 3: Code quality
    black_status, ruff_status = check_code_quality()

    # Generate final report
    print(f"\n{'='*80}")
    print("FINAL VERIFICATION REPORT")
    print(f"{'='*80}")

    print(f"\n{'='*80}")
    print("EXECUTION SUMMARY")
    print(f"{'='*80}")

    print(f"\nStatus: {'✅ PASS' if overall_success else '❌ FAIL'}")
    print(f"Codex verification: {'✅ VERIFIED' if codex_success else '❌ NOT VERIFIED'}")
    print(f"Docstring compliance: {'✅ COMPLIANT' if doc_success else '❌ ISSUES FOUND'}")
    print(f"BLACK formatting: {black_status}")
    print(f"RUFF linting: {ruff_status}")

    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}")

    if overall_success:
        print(f"🎉 SUCCESS: All Day 44 QA requirements have been independently verified!")
        print(f"The implementation meets all compliance standards.")
    else:
        print(f"❌ FAILURE: Some Day 44 QA requirements are not met.")
        print(f"The implementation does not fully comply with Day 44 standards.")

    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)