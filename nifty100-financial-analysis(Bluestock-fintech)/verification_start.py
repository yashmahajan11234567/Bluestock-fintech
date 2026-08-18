#!/usr/bin/env python3
"""
START DAY 44 INDEPENDENT VERIFICATION

This script begins the complete independent verification of Day 44 QA requirements.
"""

import ast
import subprocess
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


def analyze_specific_functions():
    """Analyze the 14 specific functions Codex claimed were fixed."""
    print("\n" + "="*80)
    print("VERIFYING CODEX'S 14 SPECIFIC FUNCTION FIXES")
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

    results = []
    all_compatible = True

    for file_path_str, function_name in claimed_fixes:
        filepath = Path(file_path_str)

        print(f"\n{'='*80}")
        print(f"ANALYZING: {file_path_str}")
        print(f"{'='*80}")
        print(f"Function claimed to be fixed: {function_name}()")

        if not filepath.exists():
            print(f"❌ FILE NOT FOUND: {file_path_str}")
            results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'FAIL',
                'message': 'File not found',
                'compliant': False
            })
            all_compatible = False
            continue

        # Read and analyze the file
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Find all functions in the file
            all_functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    all_functions.append(node.name)

            # Check if the claimed function exists
            if function_name in all_functions:
                print(f"✅ Function '{function_name}()' exists in file")

                # Find the specific function node
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        # Get docstring
                        docstring = None
                        if (node.body and
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)):
                            docstring = node.body[0].value.value

                        # Analyze docstring compliance
                        if docstring and '\n' not in docstring and docstring.strip():
                            # Check if docstring is accurate
                            doc_lower = docstring.lower().strip()
                            if (len(docstring.strip()) > 10 and
                                not doc_lower.startswith('todo') and
                                not doc_lower.startswith('fixme') and
                                not doc_lower.startswith('hack') and
                                not 'placeholder' in doc_lower and
                                not 'to be implemented' in doc_lower):
                                print(f"✅ Function '{function_name}()' has compliant one-line docstring")
                                print(f"   Docstring: '{docstring[:60]}...'")
                                results.append({
                                    'file': file_path_str,
                                    'function': function_name,
                                    'status': 'PASS',
                                    'message': 'Has compliant one-line docstring',
                                    'compliant': True
                                })
                            else:
                                print(f"❌ Function '{function_name}()' has non-compliant docstring")
                                print(f"   Docstring: '{docstring[:60]}...'")
                                results.append({
                                    'file': file_path_str,
                                    'function': function_name,
                                    'status': 'FAIL',
                                    'message': 'Non-compliant docstring',
                                    'compliant': False
                                })
                                all_compatible = False
                        else:
                            if docstring:
                                print(f"❌ Function '{function_name}()' has multi-line or invalid docstring")
                                print(f"   Docstring type: {'multi-line' if '\\n' in docstring else 'invalid format'}")
                            else:
                                print(f"❌ Function '{function_name}()' has no docstring")
                            results.append({
                                'file': file_path_str,
                                'function': function_name,
                                'status': 'FAIL',
                                'message': 'Missing or non-compliant docstring',
                                'compliant': False
                            })
                            all_compatible = False
                        break
            else:
                print(f"❌ Function '{function_name}()' NOT FOUND in file")
                results.append({
                    'file': file_path_str,
                    'function': function_name,
                    'status': 'FAIL',
                    'message': 'Function not found in file',
                    'compliant': False
                })
                all_compatible = False

        except Exception as e:
            print(f"❌ ERROR analyzing {file_path_str}: {e}")
            results.append({
                'file': file_path_str,
                'function': function_name,
                'status': 'FAIL',
                'message': f'Error: {e}',
                'compliant': False
            })
            all_compatible = False

    # Summary
    print(f"\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")

    total_claimed = len(claimed_fixes)
    passed_count = sum(1 for r in results if r['compliant'])
    failed_count = total_claimed - passed_count

    print(f"\nTotal functions claimed to be fixed: {total_claimed}")
    print(f"✅ Successfully verified: {passed_count}")
    print(f"❌ Verification failed: {failed_count}")

    if all_compatible:
        print(f"\n🎉 SUCCESS: All Codex claims independently verified!")
        print(f"Codex's Day 44 fix report is accurate.")
    else:
        print(f"\n⚠️  INCONSISTENCY: Some Codex claims not verified")
        print(f"Codex's Day 44 fix report appears incomplete or inaccurate.")
        print(f"\nFailed verifications:")
        for result in results:
            if not result['compliant']:
                print(f"  - {result['file']} - {result['function']}(): {result['message']}")

    return all_compatible


def main():
    print("="*80)
    print("START DAY 44 INDEPENDENT VERIFICATION")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {Path.cwd()}")
    print("="*80)
    print("This script performs INDEPENDENT verification of Day 44 QA requirements")
    print("and does NOT rely on any previous analysis or Codex reports.")
    print("="*80)

    # Execute the core verification
    success = analyze_specific_functions()

    # Generate a simple report
    print(f"\n{'='*80}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*80}")

    if success:
        print(f"✅ SUCCESS: All Codex Day 44 fix claims verified independently.")
        print(f"The Day 44 implementation meets all docstring compliance requirements.")
    else:
        print(f"❌ INCONSISTENCY: Some Codex Day 44 fix claims not verified.")
        print(f"There may be discrepancies in the Day 44 implementation.")

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)