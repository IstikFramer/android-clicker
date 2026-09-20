#!/usr/bin/env python3
"""Automated Playwright test for Capybara Clicker (mobile mode).

Flow: open game -> 50 clicks -> buy 2 upgrades -> verify balance -> screenshots.
Usage: python3 test/test_game.py [url]
"""
import json
import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(ROOT, "test", "screenshots")
os.makedirs(SHOT_DIR, exist_ok=True)


def get_chrome():
    out = subprocess.run(
        ["node", os.path.join(ROOT, "tools", "get_chrome.js")],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[-1]
    return json.loads(out)


def shot(page, name):
    p = os.path.join(SHOT_DIR, name)
    page.screenshot(path=p)
    print("SHOT:", p)


def run_viewport(pw, chrome, width, height, tag, mobile=True):
    lib_dir = chrome.get("libDir", "")
    ld_path = lib_dir + (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")
    browser = pw.chromium.launch(
        executable_path=chrome["execPath"],
        args=chrome["args"] + ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        env={**os.environ, "LD_LIBRARY_PATH": ld_path} if lib_dir else None,
    )
    ctx_args = dict(viewport={"width": width, "height": height},
                    device_scale_factor=2 if mobile else 1,
                    is_mobile=mobile, has_touch=True)
    if mobile:
        ctx_args["user_agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    ctx = browser.new_context(**ctx_args)
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
    time.sleep(1.2)  # boot scene + assets
    shot(page, f"{tag}_01_initial.png")

    st = page.evaluate("window.__capy.state()")
    assert st is not None, "state not available"

    # ---- 50 clicks on the capybara ----
    cx, cy = width / 2, height * 0.36
    for i in range(50):
        page.mouse.click(cx + (i % 5) * 4 - 8, cy + (i % 3) * 4 - 4, delay=10)
    page.wait_for_timeout(400)
    st = page.evaluate("window.__capy.state()")
    print(f"[{tag}] after 50 clicks: totalClicks={st['totalClicks']} coins={st['coins']}")
    assert st["totalClicks"] >= 50, "clicks not registered"
    assert st["coins"] >= 50, "coins not earned"
    shot(page, f"{tag}_02_after_clicks.png")

    # ---- open shop ----
    n = 6
    colW = min(480, width * 0.6) if width > 560 else width
    bw = min(56, (colW - 16) / n - 6)
    shop_x = width / 2 + (0 - (n - 1) / 2) * (bw + 8)
    shop_y = height - 32
    page.mouse.click(shop_x, shop_y)
    page.wait_for_timeout(500)
    shot(page, f"{tag}_03_shop.png")

    # ---- buy orange (row 0) and grass (row 1) ----
    pw_ = min(width - 24, 460)
    ph_ = min(height - 100, height * 0.78)
    top = height / 2 - ph_ / 2 + 60
    right = width / 2 + pw_ / 2 - 14
    buy_x = right - 52
    coins_before = page.evaluate("window.__capy.state().coins")
    page.mouse.click(buy_x, top + 14 + 48)          # orange costs 15
    page.wait_for_timeout(600)
    page.mouse.click(buy_x, top + 14 + 48 + 62)     # grass costs 25
    page.wait_for_timeout(600)
    st = page.evaluate("window.__capy.state()")
    print(f"[{tag}] after buys: upgrades={st['upgrades']} coins={st['coins']} (before {coins_before})")
    assert st["upgrades"].get("orange") == 1, "orange not bought"
    assert st["upgrades"].get("grass") == 1, "grass not bought"
    # balance check: spent 15+25
    assert abs(st["coins"] - (coins_before - 40)) < 8, "balance mismatch after purchases"
    shot(page, f"{tag}_04_after_buys.png")

    # cps tick check
    c1 = page.evaluate("window.__capy.state().coins")
    page.wait_for_timeout(2100)
    c2 = page.evaluate("window.__capy.state().coins")
    print(f"[{tag}] cps tick: {c1} -> {c2}")
    assert c2 > c1, "cps income not ticking"

    # close shop (X)
    close_x = width / 2 + pw_ / 2 - 26
    close_y = height / 2 - ph_ / 2 + 24
    page.mouse.click(close_x, close_y)
    page.wait_for_timeout(400)
    shot(page, f"{tag}_05_final.png")

    browser.close()
    print(f"[{tag}] ALL CHECKS PASSED")


def main():
    chrome = get_chrome()
    with sync_playwright() as pw:
        run_viewport(pw, chrome, 375, 667, "m375")
        run_viewport(pw, chrome, 414, 896, "m414")
        run_viewport(pw, chrome, 1280, 800, "pc1280", mobile=False)
    print("TEST SUITE PASSED")


if __name__ == "__main__":
    main()
