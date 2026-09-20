#!/usr/bin/env python3
"""Pixel-level verification of the things that are easy to get wrong visually.

  1. no chroma-key green left inside the parallax bands
  2. the hat really sits on the head: diff a shot with / without the hat and
     check where the changed pixels land relative to the capybara
  3. parallax drift is smooth (no jitter): sample tilePositionX over time
  4. the daily chest is rendered big enough

Usage: python3 test/verify_look.py [url]
"""
import json
import os
import subprocess
import sys
import time

from PIL import Image
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = os.path.join(ROOT, "test", "screenshots")
W, H = 375, 667


def get_chrome():
    out = subprocess.run(["node", os.path.join(ROOT, "tools", "get_chrome.js")],
                         capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
    return json.loads(out)


def screen_green(path, y0, y1):
    """count pure chroma-green pixels (the background art's grass is a muted green, so this is safe)"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    bad = 0
    lowest = None
    for y in range(max(0, int(y0)), min(h, int(y1))):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if g > 200 and r < 90 and b < 90:
                bad += 1
                if lowest is None or y < lowest:
                    lowest = y
    return bad, lowest


def main():
    chrome = get_chrome()
    problems = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=chrome["execPath"],
            args=chrome["args"] + ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            env={**os.environ, "LD_LIBRARY_PATH": chrome.get("libDir", "") +
                 (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")})
        page = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                                   is_mobile=True, has_touch=True).new_page()
        page.on("pageerror", lambda e: problems.append("PAGEERROR " + str(e)[:200]))
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
        time.sleep(2.0)
        page.evaluate("window.__capy.state().hats.owned = ['none','pumpkin','leaf','beanie']; "
                      "window.__capy.state().hats.active = 'none'; window.__capy.scene().applyHat();")
        time.sleep(0.4)

        # ---------- 1. parallax bands: no chroma green ----------
        bands = page.evaluate("""() => { const s = window.__capy.scene();
          return { hills: [s.layerHills.y - s.layerHills.height/2, s.layerHills.y + s.layerHills.height/2],
                   trees: [s.layerTrees.y - s.layerTrees.height/2, s.layerTrees.y + s.layerTrees.height/2] }; }""")
        p = os.path.join(SHOT, "verify_bands.png")
        page.screenshot(path=p)
        for nm in ("hills", "trees"):
            bad, low = screen_green(p, bands[nm][0], bands[nm][1])
            print(f'  {nm} band y={bands[nm][0]:.0f}..{bands[nm][1]:.0f}: chroma-green pixels = {bad}')
            if bad > 30:
                problems.append(f'{nm} band still shows {bad} chroma-green pixels (first at y={low})')

        # ---------- 3. parallax smoothness ----------
        samples = []
        for _ in range(8):
            samples.append(page.evaluate("window.__capy.scene().layerTrees.tilePositionX"))
            time.sleep(0.12)
        deltas = [round(samples[i + 1] - samples[i], 3) for i in range(len(samples) - 1)]
        spread = max(deltas) - min(deltas)
        print(f'  tree tilePositionX deltas: {deltas} (spread {spread:.2f})')
        if spread > 6:
            problems.append(f'parallax jitter: per-tick deltas vary by {spread:.1f}px')
        if any(d == 0 for d in deltas):
            problems.append('parallax stalled: zero delta between ticks')

        # ---------- 2. hat seating, measured from real pixels ----------
        # freeze every animation first, otherwise falling leaves / drifting clouds pollute the diff
        page.evaluate("""() => { const s = window.__capy.scene();
          s.time.paused = true;
          if (s.weather) { s.weather.destroy(); s.weather = null; }
          s.tweens.pauseAll();
          s.layerHills.tilePositionX = 0; s.layerTrees.tilePositionX = 0;
          s.clouds.forEach((c, i) => c.setPosition(-500 - i * 200, -500));
        }""")
        time.sleep(0.5)
        base = os.path.join(SHOT, "verify_nohot.png")
        page.screenshot(path=base)
        page.evaluate("window.__capy.state().hats.active = 'pumpkin'; window.__capy.scene().applyHat();")
        time.sleep(0.4)
        hatted = os.path.join(SHOT, "verify_hat.png")
        page.screenshot(path=hatted)
        capy = page.evaluate("""() => { const s = window.__capy.scene();
          const m = s.capy.getWorldTransformMatrix();
          return { x: m.tx, y: m.ty, h: s.capy.displayHeight, top: m.ty - s.capy.displayHeight/2 }; }""")
        a = Image.open(base).convert("RGB").load()
        b = Image.open(hatted).convert("RGB").load()
        im = Image.open(base)
        minx, miny, maxx, maxy = 10**9, 10**9, -1, -1
        for y in range(0, H):
            for x in range(0, W, 1):
                pa, pb = a[x, y], b[x, y]
                if abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2]) > 45:
                    minx = min(minx, x); maxx = max(maxx, x)
                    miny = min(miny, y); maxy = max(maxy, y)
        if maxx < 0:
            problems.append("hat produced no visible pixels")
        else:
            capy_top = capy["top"]
            capy_h = capy["h"]
            print(f'  hat pixels: x {minx}..{maxx} (w {maxx-minx}), y {miny}..{maxy} (h {maxy-miny}); '
                  f'capybara top={capy_top:.0f} h={capy_h:.0f}')
            gap = miny  # distance from the top of the screen
            if miny < 100:
                problems.append(f'hat top at y={miny} overlaps the HUD (bottom 96)')
            if maxy < capy_top + 0.05 * capy_h:
                problems.append(f'hat bottom y={maxy} floats above the capybara (top={capy_top:.0f})')
            if maxy > capy_top + 0.45 * capy_h:
                problems.append(f'hat bottom y={maxy} covers the face (top={capy_top:.0f}, h={capy_h:.0f})')
            if abs((minx + maxx) / 2 - capy["x"]) > 0.10 * capy_h:
                problems.append('hat is not horizontally centred on the capybara')
            print(f'  hat bottom sits {(maxy - capy_top) / capy_h:.0%} down the body, '
                  f'centre offset {abs((minx + maxx) / 2 - capy["x"]):.1f}px')

        # ---------- 4. chest size ----------
        page.evaluate("window.__capy.scene().openDaily()")
        page.wait_for_timeout(500)
        chest = page.evaluate("""() => { const s = window.__capy.scene();
          let best = null;
          const walk = (l) => { for (const o of l) { if (o.type === 'Container') { walk(o.list); continue; }
            if (o.texture && String(o.texture.key).startsWith('chest_')) best = { key: o.texture.key, w: o.displayWidth, h: o.displayHeight }; } };
          if (s.modal) walk(s.modal.container.list);
          return best; }""")
        page.screenshot(path=os.path.join(SHOT, "verify_daily.png"))
        print(f'  daily chest: {chest}')
        if not chest or chest["w"] < 100:
            problems.append(f'daily chest too small: {chest}')
        browser.close()

    print()
    if problems:
        print(f'=== {len(problems)} PROBLEM(S) ===')
        for p in problems:
            print(' -', p)
        sys.exit(1)
    print("LOOK VERIFIED")


if __name__ == "__main__":
    main()
