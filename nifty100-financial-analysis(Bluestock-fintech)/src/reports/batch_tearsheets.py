"""
Day 34: Batch Company Tearsheets Generator.

Iterates over all companies in the database and generates a 2-page
tearsheet PDF for each, reusing the existing ``generate_tearsheet``
function from Day 33.

Usage (CLI):
    python -m src.reports.batch_tearsheets --output-dir Data/output/tearsheets

Usage (API):
    from src.reports.batch_tearsheets import generate_batch_tearsheets
    results = generate_batch_tearsheets("Data/output/tearsheets")
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.dashboard.utils.db import get_company_list

# Import the existing tearsheet generator from Day 33
from src.reports.tearsheet import generate_tearsheet


def _validate_output_dir(output_dir: str) -> str:
    """Ensure *output_dir* exists and return the absolute path."""
    abs_dir = os.path.abspath(output_dir)
    if not os.path.exists(abs_dir):
        os.makedirs(abs_dir, exist_ok=True)
    return abs_dir


def generate_batch_tearsheets(
    output_dir: str,
    company_ids: Optional[List[str]] = None,
    skip_errors: bool = True,
) -> Dict[str, str]:
    """
    Generate tearsheets for all (or a subset of) companies.

    Args:
        output_dir: Directory where PDF files will be written.
        company_ids: Optional list of company IDs to process.
            When ``None`` (default), all companies from the DB are used.
        skip_errors: If ``True`` (default), companies that fail still
            produce a ``None`` entry in the result dict rather than
            raising.  If ``False``, the first error aborts the run.

    Returns:
        Dict mapping company_id → output path (or ``None`` on failure
        when *skip_errors* is ``True``).
    """
    abs_dir = _validate_output_dir(output_dir)

    # Determine the list of companies to process
    if company_ids is None:
        companies = get_company_list()
        company_ids = [c["company_id"] for c in companies]

    results: Dict[str, str] = {}
    errors: List[str] = []

    for i, cid in enumerate(sorted(company_ids), 1):
        out_path = os.path.join(abs_dir, f"tearsheet_{cid}.pdf")
        try:
            generate_tearsheet(cid, out_path)
            results[cid] = out_path
            print(f"  [{i}/{len(company_ids)}] OK {cid}")
        except Exception as exc:
            results[cid] = None
            errors.append(f"{cid}: {exc}")
            print(f"  [{i}/{len(company_ids)}] FAIL {cid} - {exc}")
            if not skip_errors:
                raise

    # ── Summary ──
    total = len(company_ids)
    succeeded = sum(1 for v in results.values() if v is not None)
    print(f"\nBatch complete: {succeeded}/{total} succeeded, "
          f"{len(errors)} failed.")

    if errors:
        print("\nFailures:")
        for err in errors:
            print(f"  - {err}")

    return results


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate batch company tearsheets (Day 34).",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("Data", "output", "tearsheets"),
        help="Output directory for PDF files.",
    )
    parser.add_argument(
        "--companies",
        nargs="*",
        default=None,
        help="Optional list of company IDs to process.",
    )
    parser.add_argument(
        "--no-skip-errors",
        action="store_true",
        help="Abort on first error instead of continuing.",
    )

    args = parser.parse_args()

    results = generate_batch_tearsheets(
        output_dir=args.output_dir,
        company_ids=args.companies,
        skip_errors=not args.no_skip_errors,
    )

    succeeded = sum(1 for v in results.values() if v is not None)
    return 0 if succeeded == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
