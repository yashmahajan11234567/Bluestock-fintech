"""
Day 43 End-to-End Integration Test Script
=========================================

Starts FastAPI on port 8000 and Streamlit on port 8501, verifies both
run simultaneously, checks health/docs endpoints, and verifies the
dashboard can load data.

Only terminates processes that this script starts.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(str(PROJECT_ROOT))

# Use the venv Python
VENV_PYTHON = Path(__file__).resolve().parents[2] / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = "python"

# Track processes we start so we can clean them up
_started_processes: list[subprocess.Popen] = []


def is_port_in_use(port: int) -> tuple[bool, str]:
    """Check if a port is in use. Returns (in_use, owning_process_info)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(("127.0.0.1", port))
            if result == 0:
                # Port is in use — try to identify via /proc or ps
                try:
                    proc = subprocess.run(
                        ["ps", "aux"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    for line in proc.stdout.split("\n"):
                        if str(port) in line and ("uvicorn" in line or "streamlit" in line):
                            return True, line.strip()
                except Exception:
                    pass
                return True, "unknown process"
            return False, ""
    except Exception:
        return False, ""


def start_fastapi(port: int) -> subprocess.Popen | None:
    """Start FastAPI via uvicorn on the given port. Returns the process or None if port is taken."""
    in_use, owner = is_port_in_use(port)
    if in_use:
        print(f"  Port {port} already in use by: {owner}")
        print(f"  NOT killing existing process (safety rule).")
        return None

    print(f"  Starting FastAPI on port {port}...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "api.main:app",
         "--host", "127.0.0.1", "--port", str(port),
         "--app-dir", str(PROJECT_ROOT / "src")],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    _started_processes.append(proc)
    # Wait for server to be ready
    for _ in range(30):
        try:
            r = requests.get(f"http://127.0.0.1:{port}/api/v1/health", timeout=2)
            if r.status_code == 200:
                print(f"  FastAPI ready on port {port}")
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    print(f"  WARNING: FastAPI did not become ready on port {port}")
    return proc


def start_streamlit(port: int) -> subprocess.Popen | None:
    """Start Streamlit on the given port."""
    in_use, owner = is_port_in_use(port)
    if in_use:
        print(f"  Port {port} already in use by: {owner}")
        print(f"  NOT killing existing process (safety rule).")
        return None

    print(f"  Starting Streamlit on port {port}...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "streamlit", "run",
         str(PROJECT_ROOT / "src" / "dashboard" / "app.py"),
         "--server.port", str(port),
         "--server.headless", "true",
         "--server.enableCORS", "false",
         "--server.enableXsrfProtection", "false"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    _started_processes.append(proc)
    # Wait for server to be ready
    for _ in range(30):
        try:
            r = requests.get(f"http://127.0.0.1:{port}", timeout=2, allow_redirects=True)
            if r.status_code == 200:
                print(f"  Streamlit ready on port {port}")
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    print(f"  WARNING: Streamlit did not become ready on port {port}")
    return proc


def stop_process(proc: subprocess.Popen):
    """Stop a process that was started by this script."""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def main():
    print("=" * 70)
    print("DAY 43 — END-TO-END INTEGRATION TEST")
    print("=" * 70)

    results = {
        "fastapi": {"started": False, "port": 8000, "ready": False, "health": False, "docs": False},
        "streamlit": {"started": False, "port": 8501, "ready": False, "data_load": False},
        "port_conflict": False,
    }

    # --- Check port availability ---
    print("\n--- Port Availability Check ---")
    fa_in_use, fa_owner = is_port_in_use(8000)
    st_in_use, st_owner = is_port_in_use(8501)
    print(f"  Port 8000: {'IN USE by ' + fa_owner if fa_in_use else 'FREE'}")
    print(f"  Port 8501: {'IN USE by ' + st_owner if st_in_use else 'FREE'}")

    # Use port 8099 as test port if 8000 is occupied by an unknown/legacy process
    if fa_in_use:
        print("  Port 8000 already occupied — using port 8099 for fresh FastAPI instance")
        results["port_conflict"] = True
        fa_port = 8099
    else:
        fa_port = 8000

    if st_in_use and not st_owner:
        print("  Port 8501 occupied by unknown process — will use temporary port")
        results["port_conflict"] = True
        st_port = 8503
    else:
        st_port = 8501

    # --- Start FastAPI ---
    print("\n--- Starting FastAPI ---")
    try:
        fa_proc = start_fastapi(fa_port)
        if fa_proc is not None:
            results["fastapi"]["started"] = True
            results["fastapi"]["port"] = fa_port
        else:
            results["fastapi"]["started"] = True  # Already running
            results["fastapi"]["ready"] = True  # Assume it's the app
    except Exception as e:
        print(f"  ERROR starting FastAPI: {e}")
        fa_proc = None

    # --- Test FastAPI endpoints ---
    print("\n--- Testing FastAPI Endpoints ---")
    try:
        r = requests.get(f"http://127.0.0.1:{fa_port}/api/v1/health", timeout=5)
        results["fastapi"]["ready"] = True
        results["fastapi"]["health"] = r.status_code == 200
        print(f"  GET /api/v1/health: {r.status_code} — {'PASS' if r.status_code == 200 else 'FAIL'}")
    except Exception as e:
        print(f"  ERROR health check: {e}")

    try:
        r = requests.get(f"http://127.0.0.1:{fa_port}/docs", timeout=5)
        results["fastapi"]["docs"] = r.status_code == 200
        print(f"  GET /docs: {r.status_code} — {'PASS' if r.status_code == 200 else 'FAIL'}")
    except Exception as e:
        print(f"  ERROR /docs check: {e}")

    try:
        r = requests.get(f"http://127.0.0.1:{fa_port}/api/v1/screener?page_size=5", timeout=5)
        print(f"  GET /api/v1/screener: {r.status_code} — {'PASS' if r.status_code == 200 else 'FAIL'}")
    except Exception as e:
        print(f"  ERROR screener check: {e}")

    # --- Start Streamlit ---
    print("\n--- Starting Streamlit ---")
    try:
        st_proc = start_streamlit(st_port)
        if st_proc is not None:
            results["streamlit"]["started"] = True
            results["streamlit"]["port"] = st_port
    except Exception as e:
        print(f"  ERROR starting Streamlit: {e}")
        st_proc = None

    # --- Test Streamlit ---
    print("\n--- Testing Streamlit ---")
    if results["streamlit"]["started"] or st_in_use:
        try:
            r = requests.get(f"http://127.0.0.1:{st_port}", timeout=5, allow_redirects=True)
            results["streamlit"]["ready"] = r.status_code == 200
            print(f"  GET / (root): {r.status_code} — {'PASS' if r.status_code == 200 else 'FAIL'}")
        except Exception as e:
            print(f"  ERROR Streamlit root check: {e}")

    # --- Verify dashboard can load data ---
    print("\n--- Verifying Dashboard Data Loading ---")
    try:
        # The db module uses relative path db/nifty100.db
        # We need to import via the dashboard utils path
        import sys as _sys
        src_path = str(PROJECT_ROOT / "src")
        if src_path not in _sys.path:
            _sys.path.insert(0, src_path)
        # Also add project root so 'dashboard' module is importable
        proj_path = str(PROJECT_ROOT)
        if proj_path not in _sys.path:
            _sys.path.insert(0, proj_path)
        from dashboard.utils.db import get_company_profile, get_screener_results
        profile = get_company_profile("TCS")
        screener = get_screener_results()
        results["streamlit"]["data_load"] = profile is not None and not screener.empty
        print(f"  get_company_profile('TCS'): {'OK' if profile else 'FAIL'}")
        print(f"  get_screener_results(): {len(screener)} rows — {'OK' if not screener.empty else 'FAIL'}")
    except Exception as e:
        print(f"  ERROR dashboard data check: {e}")
        import traceback
        traceback.print_exc()

    # --- Verify FASTAPI on port 8501 can serve dashboard data ---
    print("\n--- Verifying Dashboard/API Integration ---")
    try:
        r = requests.get(f"http://127.0.0.1:{fa_port}/api/v1/companies/TCS", timeout=5)
        print(f"  GET /api/v1/companies/TCS: {r.status_code} — {'PASS' if r.status_code == 200 else 'FAIL'}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  FastAPI port: {results['fastapi']['port']}")
    print(f"  FastAPI started: {results['fastapi']['started']}")
    print(f"  FastAPI ready: {results['fastapi']['ready']}")
    print(f"  Health endpoint: {'PASS' if results['fastapi']['health'] else 'FAIL'}")
    print(f"  /docs: {'PASS' if results['fastapi']['docs'] else 'FAIL'}")
    print(f"  Streamlit port: {results['streamlit']['port']}")
    print(f"  Streamlit started: {results['streamlit']['started']}")
    print(f"  Streamlit ready: {results['streamlit']['ready']}")
    print(f"  Dashboard data load: {'PASS' if results['streamlit']['data_load'] else 'FAIL'}")
    print(f"  Port conflict: {results['port_conflict']}")

    # --- Cleanup ---
    print("\n--- Cleanup ---")
    for proc in _started_processes:
        stop_process(proc)
        print(f"  Stopped process (PID {proc.pid})")

    # Save results
    import json
    from datetime import datetime
    output = {
        "timestamp": datetime.now().isoformat(),
        "fastapi": results["fastapi"],
        "streamlit": results["streamlit"],
        "port_conflict": results["port_conflict"],
    }
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "day43_e2e_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to: output/day43_e2e_results.json")


if __name__ == "__main__":
    main()
