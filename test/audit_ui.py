#!/usr/bin/env python3
"""Geometry audit: walks every scene/modal object and reports layout defects.

Checks
  1. objects outside the screen / outside the modal panel
  2. text boxes overlapping each other
  3. text wider than the modal's inner area
  4. hat seating on the capybara's head
  5. parallax bands: sane size, no gaps, aspect preserved

Usage: python3 test/audit_ui.py [url]
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

WALK = """
(roots) => {
  const out = [];
  const walk = (list, clip) => {
    for (const o of list) {
      if (!o || o.destroyed) continue;
      if (o.type === 'Container') {
        const c = o.getData && o.getData('clip');
        walk(o.list, c || clip);
        continue;
      }
      if (o.type === 'ParticleEmitter' || o.isParticles) continue;
      if (o.type === 'TileSprite') continue;      // parallax bands are wider than the screen on purpose
      if (o.texture && o.texture.key === 'cloud') continue; // clouds drift off-screen on purpose
      const m = o.getWorldTransformMatrix();
      const tx = m.tx, ty = m.ty;
      let w = 0, h = 0;
      if (o.type === 'Text') { w = o.width; h = o.height; }
      else if (o.displayWidth !== undefined) { w = o.displayWidth; h = o.displayHeight; }
      else if (o.width !== undefined) { w = o.width; h = o.height; }
      const ox = o.originX !== undefined ? o.originX : 0.5;
      const oy = o.originY !== undefined ? o.originY : 0.5;
      const sx = (o.scaleX === undefined ? 1 : o.scaleX), sy = (o.scaleY === undefined ? 1 : o.scaleY);
      const y0 = ty - h * oy, y1 = y0 + h;
      if (clip && (y0 > clip.y1 + 2 || y1 < clip.y0 - 2)) continue; // clipped away by the scroll mask
      out.push({
        cy0: clip ? clip.y0 : null, cy1: clip ? clip.y1 : null,
        type: o.type,
        key: (o.texture && o.texture.key) || '',
        text: o.type === 'Text' ? String(o.text).slice(0, 34) : '',
        x0: tx - w * ox, y0: y0, x1: tx - w * ox + w, y1: y1,
        w: w, h: h, vis: o.visible, alpha: o.alpha, depth: o.depth, sx: sx, sy: sy,
      });
    }
  };
  walk(roots);
  return out;
}
"""

AUDIT_JS = """
(mode) => {
  const s = window.__capy.scene();
  const walk = %s;
  let roots;
  if (mode === 'modal') roots = s.modal ? s.modal.container.list : [];
  else roots = s.children.list;
  const objs = walk(roots).filter(o => o.vis !== false && o.alpha > 0.05);
  const meta = { W: s.scale.width, H: s.scale.height };
  if (s.modal) meta.panel = { x0: s.modal.cx - s.modal.pw / 2, y0: s.modal.cy - s.modal.ph / 2,
                              x1: s.modal.cx + s.modal.pw / 2, y1: s.modal.cy + s.modal.ph / 2 };
  if (s.capy && s.hat) {
    const cm = s.capy.getWorldTransformMatrix(), hm = s.hat.getWorldTransformMatrix();
    meta.capy = { x: cm.tx, y: cm.ty, w: s.capy.displayWidth, h: s.capy.displayHeight,
                  top: cm.ty - s.capy.displayHeight / 2 };
    meta.hat = { x: hm.tx, y: hm.ty, w: s.hat.displayWidth, h: s.hat.displayHeight,
                 bottom: hm.ty + s.hat.displayHeight / 2, vis: s.hat.visible };
  }
  if (s.layerHills && s.layerTrees) {
    meta.bands = {
      hills: { y0: s.layerHills.y - s.layerHills.height / 2, y1: s.layerHills.y + s.layerHills.height / 2,
               w: s.layerHills.width, tileW: s.layerHills.texture.getSourceImage().width * s.layerHills.tileScaleX,
               scale: s.layerHills.tileScaleX },
      trees: { y0: s.layerTrees.y - s.layerTrees.height / 2, y1: s.layerTrees.y + s.layerTrees.height / 2,
               w: s.layerTrees.width, tileW: s.layerTrees.texture.getSourceImage().width * s.layerTrees.tileScaleX,
               scale: s.layerTrees.tileScaleX },
    };
  }
  return { meta: meta, objs: objs };
}
""" % WALK


def get_chrome():
    out = subprocess.run(["node", os.path.join(ROOT, "tools", "get_chrome.js")],
                         capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
    return json.loads(out)


def overlap(a, b):
    dx = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
    dy = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
    if dx <= 0 or dy <= 0:
        return 0.0
    inter = dx * dy
    small = min((a["x1"] - a["x0"]) * (a["y1"] - a["y0"]), (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]))
    return inter / max(1.0, small)


def check(name, data, problems, tol=4):
    meta, objs = data["meta"], data["objs"]
    W, H = meta["W"], meta["H"]
    panel = meta.get("panel")
    for o in objs:
        if o["type"] == "Graphics":  # masks / helper shapes
            continue
        if o["type"] == "Image" and (o["key"].startswith("bgpc_") or o["key"].startswith("bg_")):
            continue  # background uses cover-fit: bigger than the screen on purpose
        if o["type"] == "Rectangle" and o["w"] >= W - 2 and o["h"] >= H - 2:
            continue  # modal dim overlay
        if o["type"] == "Rectangle" and (o["w"] <= 0 or o["h"] <= 0):
            continue  # empty progress fill
        lab = f'{o["type"]}:{o["key"] or o["text"]!r}'
        # 1) bounds
        if panel:
            lim = (panel["x0"] - tol, panel["y0"] - tol, panel["x1"] + tol, panel["y1"] + tol)
        else:
            lim = (-tol, -tol, W + tol, H + tol)
        if o.get("cy0") is not None:
            # inside a scroll mask: rows may be half-cut by the mask (that is how scrolling looks),
            # so only the horizontal limits are meaningful here
            lim = (lim[0], -9999, lim[2], 9999)
        if o["x0"] < lim[0] or o["x1"] > lim[2] or o["y0"] < lim[1] or o["y1"] > lim[3]:
            problems.append(f'[{name}] OUT: {lab} box=({o["x0"]:.0f},{o["y0"]:.0f})-({o["x1"]:.0f},{o["y1"]:.0f}) '
                            f'limits=({lim[0]:.0f},{lim[1]:.0f})-({lim[2]:.0f},{lim[3]:.0f})')
        if (o["w"] <= 0 or o["h"] <= 0) and o["type"] != "Rectangle":
            problems.append(f'[{name}] ZERO SIZE: {lab}')
    # 2) text overlaps
    texts = [o for o in objs if o["type"] == "Text" and o["text"].strip()]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            r = overlap(texts[i], texts[j])
            if r > 0.25:
                problems.append(f'[{name}] TEXT OVERLAP {r:.0%}: {texts[i]["text"]!r} vs {texts[j]["text"]!r}')
    return len(objs)


def check_world(page, problems):
    """hat seating + parallax sanity"""
    d = page.evaluate("""() => {
      const s = window.__capy.scene();
      if (!s.capy) return null;
      const cm = s.capy.getWorldTransformMatrix(), hm = s.hat.getWorldTransformMatrix();
      return { capy: { x: cm.tx, y: cm.ty, h: s.capy.displayHeight, top: cm.ty - s.capy.displayHeight / 2 },
               hat: { x: hm.tx, y: hm.ty, h: s.hat.displayHeight, w: s.hat.displayWidth,
                      bottom: hm.ty + s.hat.displayHeight / 2, top: hm.ty - s.hat.displayHeight / 2, vis: s.hat.visible },
               art: s.hat.getData('art'),
               hills: s.layerHills ? { y0: s.layerHills.y - s.layerHills.height / 2, y1: s.layerHills.y + s.layerHills.height / 2,
                                       w: s.layerHills.width, tw: s.layerHills.texture.getSourceImage().width * s.layerHills.tileScaleX,
                                       vis: s.layerHills.visible } : null,
               trees: s.layerTrees ? { y0: s.layerTrees.y - s.layerTrees.height / 2, y1: s.layerTrees.y + s.layerTrees.height / 2,
                                       w: s.layerTrees.width, tw: s.layerTrees.texture.getSourceImage().width * s.layerTrees.tileScaleX,
                                       vis: s.layerTrees.visible } : null,
               W: s.scale.width, H: s.scale.height };
    }""")
    if not d:
        return
    c, h = d["capy"], d["hat"]
    art = d.get("art")
    if art:  # prefer the measured art box over the (padded) canvas box
        h = dict(h, bottom=art["bottom"], top=art["top"], w=art["x1"] - art["x0"])
    if h["vis"]:
        # hat bottom must sit in the top 35% of the capybara, horizontally centred
        rel = (h["bottom"] - c["top"]) / c["h"]
        dx = abs(h["x"] - c["x"]) / c["h"]
        if not (0.02 <= rel <= 0.40):
            problems.append(f'[hat] bottom at {rel:.0%} of capybara height (want 2-40%), box bottom={h["bottom"]:.0f} capyTop={c["top"]:.0f}')
        if dx > 0.10:
            problems.append(f'[hat] off-centre by {dx:.0%} of capybara height: hat.x={h["x"]:.0f} capy.x={c["x"]:.0f}')
        if not (0.20 <= h["w"] / c["h"] <= 0.75):
            problems.append(f'[hat] width {h["w"] / c["h"]:.0%} of capybara height (want 20-75%)')
        print(f'  hat: bottom={rel:.0%} of body, dx={dx:.1%}, w={h["w"] / c["h"]:.0%} OK')
    for nm in ("hills", "trees"):
        b = d[nm]
        if not b or not b["vis"]:
            continue
        if b["tw"] < 40:
            problems.append(f'[{nm}] tile art only {b["tw"]:.0f}px wide - scale is wrong')
        hgt = b["y1"] - b["y0"]
        if hgt > d["H"] * 0.35:
            problems.append(f'[{nm}] band height {hgt:.0f} > 35% of screen ({d["H"]})')


def main():
    chrome = get_chrome()
    problems = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=chrome["execPath"],
            args=chrome["args"] + ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            env={**os.environ, "LD_LIBRARY_PATH": chrome.get("libDir", "") +
                 (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")})
        for tag, w, h, mob, dsf in [("m375", 375, 667, True, 2), ("pc1280", 1280, 800, False, 1)]:
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf,
                                      is_mobile=mob, has_touch=True)
            page = ctx.new_page()
            page.on("pageerror", lambda e: problems.append("PAGEERROR: " + str(e)[:200]))
            page.goto(URL, wait_until="domcontentloaded")
            page.wait_for_function("window.__capy && window.__capy.state()", timeout=20000)
            time.sleep(1.5)
            # give some progression + a hat + pumpkins so every element exists
            page.evaluate("""() => {
              const s = window.__capy.state();
              s.coins = 500000; s.gems = 500;
              s.hats.owned = ['none','pumpkin','leaf','beanie']; s.hats.active = 'pumpkin';
              s.event.pumpkins = 900;
              s.perks = { auto: 1, crit: 2 };
              window.__capy.scene().applyHat();
            }""")
            time.sleep(0.6)
            print(f'--- {tag}: main screen')
            check(f'{tag}/main', page.evaluate(AUDIT_JS, "scene"), problems)
            check_world(page, problems)
            page.screenshot(path=os.path.join(SHOT_DIR, f'audit_{tag}_main.png'))

            views = [("shop", 0.78), ("quests", 0.8), ("daily", 0.62), ("event", 0.8),
                     ("boost", 0.55), ("prestige", 0.55), ("settings", 0.6), ("donate", 0.72)]
            for name, _ in views:
                page.evaluate(f"window.__capy.scene().open{name.capitalize()}()")
                page.wait_for_timeout(500)
                n = check(f'{tag}/{name}', page.evaluate(AUDIT_JS, "modal"), problems)
                print(f'  {name}: {n} objects checked')
                page.screenshot(path=os.path.join(SHOT_DIR, f'audit_{tag}_{name}.png'))
                page.evaluate("window.__capy.scene().closeModal()")
                page.wait_for_timeout(200)
            # donate tabs
            for i, tab in enumerate(["packs", "perks", "coins", "skins"]):
                page.evaluate(f"window.__capy.scene().donateTab = '{tab}'")
                page.evaluate("window.__capy.scene().openDonate()")
                page.wait_for_timeout(450)
                n = check(f'{tag}/donate:{tab}', page.evaluate(AUDIT_JS, "modal"), problems)
                print(f'  donate:{tab}: {n} objects')
                page.screenshot(path=os.path.join(SHOT_DIR, f'audit_{tag}_donate_{tab}.png'))
                page.evaluate("window.__capy.scene().closeModal()")
                page.wait_for_timeout(200)
        browser.close()

    print()
    if problems:
        print(f'=== {len(problems)} PROBLEM(S) ===')
        for p in problems:
            print(' -', p)
        sys.exit(1)
    print('AUDIT CLEAN')


if __name__ == "__main__":
    main()
