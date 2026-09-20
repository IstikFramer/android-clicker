#!/usr/bin/env python3
"""Extended UI test: all modals, RU/TR languages, evolution, prestige, IAP demo, daily claim.

Usage: python3 test/test_modals.py [url]
Screenshots -> test/screenshots/ext_*.png
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
W, H = 375, 667


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


def modal_geom(frac):
    pw = min(W - 24, 460)
    ph = min(H - 100, H * frac)
    cx, cy = W / 2, H / 2
    return {"pw": pw, "ph": ph, "cx": cx, "cy": cy,
            "top": cy - ph / 2 + 60, "left": cx - pw / 2 + 14, "right": cx + pw / 2 - 14}


def new_page(pw, chrome, query=""):
    browser = pw.chromium.launch(
        executable_path=chrome["execPath"],
        args=chrome["args"] + ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        env={**os.environ, "LD_LIBRARY_PATH": chrome.get("libDir", "") +
             (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")},
    )
    ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=2,
                              is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.on("pageerror", lambda e: print("PAGEERROR:", str(e)[:300]))
    page.goto(URL + query, wait_until="domcontentloaded")
    page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
    time.sleep(1.0)
    return browser, page


def st(page):
    return page.evaluate("window.__capy.state()")


def open_modal(page, name):
    page.evaluate(f"window.__capy.scene().{name}()")
    page.wait_for_timeout(450)


def close_modal(page):
    page.evaluate("window.__capy.scene().closeModal()")
    page.wait_for_timeout(250)


def main():
    chrome = get_chrome()
    with sync_playwright() as pw:
        # ---------- EN: all modals ----------
        browser, page = new_page(pw, chrome)
        # quests (do 50 clicks first so quest #0 completes)
        for i in range(50):
            page.mouse.click(W / 2, H * 0.36, delay=5)
        page.wait_for_timeout(300)
        open_modal(page, "openQuests")
        shot(page, "ext_01_quests_en.png")
        # claim quest #0 (clicks quest, target 50 -> done)
        g = modal_geom(0.8)
        q = st(page)["quests"][0]
        assert q["done"], f"quest0 should be done: {q}"
        page.mouse.click(g["right"] - 55, g["top"] + 20 + 8)
        page.wait_for_timeout(400)
        q2 = st(page)["quests"][0]
        assert not q2["claimed"] and q2["progress"] == 0, "quest should rotate after claim"
        print("[en] quest claim OK, new quest:", q2["type"], q2["target"])
        close_modal(page)

        open_modal(page, "openDaily")
        shot(page, "ext_02_daily_en.png")
        # claim daily: button at (cx, top+226), frac 0.62
        g = modal_geom(0.62)
        c0 = st(page)["coins"]
        page.mouse.click(g["cx"], g["top"] + 226)
        page.wait_for_timeout(400)
        s = st(page)
        assert s["coins"] > c0 and s["dailyStreak"] == 1, "daily claim failed"
        print(f"[en] daily claim OK: +{s['coins']-c0:.0f} coins, streak={s['dailyStreak']}")

        open_modal(page, "openSettings")
        shot(page, "ext_03_settings_en.png")
        close_modal(page)

        # evolution: grant 150k -> stage idx 2 (Cool)
        page.evaluate("window.__capy.scene().earn(150000)")
        page.wait_for_timeout(700)
        tex = page.evaluate("window.__capy.scene().capy.texture.key")
        assert tex == "capy_evo3", f"expected capy_evo3, got {tex}"
        shot(page, "ext_04_evolution.png")
        print("[en] evolution OK:", tex)

        # prestige: grant 2M -> 1 star pending
        page.evaluate("window.__capy.scene().earn(2000000)")
        page.wait_for_timeout(300)
        open_modal(page, "openPrestige")
        shot(page, "ext_05_prestige_en.png")
        g = modal_geom(0.55)
        page.mouse.click(g["cx"], g["top"] + 150)
        page.wait_for_timeout(400)
        s = st(page)
        assert s["stars"] == 1 and s["coins"] == 0 and s["prestiges"] == 1, f"prestige failed: {s['stars']},{s['coins']}"
        print("[en] prestige OK: stars=1")
        shot(page, "ext_06_after_prestige.png")
        browser.close()

        # ---------- RU: main + shop ----------
        browser, page = new_page(pw, chrome)
        page.evaluate("window.__capy.state().settings.lang='ru'")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
        page.wait_for_timeout(800)
        for i in range(12):
            page.mouse.click(W / 2, H * 0.36, delay=5)
        page.wait_for_timeout(300)
        shot(page, "ext_07_main_ru.png")
        open_modal(page, "openShop")
        shot(page, "ext_08_shop_ru.png")
        close_modal(page)
        open_modal(page, "openQuests")
        shot(page, "ext_09_quests_ru.png")
        close_modal(page)
        browser.close()

        # ---------- TR: main (glyph check) ----------
        browser, page = new_page(pw, chrome)
        page.evaluate("window.__capy.state().settings.lang='tr'")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
        page.wait_for_timeout(800)
        open_modal(page, "openDaily")
        shot(page, "ext_10_daily_tr.png")
        close_modal(page)
        browser.close()

        # ---------- Donate (gems) + exchange + boost ----------
        browser, page = new_page(pw, chrome, query="?demo_pay=1")
        open_modal(page, "openDonate")
        shot(page, "ext_11_donate.png")
        g = modal_geom(0.72)
        page.mouse.click(g["right"] - 52, g["top"] + 52 + 29)  # small pack DEMO buy
        page.wait_for_timeout(400)
        s = st(page)
        assert s["gems"] == 10, f"IAP demo buy failed: gems={s['gems']}"
        print("[iap] demo purchase OK: +10 gems")
        shot(page, "ext_12_donate_bought.png")
        # coin packs tab (index 2): spend 5 gems -> +1000 coins
        tw = (g["right"] - g["left"] - 12) / 4
        page.mouse.click(g["left"] + 6 + tw * 2 + tw / 2, g["top"] + 12)
        page.wait_for_timeout(400)
        c0 = st(page)["coins"]
        page.mouse.click(g["right"] - 52, g["top"] + 80)
        page.wait_for_timeout(400)
        s = st(page)
        assert s["gems"] == 5 and s["coins"] >= c0 + 1000, f"coin pack failed: {s['gems']},{s['coins']}"
        print("[iap] coin pack OK: 5 gems -> +1000 coins")
        close_modal(page)
        # boost modal: ad button grants x2
        open_modal(page, "openBoost")
        shot(page, "ext_13_boost.png")
        g = modal_geom(0.55)
        page.mouse.click(g["cx"], g["top"] + 6 + 108)
        page.wait_for_timeout(400)
        assert st(page)["boostUntil"] > 0, "ad boost failed"
        print("[boost] ad boost OK")
        # gem boost: 15 gems -> +5min
        page.evaluate("window.__capy.state().gems = 50")
        b0 = st(page)["boostUntil"]
        page.mouse.click(g["cx"], g["top"] + 6 + 108 + 54)
        page.wait_for_timeout(400)
        s = st(page)
        assert s["gems"] == 35 and s["boostUntil"] > b0, f"gem boost failed: {s['gems']}"
        print("[boost] gem boost OK: 50 -> 35 gems")
        shot(page, "ext_14_boost_active.png")
        close_modal(page)
        browser.close()

    print("EXTENDED SUITE PASSED")


if __name__ == "__main__":
    main()
