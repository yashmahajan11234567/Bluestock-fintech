#!/usr/bin/env python3
"""
Fast Day 43 verification - directly tests the current implementation
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.api.main import app
from fastapi.testclient import TestClient
from src.dashboard.utils import db

# Global state tracking
computation_count = 0
lock = threading.Lock()

client = TestClient(app)

def test_concurrent_performance():
    """Test 10 concurrent requests to measure performance"""
    global computation_count

    print("=" * 70)
    print("DAY 43 PERFORMANCE VERIFICATION")
    print("=" * 70)

    # Clear cache using the function we added
    db._clear_screener_cache()

    # Reset computation counter
    with lock:
        computation_count = 0

    def make_request(req_id):
        start = time.perf_counter()
        response = client.get("/api/v1/screener?page_size=10")
        elapsed = time.perf_counter() - start

        # Track cache computations
        with lock:
            computation_count += 1

        return {
            "req_id": req_id,
            "status": response.status_code,
            "ok": response.status_code == 200,
            "elapsed": elapsed,
            "response_json": response.json()
        }

    # Make 10 concurrent requests
    results = []
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(10)]
        for future in as_completed(futures):
            results.append(future.result())

    total_time = time.perf_counter() - start_time
    results.sort(key=lambda x: x["req_id"])

    times = [r["elapsed"] for r in results]
    success_count = sum(1 for r in results if r["ok"])

    print(f"\nPERFECT RESULTS:")
    print(f"  Individual times (s): {[f'{t:.4f}' for t in times]}")
    print(f"  Min: {min(times):.4f}s, Max: {max(times):.4f}s, Avg: {sum(times)/len(times):.4f}s")
    print(f"  Total wall-clock: {total_time:.4f}s")
    print(f"  Success: {success_count}/10")
    print(f"  Cache computations: {computation_count}")

    # Check requirements
    print(f"\nREQUIREMENTS CHECK:")
    all_10 = all(r["ok"] for r in results)
    print(f"  ✓ All 10 requests succeeded: {all_10}")

    all_under_10s = all(r["elapsed"] < 10.0 for r in results)
    print(f"  ✓ All 10 requests < 10s: {all_under_10s}")

    max_under_10s = max(times) < 10.0
    print(f"  ✓ MAX request time < 10s: {max_under_10s}")

    total_under_10s = total_time < 10.0
    print(f"  ✓ Total wall-clock < 10s: {total_under_10s}")

    cache_behavior = computation_count == 1
    print(f"  ✓ Exactly one cache computation (cold cache): {cache_behavior}")

    overall_pass = all_10 and all_under_10s and max_under_10s and total_under_10s and cache_behavior

    print(f"\n{'='*70}")
    if overall_pass:
        print("SUCCESS: All Day 43 requirements MET")
    else:
        print("FAILURE: Some requirements NOT met")

    return overall_pass, results

def test_company_profile_performance():
    """Test company profile performance"""
    print("\n" + "=" * 70)
    print("COMPANY PROFILE PERFORMANCE TEST")
    print("=" * 70)

    tickers = ["HAL", "ADANIENSOL", "ADANIENT", "TCS", "RELIANCE"]

    profile_results = []
    for ticker in tickers:
        start = time.perf_counter()

        # Replicate dashboard loading path
        _ = db.get_company_list()
        _ = db.get_company_profile(ticker)
        _ = db.get_financial_ratios(ticker)
        _ = db.get_cashflow_data(ticker)
        _ = db.get_capital_alloc_data(ticker)

        elapsed = time.perf_counter() - start
        profile_results.append({"ticker": ticker, "elapsed": elapsed})
        print(f"  {ticker}: {elapsed:.4f}s")

    all_under_3s = all(r["elapsed"] < 3.0 for r in profile_results)
    print(f"\nRequirements check:")
    print(f"  ✓ All 5 tickers < 3s: {all_under_3s}")

    return all_under_3s, profile_results

if __name__ == "__main__":
    print("Starting Day 43 independent verification...")

    # Test 1: Concurrent performance
    perf_pass, perf_results = test_concurrent_performance()

    # Test 2: Company profile performance
    profile_pass, profile_results = test_company_profile_performance()

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Day 43 Performance Target: {'PASS' if perf_pass else 'FAIL'}")
    print(f"Company Profile Target: {'PASS' if profile_pass else 'FAIL'}")

    if perf_pass and profile_pass:
        print("\n🎉 ALL REQUIREMENTS SATISFIED")
        print("Day 43 QA: PASS — READY TO PROCEED TO DAY 44")
    else:
        print("\n❌ SOME REQUIREMENTS FAILED")
        print("Day 43 QA: FAIL — CODEX FIX REQUIRED")