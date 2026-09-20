#!/usr/bin/env python3
"""Feature tests: autumn event (pass + tasks), perks (auto-clicker), hats,
rewarded-ad cooldown, prestige keeps boost.

Usage: python3 test/test_features.py [url]
Screenshots -> test/screenshots/ft_*.png
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
        # ---------------- AUTUMN EVENT ----------------
        browser, page = new_page(pw, chrome)
        s = st(page)
        assert s["event"], "event state missing"
        print("[event] id:", s["event"]["id"])
        # floating event button (x = cx + CW/2 - 36, y = H*0.62)
        page.mouse.click(W / 2 + W / 2 - 36, H * 0.62)
        page.wait_for_timeout(500)
        shot(page, "ft_01_event.png")
        assert page.evaluate("!!window.__capy.scene().modal"), "event modal did not open"
        close_modal(page)

        # grant pumpkins, claim free tier 1 (need 20) + buy premium
        page.evaluate("window.__capy.state().gems = 300; window.__capy.state().event.pumpkins = 150")
        open_modal(page, "openEvent")
        g = modal_geom(0.85)
        page.mouse.click(g["right"] - 62, g["top"] + 62)  # buy premium (100 gems), below the banner
        page.wait_for_timeout(450)
        s = st(page)
        assert s["event"]["premium"] and s["gems"] == 200, f"premium pass failed: {s['gems']}"
        print("[event] premium pass OK: gems 300 -> 200")
        shot(page, "ft_02_event_premium.png")
        # free tier 0 button: x = left + 118, y = top + (30+40+20+3*40+10+20) + 19
        tier0_y = g["top"] + 52 + 40 + 20 + 3 * 40 + 10 + 20 + 19  # banner(52) + pass + tasks + tiers
        c0 = st(page)["coins"]
        page.mouse.click(g["left"] + 118, tier0_y)
        page.wait_for_timeout(450)
        s = st(page)
        assert 0 in s["event"]["claimedFree"], f"free tier claim failed: {s['event']['claimedFree']}"
        assert s["coins"] > c0, "tier 1 should grant coins"
        print(f"[event] free tier claim OK: +{s['coins'] - c0:.0f} coins")
        # premium tier 0 (coin reward, scaled to cps)
        c1 = s["coins"]
        page.mouse.click(g["left"] + 236, tier0_y)
        page.wait_for_timeout(450)
        s = st(page)
        assert 0 in s["event"]["claimedPrem"] and s["coins"] > c1, f"prem tier failed: {s['coins']}"
        print(f"[event] premium tier claim OK: +{s['coins'] - c1:.0f} coins")
        shot(page, "ft_03_event_claimed.png")
        close_modal(page)

        # daily task: complete the clicks task and claim it
        page.evaluate("""() => {
          const ev = window.__capy.state().event;
          const t = ev.tasks.find(x => x.id === 'clicks');
          t.progress = t.target;
        }""")
        open_modal(page, "openEvent")
        task_y = g["top"] + 52 + 40 + 20 + 40 + 17  # task row 2 (clicks) center
        p0 = st(page)["event"]["pumpkins"]
        page.mouse.click(g["right"] - 44, task_y)
        page.wait_for_timeout(450)
        s = st(page)
        assert s["event"]["pumpkins"] > p0, f"task claim failed: {p0} -> {s['event']['pumpkins']}"
        print(f"[event] daily task OK: +{s['event']['pumpkins'] - p0} pumpkins")
        shot(page, "ft_04_event_task.png")
        close_modal(page)
        browser.close()

        # ---------------- PERKS + AUTO-CLICKER ----------------
        browser, page = new_page(pw, chrome)
        page.evaluate("window.__capy.state().gems = 500")
        open_modal(page, "openDonate")
        g = modal_geom(0.72)
        tw = (g["right"] - g["left"] - 12) / 4
        # perks tab (index 1)
        page.mouse.click(g["left"] + 6 + tw * 1 + tw / 2, g["top"] + 12)
        page.wait_for_timeout(450)
        shot(page, "ft_05_perks.png")
        page.mouse.click(g["right"] - 52, g["top"] + 80)  # buy auto-clicker lvl1 (60)
        page.wait_for_timeout(450)
        s = st(page)
        assert s["perks"].get("auto") == 1, f"perk buy failed: {s['perks']}"
        assert s["gems"] == 440, f"gems after perk: {s['gems']}"
        print("[perks] auto-clicker bought: gems 500 -> 440")
        close_modal(page)
        # auto-clicker must generate clicks + coins on its own
        c0, k0 = st(page)["coins"], st(page)["totalClicks"]
        page.wait_for_timeout(2500)
        s = st(page)
        assert s["totalClicks"] >= k0 + 2, f"auto-clicker idle: {k0} -> {s['totalClicks']}"
        assert s["coins"] > c0, "auto-clicker earned nothing"
        print(f"[perks] auto-clicker works: +{s['totalClicks'] - k0} clicks, +{s['coins'] - c0:.0f} coins")
        browser.close()

        # ---------------- COSMETICS (hats) ----------------
        browser, page = new_page(pw, chrome)
        page.evaluate("window.__capy.state().gems = 500")
        open_modal(page, "openDonate")
        g = modal_geom(0.72)
        tw = (g["right"] - g["left"] - 12) / 4
        page.mouse.click(g["left"] + 6 + tw * 3 + tw / 2, g["top"] + 12)  # cosmetics tab
        page.wait_for_timeout(450)
        shot(page, "ft_06_cosmetics.png")
        page.mouse.click(g["right"] - 52, g["top"] + 80 + 64)  # row 1 = pumpkin hat (60)
        page.wait_for_timeout(450)
        s = st(page)
        assert "pumpkin" in s["hats"]["owned"], f"hat buy failed: {s['hats']}"
        assert s["hats"]["active"] == "pumpkin", f"hat not equipped: {s['hats']}"
        assert s["gems"] == 440, f"gems after hat: {s['gems']}"
        visible = page.evaluate("window.__capy.scene().hat.visible && window.__capy.scene().hat.texture.key")
        assert visible == "hat_pumpkin", f"hat sprite not shown: {visible}"
        print("[cosmetics] pumpkin hat bought + equipped:", visible)
        close_modal(page)
        shot(page, "ft_07_hat_on.png")
        browser.close()

        # ---------------- AD COOLDOWN + PRESTIGE KEEPS BOOST ----------------
        browser, page = new_page(pw, chrome)
        open_modal(page, "openBoost")
        g = modal_geom(0.55)
        page.mouse.click(g["cx"], g["top"] + 114)  # rewarded ad -> x2 for 2 min
        page.wait_for_timeout(500)
        s = st(page)
        assert s["boostUntil"] > 0 and s["lastAdAt"] > 0, f"ad boost failed: {s['boostUntil']},{s['lastAdAt']}"
        print("[ads] first rewarded ad OK, cooldown started")
        close_modal(page)
        # second ad attempt must be blocked by the 5-minute cooldown
        open_modal(page, "openBoost")
        shot(page, "ft_08_ad_cooldown.png")
        b0 = st(page)["boostUntil"]
        page.mouse.click(g["cx"], g["top"] + 114)
        page.wait_for_timeout(500)
        s = st(page)
        assert s["boostUntil"] == b0, f"ad cooldown bypassed: {b0} -> {s['boostUntil']}"
        print("[ads] cooldown holds: boost unchanged")
        close_modal(page)
        # prestige must NOT reset the boost (nor gems / perks)
        page.evaluate("""() => {
          const s = window.__capy.state();
          s.gems = 77; s.perks = { auto: 1 };
          s.boostUntil = Date.now() + 120000;
          window.__capy.scene().doPrestige(1);
        }""")
        page.wait_for_timeout(400)
        s = st(page)
        assert s["boostUntil"] > 0 and s["stars"] == 1, f"prestige failed: {s['stars']}"
        assert s["gems"] == 77 and s["perks"]["auto"] == 1, f"prestige wiped gems/perks: {s['gems']},{s['perks']}"
        print("[prestige] keeps boost, gems and perks")
        shot(page, "ft_09_after_prestige.png")
        browser.close()

    print("FEATURE SUITE PASSED")


if __name__ == "__main__":
    main()
