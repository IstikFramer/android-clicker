#!/usr/bin/env python3
"""Diagnostic shots: daily / quests / boost-timer / main (clipping check)."""
import json, os, subprocess, sys, time
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(ROOT, "test", "screenshots")
W, H = 375, 667

out = subprocess.run(["node", os.path.join(ROOT, "tools", "get_chrome.js")],
                     capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
chrome = json.loads(out)

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path=chrome["execPath"],
        args=chrome["args"] + ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        env={**os.environ, "LD_LIBRARY_PATH": chrome.get("libDir", "") +
             (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")})
    ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=2,
                              is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.on("pageerror", lambda e: print("PAGEERROR:", str(e)[:300]))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
    time.sleep(1.0)
    page.screenshot(path=os.path.join(SHOT_DIR, "diag_main.png"))
    page.evaluate("window.__capy.scene().openDaily()")
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT_DIR, "diag_daily.png"))
    # clip: daily cells closeup (top part of modal)
    page.screenshot(path=os.path.join(SHOT_DIR, "diag_daily_top.png"),
                    clip={"x": 0, "y": 150, "width": W, "height": 220})
    page.evaluate("window.__capy.scene().closeModal()")
    page.evaluate("window.__capy.scene().openQuests()")
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT_DIR, "diag_quests.png"))
    page.evaluate("window.__capy.scene().closeModal()")
    # boost timer: fake active boost, shot bottom dock area
    page.evaluate("window.__capy.state().boostUntil = Date.now() + 115000; window.__capy.scene().updateHud()")
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT_DIR, "diag_boost.png"),
                    clip={"x": 0, "y": H - 160, "width": W, "height": 160})
    page.screenshot(path=os.path.join(SHOT_DIR, "diag_main_boost.png"))
    browser.close()
print("DIAG SHOTS DONE")
