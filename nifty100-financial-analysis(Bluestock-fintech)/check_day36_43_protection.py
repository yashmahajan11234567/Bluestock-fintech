#!/usr/bin/env python3
"""
Check Day 36-43 file protection compliance for Day 44 QA.

This script verifies that protected files from Days 36-43 have NOT been
modified in Day 44, except for approved changes mentioned in the instructions.
"""

import subprocess
from pathlib import Path


def run_git_command(cmd):
    """Run git command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def main():
    print("DAY 36-43 PROTECTION INSPECTION")
    print("=" * 80)

    # Files that should be PROTECTED from Day 44 changes
    protected_files = {
        "DAY 36": [
            "src/analytics/clustering.py",
            "output/cluster_labels.csv",
        ],
        "DAY 37": [
            "src/analytics/cluster_profiling.py",
            "output/cluster_profiles.csv",
            "output/outlier_report.csv",
            "output/portfolio_stats.csv",
            "reports/correlation_heatmap.png",
        ],
        "DAY 38": [
            "src/api/main.py",
            "src/api/routers/health.py",
        ],
        "DAY 39": [
            "src/api/routers/companies.py",
            "src/api/schemas/company.py",
            "tests/api/test_companies.py",
        ],
        "DAY 40": [
            "src/api/routers/screener.py",
            "src/api/routers/sectors.py",
            "src/api/routers/peers.py",
            "src/api/schemas/screener.py",
            "src/api/schemas/sector.py",
            "src/api/schemas/peer.py",
        ],
        "DAY 41": [
            "src/api/routers/valuation.py",
            "src/api/schemas/valuation.py",
            "tests/api/test_valuation.py",
        ],
        "DAY 42": [
            "tests/api/test_health.py",
            "tests/api/test_companies.py",
            "tests/api/test_screener.py",
            "tests/api/test_sectors.py",
            "tests/api/test_integration_dashboard_api.py",
            "reports/pytest_report.html",
        ],
        "DAY 43": [
            "src/dashboard/utils/db.py",
            "output/perf_notes.md",
            "tests/performance/test_day43_performance.py",
            "scripts/day43_performance.py",
            "scripts/day43_e2e_test.py",
        ],
    }

    # IMPORTANT: src/dashboard/utils/db.py contains approved Day 40 and Day 43
    # changes. Do not classify those existing changes as a Day 44 defect.
    approved_day40_43_changes = {"src/dashboard/utils/db.py"}

    print("Checking protected files for Day 44 modifications...")
    print("(Note: src/dashboard/utils/db.py changes are approved)\n")

    violations = []
    approved_changes = []

    for day, files in protected_files.items():
        print(f"{day}:")
        for file_path in files:
            if file_path in approved_day40_43_changes:
                print(f"  ✓ {file_path}: APPROVED DAY 40/43 CHANGES")
                approved_changes.append(file_path)
                continue

            # Check if file exists
            if not Path(file_path).exists():
                print(f"  ⚠ {file_path}: FILE DOES NOT EXIST")
                continue

            # Check git status
            code, stdout, stderr = run_git_command(
                f"git status --porcelain {file_path}"
            )

            if code == 0 and " M" in stdout:
                print(f"  ✗ {file_path}: MODIFIED (DAY 44 VIOLATION)")
                violations.append({
                    "day": day,
                    "file": file_path,
                    "type": "modification"
                })
            elif code == 0 and "??" in stdout:
                print(f"  + {file_path}: NEW FILE (DAY 44 VIOLATION)")
                violations.append({
                    "day": day,
                    "file": file_path,
                    "type": "new_file"
                })
            else:
                print(f"  ✓ {file_path}: UNCHANGED")

    print("\n" + "=" * 80)
    print("PROTECTION SUMMARY:")
    print("=" * 80)

    if not violations:
        print("✓ NO PROTECTION VIOLATIONS FOUND")
        print("✓ All Day 36-43 protected files are unchanged from Day 44")
        return True
    else:
        print(f"✗ {len(violations)} PROTECTION VIOLATIONS FOUND:")
        for violation in violations:
            print(f"  - {violation['day']}: {violation['file']} ({violation['type']})")

        print(f"\nAPPROVED CHANGES:")
        for approved in approved_changes:
            print(f"  ✓ {approved}: Approved Day 40/43 changes")

        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)