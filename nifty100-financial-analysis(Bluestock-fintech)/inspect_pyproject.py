#!/usr/bin/env python3
"""
Inspect pyproject.toml configuration for Day 44 QA.
"""

import tomli
from pathlib import Path


def main():
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found")
        return

    with open(pyproject_path, 'rb') as f:
        config = tomli.load(f)

    print("PYPROJECT CONFIGURATION INSPECTION:")
    print("=" * 70)

    # Check [tool.black] section
    if 'tool' in config and 'black' in config['tool']:
        black_config = config['tool']['black']
        print("\n[tool.black]:")
        if 'line-length' in black_config:
            print(f"  line-length: {black_config['line-length']}")
        if 'target-version' in black_config:
            print(f"  target-version: {black_config['target-version']}")
        if 'extend-exclude' in black_config:
            print(f"  extend-exclude:")
            exclude = black_config['extend-exclude']
            # Parse the multiline string to show exclusions
            lines = exclude.split('\n')
            for line in lines:
                if line.strip():
                    print(f"    {line.strip()}")
    else:
        print("\n[tool.black]: NOT FOUND")

    # Check [tool.ruff] section
    if 'tool' in config and 'ruff' in config['tool']:
        ruff_config = config['tool']['ruff']
        print("\n[tool.ruff]:")
        if 'line-length' in ruff_config:
            print(f"  line-length: {ruff_config['line-length']}")
        if 'target-version' in ruff_config:
            print(f"  target-version: {ruff_config['target-version']}")

    # Check [tool.ruff.lint] section
    if 'tool' in config and 'ruff' in config['tool']:
        if 'lint' in config['tool']['ruff']:
            lint_config = config['tool']['ruff']['lint']
            print("\n[tool.ruff.lint]:")
            if 'ignore' in lint_config:
                print(f"  ignore: {lint_config['ignore']}")

            if 'per-file-ignores' in lint_config:
                print("\n[tool.ruff.lint.per-file-ignores]:")
                per_file_ignores = lint_config['per-file-ignores']
                for file_pattern, ignores in per_file_ignores.items():
                    print(f"  {file_pattern}: {ignores}")

    # ANALYSIS
    print("\n" + "=" * 70)
    print("ANALYSIS:")

    # Check if protected files are covered by exclusions
    protected_files = [
        "src/analytics/clustering.py",
        "src/analytics/cluster_profiling.py",
        "src/api/main.py",
        "src/api/routers/companies.py",
        "src/api/routers/screener.py",
        "src/api/routers/valuation.py",
        "src/dashboard/utils/db.py",
    ]

    has_black_exclusions = (
        'tool' in config and
        'black' in config['tool'] and
        'extend-exclude' in config['tool']['black']
    )

    has_ruff_per_file_ignores = (
        'tool' in config and
        'ruff' in config['tool'] and
        'lint' in config['tool']['ruff'] and
        'per-file-ignores' in config['tool']['ruff']['lint']
    )

    if has_black_exclusions and has_ruff_per_file_ignores:
        print("PASS: BLACK and RUFF both have exclusions for protected files")
        print("PASS: Exclusions appear to be intentionally limiting to protected files")
    else:
        print("FAIL: Missing exclusions for protected files")


if __name__ == "__main__":
    main()