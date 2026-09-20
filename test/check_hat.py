#!/usr/bin/env python3
"""Numeric check: is the hat actually seated on the capybara's head?

For every evolution x hat combination it verifies
  * the brim rests on the head (not floating above, not over the eyes)
  * the hat does not poke into the HUD
  * the hat is centred on the head
  * the hat is not wider/taller than the head allows

Usage: python3 test/check_hat.py [url]
"""
import json
import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 375, 667
HUD_BOTTOM = 96  # px: hat art must stay below the top bar

# measured head geometry (must match src/config.js HEADS)
HEADS = [
    {"top": 5, "cx": 63, "w": 75},
    {"top": 5, "cx": 63.5, "w": 56},
    {"top": 3, "cx": 62.5, "w": 48},
    {"top": 14, "cx": 63, "w": 45},
    {"top": 20, "cx": 63, "w": 46},
]


def get_chrome():
    out = subprocess.run(["node", os.path.join(ROOT, "tools", "get_chrome.js")],
                         capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
    return json.loads(out)


def main():
    chrome = get_chrome()
    bad = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=chrome["execPath"],
            args=chrome["args"] + ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            env={**os.environ, "LD_LIBRARY_PATH": chrome.get("libDir", "") +
                 (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")})
        page = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=2,
                                   is_mobile=True, has_touch=True).new_page()
        page.on("pageerror", lambda e: bad.append("PAGEERROR " + str(e)[:200]))
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
        time.sleep(1.5)
        page.evaluate("window.__capy.state().hats.owned = ['none','pumpkin','leaf','beanie']")
        print(f'{"evo":<5}{"hat":<9}{"brim/head":>10}{"top px":>8}{"w/head":>8}{"dx px":>7}  verdict')
        for i, head in enumerate(HEADS):
            for hat in ("pumpkin", "leaf", "beanie"):
                d = page.evaluate("""(a) => {
                  const s = window.__capy.scene();
                  s.state_ = null;
                  window.__capy.state().hats.active = a.hat;
                  s.evoIdx = a.i;
                  s.capy.setTexture('capy_evo' + (a.i + 1));
                  s.placeHat();
                  const art = s.hat.getData('art');
                  const m = s.capy.getWorldTransformMatrix();
                  return { art: art, capyX: m.tx, capyY: m.ty, capyH: s.capy.displayHeight, vis: s.hat.visible };
                }""", {"i": i, "hat": hat})
                art = d["art"]
                scale = d["capyH"] / 128
                capy_top = d["capyY"] - d["capyH"] / 2
                head_top_px = capy_top + head["top"] * scale
                head_w_px = head["w"] * scale
                head_cx_px = d["capyX"] + (head["cx"] - 64) * scale
                brim = (art["bottom"] - head_top_px) / head_w_px   # want ~0.26
                w_ratio = (art["x1"] - art["x0"]) / head_w_px        # want ~0.92 (or less when clamped)
                dx = abs((art["x0"] + art["x1"]) / 2 - head_cx_px)
                issues = []
                if not d["vis"]:
                    issues.append("invisible")
                if not (0.10 <= brim <= 0.42):
                    issues.append(f'brim {brim:.2f} off head (want 0.10-0.42)')
                if art["top"] < HUD_BOTTOM + 6:
                    issues.append(f'top {art["top"]:.0f}px pokes into HUD')
                if dx > 4:
                    issues.append(f'off-centre {dx:.1f}px')
                if not (0.55 <= w_ratio <= 1.02):
                    issues.append(f'width {w_ratio:.2f} of head (want 0.55-1.02)')
                verdict = "OK" if not issues else "; ".join(issues)
                if issues:
                    bad.append(f'evo{i+1}/{hat}: {verdict}')
                print(f'evo{i+1:<2}{hat:<9}{brim:>10.2f}{art["top"]:>8.0f}{w_ratio:>8.2f}{dx:>7.1f}  {verdict}')
        browser.close()
    print()
    if bad:
        print(f'=== {len(bad)} HAT PROBLEM(S) ===')
        for b in bad:
            print(" -", b)
        sys.exit(1)
    print("HAT FIT OK")


if __name__ == "__main__":
    main()
