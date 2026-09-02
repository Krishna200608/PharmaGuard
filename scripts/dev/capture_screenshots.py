"""
Automated High-Resolution Dashboard Screenshot Capture
======================================================
Captures exact 1920x1080 verification screenshots for all 5 tabs in both Light and Dark modes.
Saves to assets/Screenshots/Light/ and assets/Screenshots/Dark/.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
LIGHT_DIR = REPO_ROOT / "assets" / "Screenshots" / "Light"
DARK_DIR = REPO_ROOT / "assets" / "Screenshots" / "Dark"
LIGHT_DIR.mkdir(parents=True, exist_ok=True)
DARK_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8544
URL = f"http://localhost:{PORT}"

TABS = [
    ("Overview", "1_Overview.png"),
    ("Per-Pair Table", "2_Per-Pair Table.png"),
    ("Disagreement Spotlight", "3_Disagreement Spotlight.png"),
    ("Baseline Comparison", "4_Baseline Comparison.png"),
    ("Methodology Probes", "5_Methodology Probes.png"),
    ("OMOP Pilot", "6_OMOP Pilot.png"),
]


def wait_for_server(url: str, timeout: int = 35) -> bool:
    """Poll URL until server responds 200 OK."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def run_capture() -> None:
    print(f"Starting Streamlit dashboard on port {PORT}...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "scripts/dashboard.py",
            f"--server.port={PORT}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        print("Waiting for Streamlit server to initialize...")
        ready = wait_for_server(URL, timeout=40)
        if not ready:
            print("ERROR: Streamlit server did not respond in time!")
            out, err = proc.communicate(timeout=5)
            print("STDOUT:", out.decode("utf-8", errors="ignore"))
            print("STDERR:", err.decode("utf-8", errors="ignore"))
            return

        print("Streamlit server is ready. Launching Playwright Chromium...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(3000)

            for theme, out_dir in [("Light", LIGHT_DIR), ("Dark", DARK_DIR)]:
                print(f"\n--- Switching to {theme} Theme ---")
                theme_radio = page.locator('[role="radio"]').filter(has_text=theme).first
                if theme_radio.count() > 0:
                    theme_radio.click()
                    page.wait_for_timeout(2000)
                else:
                    print(f"Warning: Could not find theme radio for {theme}")

                for tab_name, filename in TABS:
                    print(f"Capturing [{theme}] -> {tab_name} ({filename})...")
                    tab_loc = page.locator('[role="tab"]').filter(has_text=tab_name).first
                    if tab_loc.count() > 0:
                        tab_loc.click()
                        page.wait_for_timeout(2500)
                        page.evaluate("window.scrollTo(0, 0)")
                        page.wait_for_timeout(500)
                        out_path = out_dir / filename
                        page.screenshot(path=str(out_path), full_page=False)
                        print(f"  -> Saved {out_path.name} ({out_path.stat().st_size:,} bytes)")
                    else:
                        print(f"Warning: Could not find tab locator for {tab_name}")

            browser.close()
            print("\nAll screenshots captured successfully!")

    finally:
        print("Terminating Streamlit server process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Done.")


if __name__ == "__main__":
    run_capture()