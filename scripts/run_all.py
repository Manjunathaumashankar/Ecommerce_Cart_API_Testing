"""
Comprehensive Test Orchestrator for E-Commerce Shopping Cart API.
1. Starts the Flask server in background.
2. Polls health check endpoint until ready.
3. Runs Python unittests.
4. Executes SoapUI testrunner CLI (if available) with JUnit XML report generation.
5. Shuts down the background Flask server.
"""

import os
import sys
import time
import subprocess
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:5000"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOAPUI_PROJECT = os.path.join(PROJECT_ROOT, "soapui", "Ecommerce-Cart-SoapUI-Project.xml")
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports", "soapui")


def find_soapui_runner():
    candidates = [
        r"C:\Program Files\SmartBear\SoapUI-5.10.0\bin\testrunner.bat",
        r"C:\Program Files\SmartBear\SoapUI-5.7.2\bin\testrunner.bat",
        os.path.join(os.environ.get("SOAPUI_HOME", ""), "bin", "testrunner.bat"),
        os.path.join(os.environ.get("SOAPUI_HOME", ""), "bin", "testrunner.sh"),
        "testrunner.bat",
        "testrunner.sh"
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def wait_for_server(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.urlopen(f"{url}/", timeout=2)
            if req.status == 200:
                return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


def main():
    print("=" * 65)
    print("  E-Commerce Shopping Cart API - Unified Test Runner")
    print("=" * 65)

    os.makedirs(REPORT_DIR, exist_ok=True)

    # 1. Start Flask app
    print("\n[1/3] Starting Flask Application...")
    flask_env = os.environ.copy()
    server_process = subprocess.Popen(
        [sys.executable, os.path.join(PROJECT_ROOT, "app.py")],
        cwd=PROJECT_ROOT,
        env=flask_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        if not wait_for_server(API_URL, timeout=10):
            print("[WARN] Server did not respond to local socket probe (may require bypass sandbox or server is starting).")
        else:
            print(f"[OK] Flask API is running at {API_URL}")

        # 2. Run Python Unit / Integration Tests
        print("\n[2/3] Running Python API Test Suite...")
        py_result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=PROJECT_ROOT
        )
        if py_result.returncode != 0:
            print("[FAIL] Python tests failed!")
        else:
            print("[PASS] All Python API tests passed!")

        # 3. Run SoapUI TestRunner
        print("\n[3/3] Checking for SoapUI CLI TestRunner...")
        soapui_runner = find_soapui_runner()

        if soapui_runner:
            print(f"[INFO] Found SoapUI runner: {soapui_runner}")
            print(f"[INFO] Executing SoapUI project: {SOAPUI_PROJECT}")
            cmd = [
                soapui_runner,
                "-r",
                "-a",
                "-j",
                f"-f{REPORT_DIR}",
                f"-PbaseUrl={API_URL}",
                SOAPUI_PROJECT
            ]
            soapui_res = subprocess.run(cmd, cwd=PROJECT_ROOT)
            if soapui_res.returncode == 0:
                print(f"[PASS] SoapUI TestSuites completed successfully!")
                print(f"[INFO] Test reports exported to: {REPORT_DIR}")
            else:
                print(f"[FAIL] SoapUI TestRunner exited with code {soapui_res.returncode}")
        else:
            print("[SKIP] SoapUI testrunner CLI not found on PATH or standard directory.")
            print("       You can run tests via SoapUI GUI or install SoapUI Open Source.")

    finally:
        print("\n[CLEANUP] Stopping background Flask server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("[OK] Server stopped.")

    print("\n" + "=" * 65)
    print("  Execution Finished")
    print("=" * 65)


if __name__ == "__main__":
    main()
