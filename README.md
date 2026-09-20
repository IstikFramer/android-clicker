# 🦫 Capybara Clicker

Pixel-art idle clicker for **Yandex Games** (HTML5, portrait, mobile-first).
Tap the capybara, earn coins, buy upgrades, evolve through 5 stages, prestige for permanent stars.

Built with **Phaser 3 + Vite**. Languages: **RU / EN / TR**. Monetization: **Rewarded + Interstitial ads, IAP (Yandex Payments), leaderboard**.

## Features (spec coverage)

| Spec item | Status |
|---|---|
| Phaser 3, ES6+, Vite build, ZIP with `index.html` at root < 15 MB | ✅ `capybara-clicker-yandex.zip` ~0.6 MB |
| Pixel sprites, local `assets/` (no external URLs) | ✅ |
| Clicker core: coins, per-click, coins/sec | ✅ |
| 7 upgrades, cost `base × 1.15^owned` | ✅ |
| 5 evolution stages | ✅ |
| Offline income (50% cps, 8h cap) | ✅ |
| Prestige (stars, +25% each) | ✅ |
| Daily streak rewards (7-day cycle) | ✅ |
| Quests (rotating) + 14 achievements | ✅ |
| YaGames SDK v2: init before boot, rewarded (player-initiated x2/2min), interstitial (130s cooldown, never at start), leaderboard `totalCoins`, cloud saves + localStorage fallback, i18n from SDK | ✅ all wrapped in try/catch |
| Portrait, 320–428px wide, ≥48px touch targets, Press Start 2P (latin/cyrillic/latin-ext + ₽/ı fixes), no scroll/zoom | ✅ |
| Procedural WebAudio SFX + chiptune (no audio files, license-clean) | ✅ |
| Playwright autotests (50 clicks, 2 buys, balance, modals, i18n, evo, prestige, IAP) + screenshots | ✅ `test/` |

## Quickstart

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # -> dist/
```

Preview the IAP section locally (mock purchases, no SDK needed):

```
http://localhost:5173/?demo_pay=1   # open SHOP and scroll down
```

## Tests

```bash
# one-time: headless Chromium comes from tools/chromehelper (@sparticuz/chromium),
# system libs (libnss3) are extracted from its bundled al2023 archive automatically
pip install playwright
cd tools/chromehelper && npm install && cd ../..

python3 test/test_game.py            # core flow, 375x667 + 414x896
python3 test/test_modals.py          # modals, RU/TR, evolution, prestige, IAP demo
python3 test/test_game.py http://localhost:8901   # test any build (e.g. dist/ via http.server)
```

Screenshots land in `test/screenshots/`.

## Yandex dashboard setup (IAP)

Create 3 **consumable** products with these exact IDs (prices are suggestions):

| Product ID | Coins granted | Suggested price |
|---|---|---|
| `coins_small` | 10 000 | 29 ₽ |
| `coins_big` | 100 000 | 199 ₽ |
| `coins_mega` | 1 000 000 | 999 ₽ |

The game reads live prices via `payments.getCatalog()`; the GEMS section appears only when Payments API is available. Also create a leaderboard named **`totalCoins`**.

## Project layout

```
src/            game code (main.js, config/balance, i18n, audio synth, yandex SDK wrapper, saves)
public/assets/  final game assets (sprites, ui, particles, backgrounds, fonts)
tools/          chroma-key + procedural asset scripts, headless-chrome helper
test/           playwright suites + screenshots
dist/           production build (git-ignored; ship the .zip instead)
```

## Deploy

1. `npm run build`
2. Zip the **contents** of `dist/` (index.html at archive root) — or use the prebuilt `capybara-clicker-yandex.zip`
3. Upload to Yandex Games draft, set orientation **Portrait**, test on device
