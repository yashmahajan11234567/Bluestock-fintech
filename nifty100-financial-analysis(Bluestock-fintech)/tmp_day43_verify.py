"""
Day 43 Fix — Verify optimized output matches baseline.
Compares day43_baseline.json results against current get_screener_results()
output.  Must be mathematically equivalent (within float tolerance).
"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
os.chdir(PROJECT_ROOT)

from src.dashboard.utils import db
import pandas as pd
import numpy as np

BASELINE_PATH = os.path.join(PROJECT_ROOT, "output", "day43_baseline.json")

def load_baseline():
    with open(BASELINE_PATH) as f:
        return json.load(f)

def get_optimized_result(scenario, filters=None, sort_by="composite_quality_score",
                         sector_filter=None, name_sort_asc=False):
    """Get result from optimized function for a given scenario."""
    df = db.get_screener_results(filters, sort_by=sort_by)
    if sector_filter:
        df = df[df["sector"] == sector_filter]
    if name_sort_asc:
        df = df.sort_values("company_name", ascending=True)
    return df

def compare_item_dicts(baseline_items, optimized_items, scenario_name, float_tolerance=0.01):
    """Compare two lists of item dicts. Return list of discrepancies."""
    discrepancies = []

    # Compare counts
    if len(baseline_items) != len(optimized_items):
        discrepancies.append(f"  COUNT MISMATCH: baseline={len(baseline_items)}, optimized={len(optimized_items)}")

    # Compare company IDs in order
    baseline_ids = [i.get("company_id") for i in baseline_items]
    optimized_ids = [i.get("company_id") for i in optimized_items]

    if baseline_ids != optimized_ids:
        # Check if same set but different order
        if set(baseline_ids) == set(optimized_ids):
            discrepancies.append(f"  ORDER DIFFERENCE (same set, different order)")
            # Find first difference
            for i, (b, o) in enumerate(zip(baseline_ids, optimized_ids)):
                if b != o:
                    discrepancies.append(f"    First order diff at index {i}: baseline={b}, optimized={o}")
                    break
        else:
            discrepancies.append(f"  COMPANY ID SET MISMATCH")
            baseline_set = set(baseline_ids)
            optimized_set = set(optimized_ids)
            discrepancies.append(f"    In baseline not optimized: {baseline_set - optimized_set}")
            discrepancies.append(f"    In optimized not baseline: {optimized_set - baseline_set}")

    # Compare numeric fields per company
    baseline_by_id = {i.get("company_id"): i for i in baseline_items}
    optimized_by_id = {i.get("company_id"): i for i in optimized_items}

    for cid in baseline_by_id:
        if cid not in optimized_by_id:
            continue
        b = baseline_by_id[cid]
        o = optimized_by_id[cid]
        for key in b:
            if key not in o:
                continue
            b_val = b[key]
            o_val = o[key]
            if b_val is None and o_val is None:
                continue
            if b_val is None or o_val is None:
                discrepancies.append(f"    NULL mismatch for {cid}.{key}: baseline={b_val}, optimized={o_val}")
                continue
            try:
                b_float = float(b_val)
                o_float = float(o_val)
                if not np.isclose(b_float, o_float, rtol=float_tolerance, atol=float_tolerance):
                    discrepancies.append(f"    VALUE mismatch for {cid}.{key}: baseline={b_float}, optimized={o_float}")
            except (ValueError, TypeError):
                if str(b_val) != str(o_val):
                    discrepancies.append(f"    STRING mismatch for {cid}.{key}: baseline={b_val}, optimized={o_val}")

    return discrepancies

def main():
    print("=" * 70)
    print("CORRECTNESS VERIFICATION — Baseline vs Optimized")
    print("=" * 70)

    baseline = load_baseline()
    all_pass = True

    # Test 1: Unfiltered screener
    print("\n--- Test 1: Unfiltered screener ---")
    df_opt = db.get_screener_results(None, sort_by="company_id")
    base_items = baseline["unfiltered"]["items"]
    # Sort baseline by company_id DESC to match optimized sort (ascending=False)
    base_items = sorted(base_items, key=lambda x: x.get("company_id") or "", reverse=True)
    opt_items = [dict(row) for _, row in df_opt.iterrows()]
    # Normalize
    for item in opt_items:
        for k, v in item.items():
            if pd.isna(v):
                item[k] = None
            elif hasattr(v, 'item'):
                item[k] = v.item()
    discrepancies = compare_item_dicts(base_items, opt_items, "unfiltered")
    if discrepancies:
        all_pass = False
        for d in discrepancies:
            print(f"  FAIL: {d}")
    else:
        print(f"  PASS: {len(opt_items)} companies match baseline within tolerance")

    # Test 2: min_roe=15
    print("\n--- Test 2: min_roe=15 ---")
    df_opt2 = db.get_screener_results({"ROE": {"min": 15}}, sort_by="company_id")
    base_items2 = baseline["min_roe_15"]["items"]
    # Sort baseline by company_id DESC to match optimized sort (ascending=False)
    base_items2 = sorted(base_items2, key=lambda x: x.get("company_id") or "", reverse=True)
    opt_items2 = [dict(row) for _, row in df_opt2.iterrows()]
    for item in opt_items2:
        for k, v in item.items():
            if pd.isna(v):
                item[k] = None
            elif hasattr(v, 'item'):
                item[k] = v.item()
    discrepancies2 = compare_item_dicts(base_items2, opt_items2, "min_roe_15")
    if discrepancies2:
        all_pass = False
        for d in discrepancies2:
            print(f"  FAIL: {d}")
    else:
        print(f"  PASS: {len(opt_items2)} companies match baseline within tolerance")

    # Test 3: roe_15_30
    print("\n--- Test 3: min_roe=15 + max_roe=30 ---")
    df_opt3 = db.get_screener_results({"ROE": {"min": 15, "max": 30}}, sort_by="company_id")
    base_items3 = baseline["roe_15_30"]["items"]
    # Sort baseline by company_id DESC to match optimized sort (ascending=False)
    base_items3 = sorted(base_items3, key=lambda x: x.get("company_id") or "", reverse=True)
    opt_items3 = [dict(row) for _, row in df_opt3.iterrows()]
    for item in opt_items3:
        for k, v in item.items():
            if pd.isna(v):
                item[k] = None
            elif hasattr(v, 'item'):
                item[k] = v.item()
    discrepancies3 = compare_item_dicts(base_items3, opt_items3, "roe_15_30")
    if discrepancies3:
        all_pass = False
        for d in discrepancies3:
            print(f"  FAIL: {d}")
    else:
        print(f"  PASS: {len(opt_items3)} companies match baseline within tolerance")

    # Test 4: Sort by composite_quality_score desc (default API sort)
    print("\n--- Test 4: Sort by composite_quality_score desc ---")
    df_opt4 = db.get_screener_results(None, sort_by="composite_quality_score")
    # Baseline items were already captured in composite_quality_score desc order
    base_sorted = baseline["unfiltered"]["items"]
    opt_sorted = [dict(row) for _, row in df_opt4.iterrows()]
    for item in opt_sorted:
        for k, v in item.items():
            if pd.isna(v):
                item[k] = None
            elif hasattr(v, 'item'):
                item[k] = v.item()
    discrepancies4 = compare_item_dicts(base_sorted, opt_sorted, "composite_sort")
    if discrepancies4:
        all_pass = False
        for d in discrepancies4:
            print(f"  FAIL: {d}")
    else:
        print(f"  PASS: Sort order and values match baseline within tolerance")

    # Test 5: Verify composite scores are computed
    print("\n--- Test 5: Verify composite scores present ---")
    df_opt5 = db.get_screener_results(None, sort_by="company_id")
    if "composite_quality_score" not in df_opt5.columns:
        all_pass = False
        print("  FAIL: composite_quality_score column missing")
    elif "sector_relative_score" not in df_opt5.columns:
        all_pass = False
        print("  FAIL: sector_relative_score column missing")
    else:
        # Check first 3 composite scores
        top3 = df_opt5.nlargest(3, "composite_quality_score")
        for _, row in top3.iterrows():
            score = row["composite_quality_score"]
            print(f"    {row['company_id']}: {score:.2f}")
        print(f"  PASS: composite_quality_score and sector_relative_score present")

    # Summary
    print("\n" + "=" * 70)
    if all_pass:
        print("ALL CORRECTNESS TESTS PASSED")
    else:
        print("SOME CORRECTNESS TESTS FAILED — REVIEW ABOVE")
    print("=" * 70)

    # Now time the cached version
    print("\n--- Performance: Cached call timing ---")
    import time
    t0 = time.perf_counter()
    df1 = db.get_screener_results(None, sort_by="composite_quality_score")
    t1 = time.perf_counter()
    print(f"  First call (from cache): {(t1-t0)*1000:.2f} ms, {len(df1)} rows")

    t0 = time.perf_counter()
    df2 = db.get_screener_results({"ROE": {"min": 15}}, sort_by="composite_quality_score")
    t1 = time.perf_counter()
    print(f"  Filtered call (from cache): {(t1-t0)*1000:.2f} ms, {len(df2)} rows")


if __name__ == "__main__":
    main()
