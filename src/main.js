// ===== CAPYBARA CLICKER — main game (Phaser 3) =====
import Phaser from 'phaser';
import { t, setLanguage, getLanguage, LANGS } from './i18n.js';
import {
  UPGRADES, upgradeCost, EVOLUTIONS, evolutionIndex, pendingStars,
  PRESTIGE_MIN, starMultiplier, dailyReward, BOOST_DURATION, BOOST_MULT, nextPrestigeNeed,
  OFFLINE_RATE, OFFLINE_CAP_SEC, ACHIEVEMENTS, totalUpgrades, makeQuest, IAP_PRODUCTS,
  GEM_BOOST_COST, GEM_BOOST_DURATION, EXCHANGE_GEMS, EXCHANGE_COINS, DAILY_GEMS_DAY7,
  REWARDED_COOLDOWN, PERKS, perkLevel, autoClickRate, offlineBonus, critChance,
  HATS, COIN_PACKS, packCoins, HEADS, HAT_W, HAT_MAX_H, HAT_BRIM,
  EVENT, eventActive, eventDaysLeft, PASS_TIERS, PASS_PREMIUM_COST, passTierReached,
  EVENT_TASKS, dayKey, makeEventTasks,
} from './config.js';
import { SFX, setSound, setMusic, unlockAudio, startMusic } from './audio.js';
import * as Y from './yandex.js';
import { loadState, saveState } from './save.js';

const FONT = '"Press Start 2P", monospace';
let STATE = null;

function fmt(n) {
  n = Math.floor(n);
  if (n < 1000) return String(n);
  const units = ['K', 'M', 'B', 'T'];
  let u = -1; let v = n;
  while (v >= 1000 && u < units.length - 1) { v /= 1000; u++; }
  const s = v >= 100 ? String(Math.floor(v)) : (Math.floor(v * 10) / 10).toString();
  return s + units[u];
}

function fmtTime(sec) {
  sec = Math.max(0, Math.floor(sec));
  const m = Math.floor(sec / 60), s = sec % 60;
  return m + ':' + String(s).padStart(2, '0');
}

// ---------------- derived stats ----------------
function clickPower() {
  const leafMult = Math.pow(2, STATE.upgrades.leaf || 0);
  const base = 1 + (STATE.upgrades.orange || 0);
  return base * leafMult * starMultiplier(STATE.stars) * boostMult();
}
function cpsBase() {
  let v = 0;
  for (const u of UPGRADES) if (u.type === 'cps') v += u.value * (STATE.upgrades[u.id] || 0);
  return v;
}
function boostMult() { return STATE.boostUntil > Date.now() ? BOOST_MULT : 1; }
function cps() { return cpsBase() * starMultiplier(STATE.stars) * boostMult(); }

function pickBg(W, H) {
  const now = new Date();
  const land = W > H;
  const h = now.getHours();
  const tod = (h >= 20 || h < 6) ? 'night' : ((h >= 6 && h < 8) || (h >= 17 && h < 20)) ? 'sunset' : 'day';
  if (eventActive(now.getTime())) return land ? 'bgpc_autumn' : 'bg_autumn_' + tod; // autumn event art
  if (now.getMonth() === 11) return land ? 'bgpc_winter' : 'bg_winter'; // festive December
  const p = land ? 'bgpc_' : 'bg_';
  return p + tod;
}

// ================================================================
class BootScene extends Phaser.Scene {
  constructor() { super('boot'); }
  create() {
    const W = this.scale.width, H = this.scale.height;
    this.add.rectangle(W / 2, H / 2, W, H, 0x4aa0ff);
    const title = this.add.text(W / 2, H * 0.4, t('title'), { fontFamily: FONT, fontSize: '18px', padding: { x: 2, y: 6 }, color: '#ffffff', stroke: '#1a4a8a', strokeThickness: 4, align: 'center' }).setOrigin(0.5);
    const load = this.add.text(W / 2, H * 0.5, t('loading'), { fontFamily: FONT, fontSize: '10px', padding: { x: 2, y: 4 }, color: '#ffffff' }).setOrigin(0.5);
    const bar = this.add.rectangle(W / 2, H * 0.56, 200, 10, 0x1a4a8a);
    const fill = this.add.rectangle(W / 2 - 98, H * 0.56, 4, 6, 0xffd24a).setOrigin(0, 0.5);
    this.load.on('progress', p => { fill.width = Math.max(4, 196 * p); });
    // sprites
    for (let i = 1; i <= 5; i++) this.load.image('capy_evo' + i, `assets/sprites/capy_evo${i}.png?v=3`);
    for (let i = 1; i <= 5; i++) this.load.image('capy_evo' + i + '_b', `assets/sprites/capy_evo${i}_b.png?v=3`);
    for (const u of UPGRADES) this.load.image(u.icon, `assets/ui/${u.icon}.png?v=3`);
    this.load.image('btn_orange', 'assets/ui/btn_orange.png?v=3');
    this.load.image('btn_blue', 'assets/ui/btn_blue.png?v=3');
    this.load.image('btn_green', 'assets/ui/btn_green.png?v=3');
    this.load.image('btn_red', 'assets/ui/btn_red.png?v=3');
    this.load.image('icon_gift', 'assets/ui/icon_gift.png?v=3');
    for (const k of ['coin_gold', 'strip_gold', 'mound', 'cloud', 'burst', 'heart_big', 'crown']) this.load.image(k, `assets/ui/${k}.png?v=1`);
    for (const k of ['icon_boost', 'icon_gem', 'chest_closed', 'chest_open', 'firework', 'star_big', 'icon_medal', 'trophy', 'icon_tv']) this.load.image(k, `assets/ui/${k}.png?v=1`);
    for (const k of ['layer_hills', 'layer_trees', 'pumpkin', 'hat_pumpkin', 'hat_leaf', 'hat_beanie', 'pedestal', 'bar_frame', 'banner']) this.load.image(k, `assets/ui/${k}.png?v=2`);
    for (const k of ['row_plate', 'row_plate_alt', 'cell_plate', 'hud_frame', 'dock_frame', 'btn_close', 'tab_plate', 'banner_small', 'strip_divider', 'pedestal_glow']) this.load.image(k, `assets/ui/${k}.png?v=1`);
    for (const b of ['day', 'sunset', 'night', 'winter']) this.load.image('bg_' + b, `assets/backgrounds/bg_${b}.jpg?v=3`);
    for (const b of ['day', 'sunset', 'night', 'winter']) this.load.image('bgpc_' + b, `assets/backgrounds/bgpc_${b}.jpg?v=1`);
    this.load.image('bgpc_autumn', 'assets/backgrounds/bgpc_autumn.jpg?v=1');
    for (const b of ['day', 'sunset', 'night']) this.load.image('bg_autumn_' + b, `assets/backgrounds/bg_autumn_${b}.jpg?v=1`);
    this.load.image('part_coin', 'assets/particles/part_coin.png?v=3');
    this.load.image('part_spark', 'assets/particles/part_spark.png?v=3');
    this.load.image('part_heart', 'assets/particles/part_heart.png?v=3');
    this.load.image('part_leaf', 'assets/particles/part_leaf.png?v=1');
    this.load.image('part_snow', 'assets/particles/part_snow.png?v=1');
    this.load.image('icon_star', 'assets/particles/part_spark.png?v=3');
    this.load.once('complete', () => {
      this.time.delayedCall(300, () => this.scene.start('game'));
    });
    this.load.start();
  }
}

// ================================================================
class GameScene extends Phaser.Scene {
  constructor() { super('game'); }

  async create() {
    const { state } = await loadState();
    STATE = state;
    STATE.cpsBase = cpsBase();

    // language
    const savedLang = STATE.settings.lang;
    setLanguage(savedLang || Y.getLang(navigator.language || 'ru'));

    setSound(STATE.settings.sound);
    setMusic(STATE.settings.music);

    this.ui = [];           // disposable ui objects
    this.modal = null;
    this.toasts = [];

    // ---- persistent world objects ----
    const W = this.scale.width, H = this.scale.height;
    this.bg = this.add.image(W / 2, H / 2, pickBg(W, H));
    this.layerHills = this.add.tileSprite(W / 2, H * 0.30, W + 120, 90, 'layer_hills').setDepth(1);
    this.layerTrees = this.add.tileSprite(W / 2, H * 0.34, W + 120, 130, 'layer_trees').setDepth(2);
    this.autoT = 0; this.pxOff = 0; this.pxTarget = 0; // parallax state (single source of truth)
    this.clouds = [];
    for (let i = 0; i < 3; i++) this.clouds.push(this.add.image(-200, 100, 'cloud').setAlpha(0.92));
    this.mound = this.add.image(W / 2, H * 0.4, 'mound').setDepth(4);
    this.capy = this.add.image(W / 2, H * 0.38, 'capy_evo1').setDepth(5);
    this.hat = this.add.image(W / 2, H * 0.38, 'hat_pumpkin').setDepth(6).setVisible(false);
    this.capy.setInteractive({ useHandCursor: true });
    this.capy.on('pointerdown', p => this.onCapyClick(p));
    this.combo = 0; this.lastClickT = 0; this.comboTimer = null;
    this.comboTxt = this.add.text(W / 2, H * 0.2, '', { fontFamily: FONT, fontSize: '12px', padding: { x: 2, y: 4 }, color: '#7dff8a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5).setVisible(false).setDepth(10);

    this.emitterCoin = this.add.particles(0, 0, 'part_coin', {
      speed: { min: 80, max: 220 }, angle: { min: 200, max: 340 },
      gravity: 500, lifespan: 700, scale: { start: 1, end: 0.4 },
      emitting: false,
    });
    this.emitterSpark = this.add.particles(0, 0, 'part_spark', {
      speed: { min: 50, max: 260 }, lifespan: 600, scale: { start: 1.4, end: 0 },
      emitting: false,
    });
    this.emitterBurst = this.add.particles(0, 0, 'burst', { speed: { min: 100, max: 300 }, lifespan: 500, scale: { start: 1.2, end: 0 }, emitting: false });
    this.emitterHeart = this.add.particles(0, 0, 'heart_big', { speed: { min: 60, max: 160 }, angle: { min: 230, max: 310 }, gravityY: -200, lifespan: 900, scale: { start: 0.8, end: 0.2 }, emitting: false });
    this.emitterFire = this.add.particles(0, 0, 'firework', { speed: { min: 60, max: 240 }, lifespan: 800, scale: { start: 1, end: 0 }, emitting: false });
    this.emitterStar = this.add.particles(0, 0, 'star_big', { speed: { min: 80, max: 200 }, lifespan: 700, scale: { start: 0.9, end: 0.1 }, emitting: false });
    for (const e of [this.emitterCoin, this.emitterSpark, this.emitterBurst, this.emitterHeart, this.emitterFire, this.emitterStar]) e.setDepth(150);

    // event state
    if (!STATE.event || STATE.event.id !== EVENT.id) {
      STATE.event = { id: EVENT.id, pumpkins: 0, pumpkinsTotal: 0, tierClaimed: 0, premium: false, claimedFree: [], claimedPrem: [], tasks: null, taskDay: '' };
    }
    this.rollEventTasks();
    this.applyHat();

    // quests init
    if (!STATE.quests || STATE.quests.length === 0) {
      STATE.quests = [makeQuest(this.questCtx(), 0), makeQuest(this.questCtx(), 1), makeQuest(this.questCtx(), 2)];
    }

    this.layout();
    this.startCapyIdle();
    this.scale.on('resize', () => { this.closeModal(); this.layout(); });

    // ---- income tick (+ auto-clicker perk) ----
    this.autoAcc = 0;
    this.time.addEvent({ delay: 100, loop: true, callback: () => {
      const gain = cps() / 10;
      if (gain > 0) this.earn(gain, false);
      const rate = autoClickRate(STATE);
      if (rate > 0 && !this.modal) {
        this.autoAcc += rate / 10;
        let guard = 0;
        while (this.autoAcc >= 1 && guard++ < 20) { this.autoAcc -= 1; this.autoClick(); }
      }
      this.updateHud();
    }});

    // ---- passive pumpkin drops during the event ----
    this.time.addEvent({ delay: 8000, loop: true, callback: () => {
      if (eventActive() && Math.random() < 0.4) this.addPumpkins(1 + Math.floor(Math.random() * 3));
    }});

    // ---- autosave ----
    this.time.addEvent({ delay: 5000, loop: true, callback: () => saveState(STATE, true) });
    // ---- achievements check ----
    this.time.addEvent({ delay: 2000, loop: true, callback: () => this.checkAchievements() });
    // ---- leaderboard ----
    this.time.addEvent({ delay: 60000, loop: true, callback: () => {
      STATE.bestScore = Math.max(STATE.bestScore, STATE.totalEarnedAll);
      Y.submitScore(STATE.bestScore);
      saveState(STATE, true);
    }});

    Y.onVisibility(hidden => {
      if (hidden) saveState(STATE, true);
    });
    window.addEventListener('pagehide', () => saveState(STATE, true));

    // first interaction: unlock audio + music
    this.input.once('pointerdown', () => {
      unlockAudio();
      if (STATE.settings.music) startMusic();
    });

    // offline income & daily check
    this.checkOffline();

    // debug hook for automated tests
    window.__capy = {
      state: () => STATE,
      scene: () => this,
    };

    this.updateHud();
    Y.gameplayStart(); // hide Yandex loader: game is ready
  }

  questCtx() {
    return { totalEarnedAll: STATE.totalEarnedAll, cpsBase: cpsBase(), prestiges: STATE.prestiges, questSeed: STATE.questSeed };
  }

  // ---------------- layout / UI ----------------
  U(obj) { if (obj && obj.setDepth) obj.setDepth(10); this.ui.push(obj); return obj; }

  clearUI() {
    for (const o of this.ui) { if (o && o.destroy) { this.tweens.killTweensOf(o); o.destroy(); } }
    this.ui = [];
  }

  layout() {
    const W = this.scale.width, H = this.scale.height;
    this.colW = W > 560 ? Math.min(480, W * 0.6) : W;
    const CW = this.colW, cx = W / 2;
    this.clearUI();
    this.bg.setScale(Math.max(W / this.bg.width, H / this.bg.height)); // cover: crop, never stretch
    const capySize = Math.min(CW * 0.62, H * 0.30);
    this.capy.setPosition(cx, H * 0.36).setDisplaySize(capySize, capySize);
    this.capyBaseY = H * 0.36;
    this.capyBaseScaleX = this.capy.scaleX;
    this.capyBaseScaleY = this.capy.scaleY;
    this.mound.setPosition(cx, H * 0.36 + capySize * 0.40).setDisplaySize(capySize * 1.15, capySize * 0.5);
    this.comboTxt.setPosition(cx, H * 0.36 - capySize * 0.75);
    // parallax bands: seamless tiling tiles, anchored to the horizon (no stretching, no gaps)
    const bandW = Math.max(W, CW) + 140;
    const feetY = H * 0.36 + capySize * 0.42;
    const hillH = capySize * 0.30, treeH = capySize * 0.42;
    const fitTile = (ts, key, h, cyy) => {
      // NOTE: ts.texture.getSourceImage() is the tile's own fill canvas - use the real asset instead
      const img = this.textures.get(key).getSourceImage();
      const s = h / img.height; // keep the art's own aspect; the tile repeats to fill the width
      ts.setSize(bandW, h).setPosition(cx, cyy);
      ts.tileScaleX = s; ts.tileScaleY = s;
    };
    fitTile(this.layerHills, 'layer_hills', hillH, feetY - capySize * 0.13 - hillH / 2);
    fitTile(this.layerTrees, 'layer_trees', treeH, feetY - capySize * 0.10 - treeH / 2);
    this.layerHills.setVisible(H > 520); this.layerTrees.setVisible(H > 520);
    this.placeHat();
    this.setupWeather();
    this.applyEvolutionSprite(false);

    // ---- top HUD ----
    const hudH = 96;
    this.U(this.add.rectangle(cx, hudH / 2, CW, hudH, 0x123a6a, 1));
    this.U(this.add.nineslice(cx, hudH / 2, 'hud_frame', undefined, CW, hudH + 8, 24, 24, 20, 20));
    this.txtCoins = this.U(this.add.text(cx, 26, '0', { fontFamily: FONT, fontSize: '20px', padding: { x: 2, y: 7 }, color: '#ffd24a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5));
    this.coinIcon = this.U(this.add.image(0, 26, 'coin_gold').setDisplaySize(24, 24));
    this.txtCps = this.U(this.add.text(cx, 56, '', { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#bfe3ff' }).setOrigin(0.5));
    this.txtClick = this.U(this.add.text(cx, 74, '', { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffe9b0' }).setOrigin(0.5));
    this.txtStars = this.U(this.add.text(cx + CW / 2 - 10, 12, '', { fontFamily: FONT, fontSize: '10px', padding: { x: 2, y: 4 }, color: '#ffd24a', stroke: '#000', strokeThickness: 3 }).setOrigin(1, 0));
    this.txtGems = this.U(this.add.text(cx + CW / 2 - 10, 46, '', { fontFamily: FONT, fontSize: '10px', padding: { x: 2, y: 4 }, color: '#7df9ff', stroke: '#000', strokeThickness: 3 }).setOrigin(1, 0.5));
    this.gemIcon = this.U(this.add.image(0, 46, 'icon_gem').setDisplaySize(22, 22));
    const dz = this.U(this.add.zone(cx + CW / 2 - 50, 32, 100, 52).setInteractive({ useHandCursor: true }));
    dz.on('pointerdown', () => { SFX.ui(); this.openDonate(); });
    // event currency counter (left side of the HUD)
    const evOn = eventActive();
    this.pumpIcon = this.U(this.add.image(cx - CW / 2 + 20, 26, 'pumpkin').setDisplaySize(24, 24).setVisible(evOn));
    this.txtPump = this.U(this.add.text(cx - CW / 2 + 40, 26, '0', { fontFamily: FONT, fontSize: '11px', padding: { x: 2, y: 4 }, color: '#ffb347', stroke: '#000', strokeThickness: 3 }).setOrigin(0, 0.5).setVisible(evOn));
    const pz = this.U(this.add.zone(cx - CW / 2 + 44, 26, 90, 44).setInteractive({ useHandCursor: true }));
    pz.on('pointerdown', () => { SFX.ui(); this.openEvent(); });
    if (!evOn) { pz.disableInteractive(); }

    // ---- bottom bar ----
    const barH = 64;
    this.U(this.add.rectangle(cx, H - barH / 2, CW, barH, 0x123a6a, 1));
    this.U(this.add.nineslice(cx, H - barH / 2, 'dock_frame', undefined, CW, barH + 8, 24, 24, 16, 16));
    if (CW < W) { // PC side decor: dimmed wings with gold edges
      const edge = (W - CW) / 2;
      this.U(this.add.rectangle(edge / 2, H / 2, edge, H, 0x0a1a33, 0.88));
      this.U(this.add.rectangle(W - edge / 2, H / 2, edge, H, 0x0a1a33, 0.88));
      this.U(this.add.rectangle(edge, H / 2, 3, H, 0xffd24a, 0.5));
      this.U(this.add.rectangle(W - edge, H / 2, 3, H, 0xffd24a, 0.5));
    }
    const btns = [
      { key: 'shop', icon: 'icon_orange', cb: () => this.openShop() },
      { key: 'quests', icon: 'icon_medal', cb: () => this.openQuests() },
      { key: 'daily', icon: 'icon_gift', cb: () => this.openDaily() },
      { key: 'boost', icon: 'icon_boost', cb: () => this.openBoost() },
      { key: 'prestige', icon: 'crown', cb: () => this.openPrestige() },
      { key: 'settings', icon: 'icon_duck', cb: () => this.openSettings() },
    ];
    const n = btns.length;
    const bw = Math.min(56, (CW - 16) / n - 6);
    btns.forEach((b, i) => {
      const x = cx + (i - (n - 1) / 2) * (bw + 8);
      const y = H - barH / 2;
      const zone = this.U(this.add.zone(x, y, bw + 8, barH).setInteractive({ useHandCursor: true }));
      this.U(this.add.image(x, y - 8, 'tab_plate').setDisplaySize(bw * 0.80, bw * 0.80));
      const img = this.U(this.add.image(x, y - 8, b.icon).setDisplaySize(bw * 0.56, bw * 0.56));
      const lbl = this.U(this.add.text(x, y + 20, t('tabs')[b.key], { fontFamily: FONT, fontSize: '6px', padding: { x: 2, y: 3 }, color: '#bfe3ff' }).setOrigin(0.5));
      zone.on('pointerdown', () => { SFX.ui(); b.cb(); const s0 = img.scaleX; this.tweens.killTweensOf(img); img.setScale(s0); this.tweens.add({ targets: img, scaleX: s0 * 0.85, scaleY: s0 * 0.85, duration: 90, yoyo: true }); });
      this['bar_' + b.key] = { zone, img, lbl, x, y };
    });

    if (evOn) { // floating event button (keeps the bottom bar at 6 tabs)
      const ex = cx + CW / 2 - 36, ey = H * 0.62;
      const ring = this.U(this.add.circle(ex, ey, 27, 0x2a1a5a, 0.95).setStrokeStyle(3, 0xffb347));
      this.U(this.add.image(ex, ey - 5, 'pumpkin').setDisplaySize(28, 28));
      this.U(this.add.text(ex, ey + 15, t('eventTab'), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#ffb347' }).setOrigin(0.5));
      const ez = this.U(this.add.zone(ex, ey, 58, 58).setInteractive({ useHandCursor: true }));
      ez.on('pointerdown', () => { SFX.ui(); this.openEvent(); });
      this.tweens.add({ targets: ring, scaleX: 1.09, scaleY: 1.09, duration: 750, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
    }
    this.dailyBadge = this.U(this.add.circle(0, 0, 6, 0xff4a6a).setVisible(false));
    this.prestigeBadge = this.U(this.add.circle(0, 0, 6, 0xffd24a).setVisible(false));
    this.boostPill = this.U(this.add.rectangle(0, 0, 60, 20, 0x081a33, 0.9).setVisible(false));
    this.boostTimer = this.U(this.add.text(0, 0, '', { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#7dff8a', stroke: '#000', strokeThickness: 3 }).setOrigin(0.5).setVisible(false));
    // clouds spread
    const cloudY = [0.12, 0.2, 0.27];
    this.clouds.forEach((c, i) => {
      const s = Math.min(W * 0.3, 170) * (0.7 + i * 0.2);
      c.setDisplaySize(s, s * 0.5).setPosition(W * (0.15 + 0.35 * i), H * cloudY[i % 3]);
      c.setData('sp', 0.25 + i * 0.15);
    });

    this.updateHud();
  }

  updateHud() {
    if (!this.txtCoins) return;
    this.txtCoins.setText(fmt(STATE.coins) + ' ' + t('coins'));
    if (this.coinIcon) this.coinIcon.setPosition(this.scale.width / 2 - this.txtCoins.width / 2 - 24, 26);
    this.txtCps.setText(fmt(cps()) + ' ' + t('perSec'));
    this.txtClick.setText('+' + fmt(clickPower()) + ' ' + t('perClick'));
    this.txtStars.setText(STATE.stars > 0 ? '*' + STATE.stars : '');
    if (this.txtPump && STATE.event) this.txtPump.setText(fmt(STATE.event.pumpkins));
    if (this.txtGems) {
      this.txtGems.setText(fmt(STATE.gems || 0));
      if (this.gemIcon) this.gemIcon.setPosition(this.txtGems.x - this.txtGems.width - 16, 46);
    }
    // badges
    if (this.bar_daily) {
      const canDaily = this.canClaimDaily();
      this.dailyBadge.setPosition(this.bar_daily.x + 22, this.bar_daily.y - 26).setVisible(canDaily);
      const pend = pendingStars(STATE.totalEarnedRun, STATE.prestiges);
      this.prestigeBadge.setPosition(this.bar_prestige.x + 22, this.bar_prestige.y - 26).setVisible(pend > 0);
      const left = (STATE.boostUntil - Date.now()) / 1000;
      if (left > 0) {
        this.boostTimer.setVisible(true).setText('x2 ' + fmtTime(left))
          .setPosition(this.bar_boost.x, this.bar_boost.y - 44);
        this.boostPill.setVisible(true).setPosition(this.bar_boost.x, this.bar_boost.y - 44)
          .setDisplaySize(this.boostTimer.width + 16, 20);
      } else { this.boostTimer.setVisible(false); this.boostPill.setVisible(false); }
    }
  }

  // ---------------- clicks & earn ----------------
  onCapyClick(p) {
    unlockAudio();
    // juice: combo chain (1.1s window) + 5% crit x5
    const now = this.time.now;
    this.combo = (now - (this.lastClickT || 0) < 1100) ? (this.combo + 1) : 1;
    this.lastClickT = now;
    if (this.comboTimer) this.comboTimer.remove();
    this.comboTimer = this.time.delayedCall(1100, () => { this.combo = 0; this.comboTxt.setVisible(false); });
    const comboMult = 1 + Math.min(this.combo, 100) * 0.01;
    const crit = Math.random() < critChance(STATE);
    const gain = clickPower() * comboMult * (crit ? 5 : 1);
    STATE.totalClicks++;
    this.earn(gain, true);
    this.questProgress('clicks', 1);
    if (crit) SFX.crit(); else SFX.click();
    this.capySetHappy(crit ? 300 : 140);
    // squash (kill previous tween + reset to base scale: rapid clicks must not compound)
    this.tweens.killTweensOf(this.capy);
    this.capy.setScale(this.capyBaseScaleX, this.capyBaseScaleY);
    this.tweens.add({
      targets: this.capy,
      scaleX: this.capyBaseScaleX * 0.88,
      scaleY: this.capyBaseScaleY * 1.1,
      duration: 60, yoyo: true,
      onComplete: () => this.capy.setScale(this.capyBaseScaleX, this.capyBaseScaleY),
    });
    // particles
    this.emitterCoin.explode(crit ? 10 : 3, this.capy.x, this.capy.y - this.capy.displayHeight * 0.3);
    if (crit) {
      this.emitterBurst.explode(6, p.x || this.capy.x, p.y || this.capy.y);
      this.emitterFire.explode(2, p.x || this.capy.x, p.y || this.capy.y);
      this.cameras.main.shake(120, 0.004);
    }
    this.eventTask('clicks', 1);
    if (eventActive() && Math.random() < 0.10) this.dropPumpkin(p.x || this.capy.x, p.y || this.capy.y);
    if (this.combo >= 5) this.comboTxt.setVisible(true).setText(t('combo') + ' x' + this.combo);
    if (this.combo > 0 && this.combo % 25 === 0) this.emitterHeart.explode(8, this.capy.x, this.capy.y);
    // floating text
    const ft = this.add.text(p.x || this.capy.x, (p.y || this.capy.y) - 30, (crit ? t('crit') + ' +' : '+') + fmt(gain), { fontFamily: FONT, fontSize: crit ? '18px' : '12px', color: crit ? '#ff6a3d' : '#ffd24a', stroke: '#000', strokeThickness: crit ? 5 : 3, padding: { x: 2, y: crit ? 6 : 4 } }).setOrigin(0.5).setDepth(12);
    this.tweens.add({ targets: ft, y: ft.y - 60, alpha: 0, duration: 700, onComplete: () => ft.destroy() });
    this.updateHud();
  }

  earn(amount, fromClick) {
    STATE.coins += amount;
    STATE.totalEarnedRun += amount;
    STATE.totalEarnedAll += amount;
    STATE.cpsBase = cpsBase();
    this.questProgress('coins', amount);
    this.checkEvolution();
  }

  checkEvolution() {
    const idx = evolutionIndex(STATE.totalEarnedRun);
    if (idx > (this.evoIdx === undefined ? evolutionIndex(0) : this.evoIdx)) {
      this.evoIdx = idx;
      STATE.maxEvolution = Math.max(STATE.maxEvolution, idx + 1);
      this.applyEvolutionSprite(true);
    } else if (this.evoIdx === undefined) {
      this.evoIdx = idx;
      STATE.maxEvolution = Math.max(STATE.maxEvolution, idx + 1);
    }
  }

  applyEvolutionSprite(celebrate) {
    const idx = evolutionIndex(STATE.totalEarnedRun);
    this.evoIdx = idx;
    const key = EVOLUTIONS[idx].sprite;
    if (this.capy && this.capy.texture.key !== key) {
      this.capy.setTexture(key);
    }
    this.capyMood = 'base';
    if (this.happyTimer) { this.happyTimer.remove(); this.happyTimer = null; }
    if (celebrate) {
      SFX.evolve();
      this.emitterSpark.explode(40, this.capy.x, this.capy.y);
      this.emitterFire.explode(4, this.capy.x, this.capy.y);
      this.toast(t('evolution') + ' ' + t('evoNames')[idx]);
      this.flash();
      Y.showInterstitial();
    }
  }

  startCapyIdle() {
    if (this.bobTween) return;
    this.capyMood = 'base';
    const bob = { v: 0 };
    this.bobTween = this.tweens.add({
      targets: bob, v: 8, duration: 1300, yoyo: true, repeat: -1, ease: 'Sine.easeInOut',
      onUpdate: () => { if (this.capy) this.capy.y = this.capyBaseY + bob.v; },
    });
    // joyful blink every few seconds
    this.time.addEvent({ delay: 8000, loop: true, callback: () => {
      if (this.capyMood === 'base') this.capySetHappy(170);
    }});
    this.time.addEvent({ delay: 50, loop: true, callback: () => {
      const W = this.scale.width;
      for (const c of this.clouds) {
        c.x += c.getData('sp');
        if (c.x - c.displayWidth / 2 > W) c.x = -c.displayWidth / 2;
      }
      // parallax: continuous drift + eased pointer offset (tilePosition only -> no jitter)
      this.autoT += 0.35;
      this.pxOff += (this.pxTarget - this.pxOff) * 0.12;
      if (this.layerHills) this.layerHills.tilePositionX = -(this.autoT * 0.35 + this.pxOff * 14);
      if (this.layerTrees) this.layerTrees.tilePositionX = -(this.autoT + this.pxOff * 40);
      if (this.hat && this.capy) this.placeHat();
    }});
    // pointer parallax: records a target only, the timer applies it smoothly
    this.input.on('pointermove', p => {
      this.pxTarget = (p.x / this.scale.width - 0.5) * 2;
    });
  }

  capySetHappy(ms) {
    if (!this.capy) return;
    this.capy.setTexture(EVOLUTIONS[this.evoIdx || 0].sprite + '_b');
    this.capyMood = 'happy';
    if (this.happyTimer) this.happyTimer.remove();
    const evo = this.evoIdx;
    this.happyTimer = this.time.delayedCall(ms, () => {
      if (this.evoIdx === evo && this.capyMood === 'happy') {
        this.capy.setTexture(EVOLUTIONS[this.evoIdx || 0].sprite);
        this.capyMood = 'base';
      }
    });
  }

  flash() {
    const W = this.scale.width, H = this.scale.height;
    const r = this.add.rectangle(W / 2, H / 2, W, H, 0xffffff, 0.8).setDepth(50);
    this.tweens.add({ targets: r, alpha: 0, duration: 500, onComplete: () => r.destroy() });
  }

  // ---------------- quests ----------------
  questProgress(type, amount) {
    let changed = false;
    for (const q of STATE.quests) {
      if (q.type === type && !q.claimed) {
        q.progress = Math.min(q.target, q.progress + amount);
        if (q.progress >= q.target && !q.done) { q.done = true; SFX.quest(); this.toast(t('questDone')); changed = true; }
      }
    }
    if (changed) this.updateHud();
  }

  checkAchievements() {
    for (const a of ACHIEVEMENTS) {
      if (!STATE.achievements.includes(a.id) && a.check(STATE)) {
        STATE.achievements.push(a.id);
        if (a.reward) STATE.coins += a.reward;
        SFX.quest();
        this.toast(t('achievementDone') + (a.reward ? ' +' + fmt(a.reward) : ''));
      }
    }
  }

  // ---------------- toasts ----------------
  toast(msg) {
    const W = this.scale.width, H = this.scale.height;
    // keep the hero visible: bottom-anchored stack, max 4 (drop oldest)
    while (this.toasts.length >= 4) {
      const old = this.toasts.shift();
      if (old.scene) this.tweens.killTweensOf(old);
      old.destroy();
    }
    const y = H - 64 - 24 - this.toasts.length * 30;
    const txt = this.add.text(W / 2, y, msg, { fontFamily: FONT, fontSize: '9px', color: '#ffffff', stroke: '#000', strokeThickness: 3, backgroundColor: '#123a6a', padding: { x: 8, y: 6 } }).setOrigin(0.5).setDepth(60);
    this.toasts.push(txt);
    this.tweens.add({ targets: txt, delay: 2200, alpha: 0, duration: 400, onComplete: () => {
      txt.destroy();
      this.toasts = this.toasts.filter(x => x !== txt);
      this.toasts.forEach((x, i) => { x.y = this.scale.height - 64 - 24 - i * 30; });
    }});
  }

  // ---------------- modal helpers ----------------
  openModal(titleKey, builder, heightFrac = 0.72) {
    this.closeModal();
    Y.gameplayStop();
    const W = this.scale.width, H = this.scale.height;
    const m = this.add.container(0, 0).setDepth(100);
    const dim = this.add.rectangle(W / 2, H / 2, W, H, 0x000000, 0.6).setInteractive();
    dim.on('pointerdown', () => {}); // swallow
    const pw = Math.min(W - 24, 460);
    const ph = Math.min(H - 100, H * heightFrac);
    const panel = this.add.rectangle(W / 2, H / 2, pw, ph, 0x1c4f8f, 0.97).setStrokeStyle(4, 0x0d2c55);
    const title = this.add.text(W / 2, H / 2 - ph / 2 + 26, t(titleKey), { fontFamily: FONT, fontSize: '13px', padding: { x: 2, y: 5 }, color: '#ffd24a', stroke: '#000', strokeThickness: 3 }).setOrigin(0.5);
    // close btn
    const cb = this.add.image(W / 2 + pw / 2 - 24, H / 2 - ph / 2 + 24, 'btn_close').setDisplaySize(28, 28).setInteractive({ useHandCursor: true });
    cb.on('pointerdown', () => { SFX.ui(); this.closeModal(); });
    const inner = this.add.rectangle(W / 2, H / 2, pw - 10, ph - 10, 0x000000, 0).setStrokeStyle(2, 0x3a7ac9, 0.9);
    const under = this.add.image(W / 2, H / 2 - ph / 2 + 42, 'strip_divider').setDisplaySize(168, 18);
    m.add([dim, panel, inner, title, under, cb]);
    this.modal = { container: m, W, H, pw, ph, cx: W / 2, cy: H / 2, add: (o) => { m.add(o); return o; } };
    builder(this.modal, { top: H / 2 - ph / 2 + 60, left: W / 2 - pw / 2 + 14, right: W / 2 + pw / 2 - 14, width: pw - 28, height: ph - 80 });
    // pop-in: panel scale + contents fade
    panel.setScale(0.92); inner.setScale(0.92);
    this.tweens.add({ targets: [panel, inner], scaleX: 1, scaleY: 1, duration: 170, ease: 'Back.easeOut' });
    for (const o of m.list.slice()) {
      if (o === panel || o === inner || o === dim) continue;
      const a = o.alpha;
      o.setAlpha(0);
      this.tweens.add({ targets: o, alpha: a, duration: 140 });
    }
    return this.modal;
  }

  closeModal() {
    if (this.modal) {
      if (this.modalCleanup) { this.modalCleanup(); this.modalCleanup = null; }
      for (const ch of this.modal.container.list) this.tweens.killTweensOf(ch);
      this.modal.container.destroy();
      this.modal = null;
      this.shopRows = null;
      Y.gameplayStart();
    }
  }

  makeButton(x, y, w, h, label, cb, style = 'orange', fontSize = 9) {
    const TEX = { orange: 'btn_orange', blue: 'btn_blue', green: 'btn_green', red: 'btn_red' };
    const INK = { orange: '#5a2b0e', blue: '#0e2a5a', green: '#0e4a1a', red: '#5a0e1a' };
    const img = this.add.image(x, y, TEX[style] || TEX.orange).setDisplaySize(w, h).setInteractive({ useHandCursor: true });
    const txt = this.add.text(x, y, label, { fontFamily: FONT, fontSize: fontSize + 'px', color: INK[style] || INK.orange, stroke: '#ffffff', strokeThickness: 0, padding: { x: 2, y: Math.max(3, Math.round(fontSize * 0.35)) } }).setOrigin(0.5);
    img.on('pointerdown', () => {
      if (!img.getData('disabled')) {
        const sx = img.scaleX, sy = img.scaleY;
        this.tweens.killTweensOf([img, txt]);
        img.setScale(sx, sy); txt.setScale(1);
        this.tweens.add({ targets: img, scaleX: sx * 0.92, scaleY: sy * 0.92, duration: 80, yoyo: true, onComplete: () => img.setScale(sx, sy) });
        this.tweens.add({ targets: txt, scaleX: 0.92, scaleY: 0.92, duration: 80, yoyo: true, onComplete: () => txt.setScale(1) });
      }
      cb && cb(img, txt);
    });
    img.on('pointerover', () => { if (!img.getData('disabled')) img.setTint(0xffe0c0); });
    img.on('pointerout', () => { img.clearTint(); if (img.getData('disabled')) img.setTint(0x888888); });
    return { img, txt };
  }

  setDisabled(btn, off) {
    btn.img.setData('disabled', off);
    if (off) btn.img.setTint(0x888888); else btn.img.clearTint();
    btn.txt.setAlpha(off ? 0.7 : 1);
  }

  // ---------------- SHOP ----------------
  openShop() {
    this.openModal('shop', (m, area) => {
      const rows = [];
      const rowH = 56;
      const content = this.add.container(0, 0);
      m.add(content);
      // donate entry (always visible at top)
      const dg = this.makeButton(m.cx - 40, area.top + 22, 190, 36, t('iap'), () => this.openDonate(), 'blue', 9);
      content.add([dg.img, dg.txt, this.add.image(m.cx + 78, area.top + 22, 'icon_gem').setDisplaySize(28, 28)]);
      UPGRADES.forEach((u, i) => {
        const y = area.top + 14 + 48 + i * (rowH + 6);
        const row = this.add.container(0, y);
        const bgRow = this.add.nineslice(m.cx, 0, i % 2 ? 'row_plate_alt' : 'row_plate', undefined, area.width, rowH, 16, 16, 12, 12);
        const icon = this.add.image(area.left + 26, 0, u.icon).setDisplaySize(40, 40);
        const owned = STATE.upgrades[u.id] || 0;
        const name = this.add.text(area.left + 54, -14, t('up_' + u.id), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffffff' });
        const desc = this.add.text(area.left + 54, 2, `${t('up_' + u.id + '_d')}  ${t('level')}:${owned}`, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' });
        const cost = upgradeCost(u, owned);
        const btn = this.makeButton(area.right - 52, 0, 84, 34, fmt(cost), null, 'orange', 8);
        btn.img.removeAllListeners('pointerdown');
        btn.img.on('pointerdown', () => this.buyUpgrade(u, btn.txt, desc));
        this.setDisabled(btn, STATE.coins < cost);
        row.add([bgRow, icon, name, desc, btn.img, btn.txt]);
        rows.push({ row, btn, u, y });
        content.add(row);
      });
      this.shopRows = rows;
      let contentH = 48 + UPGRADES.length * (rowH + 6);
      // (IAP moved to the Donate modal)
      this.attachDragScroll(content, area, contentH);
    }, 0.78);
  }

  buyUpgrade(u, txt, desc) {
    const owned = STATE.upgrades[u.id] || 0;
    const cost = upgradeCost(u, owned);
    if (STATE.coins < cost) { SFX.error(); this.toast(t('notEnough')); return; }
    STATE.coins -= cost;
    STATE.upgrades[u.id] = owned + 1;
    STATE.cpsBase = cpsBase();
    this.questProgress('buy', 1);
    this.eventTask('buy', 1);
    SFX.buy();
    try {
      const mm = txt ? txt.getWorldTransformMatrix() : null;
      if (mm) this.emitterStar.explode(6, mm.tx, mm.ty);
    } catch (e) {}
    if (this.shopRows) for (const r of this.shopRows) this.setDisabled(r.btn, STATE.coins < upgradeCost(r.u, STATE.upgrades[r.u.id] || 0));
    if (txt) txt.setText(fmt(upgradeCost(u, owned + 1)));
    if (desc) desc.setText(`${t('up_' + u.id + '_d')}  ${t('level')}:${owned + 1}`);
    this.updateHud();
    saveState(STATE, true);
  }

  openDonate() {
    const tab = this.donateTab || 'packs';
    const TABS = [['packs', t('iap')], ['perks', t('perks')], ['coins', t('coinsPacks')], ['skins', t('cosmetics')]];
    this.openModal('iap', async (m, area) => {
      // tab strip
      const tw = (area.width - 12) / TABS.length;
      TABS.forEach((tb, i) => {
        const x = area.left + 6 + tw * i + tw / 2;
        const b = this.makeButton(x, area.top + 12, tw - 4, 28, tb[1], () => {
          this.donateTab = tb[0];
          SFX.ui();
          this.closeModal();
          this.openDonate();
        }, tab === tb[0] ? 'orange' : 'blue', 7);
        m.add([b.img, b.txt]);
      });
      const rowH = 56;
      const rowY = (j) => area.top + 52 + j * (rowH + 8) + rowH / 2;
      const addRow = (y, icon, title, desc, btnLabel, style, cb) => {
        m.add(this.add.rectangle(m.cx, y, area.width, rowH, 0x2a1a5a, 0.9));
        m.add(this.add.nineslice(m.cx, y, 'row_plate_alt', undefined, area.width, rowH, 16, 16, 12, 12));
        m.add(this.add.image(area.left + 28, y, icon).setDisplaySize(38, 38));
        m.add(this.add.text(area.left + 56, y - 10, title, { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffd24a' }));
        m.add(this.add.text(area.left + 56, y + 6, desc, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }));
        const b = this.makeButton(area.right - 52, y, 84, 34, btnLabel, cb, style, 8);
        m.add([b.img, b.txt]);
        return b;
      };
      const spend = (cost) => {
        if ((STATE.gems || 0) < cost) { SFX.error(); this.toast(t('noGems')); return false; }
        STATE.gems -= cost;
        return true;
      };
      const afterBuy = (x, y) => {
        SFX.buy();
        this.emitterStar.explode(8, x, y);
        this.updateHud();
        saveState(STATE, true);
        this.closeModal();
        this.openDonate();
      };

      if (tab === 'packs') {
        m.add(this.add.text(m.cx, area.top + 34, t('iapDesc'), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff', align: 'center', wordWrap: { width: area.width } }).setOrigin(0.5, 0));
        let catalog = [];
        if (Y.hasPayments()) { try { catalog = await Y.getCatalog(); } catch (e) { catalog = []; } }
        if (!this.modal) return;
        const demo = !Y.hasPayments();
        const priceOf = (p) => {
          const found = catalog.find(c => c.id === p.id);
          if (found && found.priceValue) return String(found.priceValue).replace(/\xa0/g, ' ');
          return p.price + ' \u20bd';
        };
        IAP_PRODUCTS.forEach((p, j) => {
          const y = rowY(j);
          addRow(y, 'icon_gem', '+' + fmt(p.gems) + ' ' + t('gems'), demo ? 'DEMO' : 'YANDEX',
            demo ? 'DEMO' : priceOf(p), 'blue', () => this.buyIAP(p, area.right - 52, y));
        });
      } else if (tab === 'perks') {
        m.add(this.add.text(m.cx, area.top + 34, t('perks'), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }).setOrigin(0.5, 0));
        PERKS.forEach((pk, j) => {
          const lv = perkLevel(STATE, pk.id);
          const max = lv >= pk.levels.length;
          const cost = max ? 0 : pk.levels[lv].cost;
          const y = rowY(j);
          const b = addRow(y, pk.icon, t('perk_' + pk.id), t('perk_' + pk.id + '_d') + '  ' + t('level') + ':' + lv,
            max ? t('max') : fmt(cost), max ? 'green' : 'blue', () => {
              if (max) return;
              if (!spend(cost)) return;
              STATE.perks[pk.id] = lv + 1;
              afterBuy(area.right - 52, y);
            });
          if (max) { this.setDisabled(b, true); b.img.disableInteractive(); }
        });
      } else if (tab === 'coins') {
        m.add(this.add.text(m.cx, area.top + 34, t('exchangeD'), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff', align: 'center' }).setOrigin(0.5, 0));
        COIN_PACKS.forEach((p, j) => {
          const y = rowY(j);
          addRow(y, 'coin_gold', fmt(packCoins(p, cps())) + ' ' + t('coins'), p.gems + ' ' + t('gems'),
            fmt(p.gems), 'green', () => {
              if (!spend(p.gems)) return;
              const c = packCoins(p, cps());
              STATE.coins += c;
              STATE.totalEarnedRun += c;
              STATE.totalEarnedAll += c;
              this.questProgress('coins', c);
              this.emitterCoin.explode(10, m.cx, y);
              afterBuy(area.right - 52, y);
            });
        });
      } else {
        m.add(this.add.text(m.cx, area.top + 34, t('cosmetics'), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }).setOrigin(0.5, 0));
        HATS.forEach((h, j) => {
          const y = rowY(j);
          const owned = STATE.hats.owned.includes(h.id);
          const active = STATE.hats.active === h.id;
          if (h.id === 'none') {
            const b = addRow(y, 'crown', t('hat_none'), t('cosmetics'), active ? t('worn') : t('wear'),
              active ? 'green' : 'blue', () => {
                STATE.hats.active = 'none';
                this.applyHat();
                SFX.ui();
                this.closeModal();
                this.openDonate();
              });
            if (active) { this.setDisabled(b, true); b.img.disableInteractive(); }
            return;
          }
          const b = addRow(y, 'hat_' + h.id, t('hat_' + h.id), owned ? (active ? t('worn') : t('wear')) : fmt(h.cost),
            owned ? (active ? t('worn') : t('wear')) : t('buy'), owned ? (active ? 'green' : 'blue') : 'orange', () => {
              if (!owned) {
                if (!spend(h.cost)) return;
                STATE.hats.owned.push(h.id);
                STATE.hats.active = h.id;
                this.applyHat();
                afterBuy(area.right - 52, y);
                return;
              }
              STATE.hats.active = h.id;
              this.applyHat();
              SFX.ui();
              this.closeModal();
              this.openDonate();
            });
          if (active) { this.setDisabled(b, true); b.img.disableInteractive(); }
        });
      }
    }, 0.72);
  }

  async buyIAP(p, bx, by) {
    const demo = !Y.hasPayments(); // preview without SDK: clearly-labeled DEMO grants
    const grant = () => {
      STATE.gems = (STATE.gems || 0) + p.gems;
      SFX.buy();
      this.toast('+' + fmt(p.gems) + ' ' + t('gems'));
      if (bx !== undefined) { this.emitterStar.explode(10, bx, by); this.emitterFire.explode(2, bx, by); }
      this.updateHud();
      saveState(STATE, true);
    };
    if (demo) { grant(); return; }
    const product = await Y.purchase(p.id);
    if (product) grant();
    else { SFX.error(); this.toast(t('iapFail')); }
  }

  // ---------------- WEATHER / HAT ----------------
  setupWeather() {
    if (this.weather) { this.weather.destroy(); this.weather = null; }
    const W = this.scale.width;
    const month = new Date().getMonth();
    let tex = 'part_spark';
    if (eventActive()) tex = 'part_leaf';
    else if (month === 11 || month === 0 || month === 1) tex = 'part_snow';
    this.weather = this.add.particles(0, 0, tex, {
      x: { min: -30, max: W + 30 }, y: -30,
      lifespan: 11000, speedY: { min: 25, max: 70 }, speedX: { min: -20, max: 20 },
      rotate: { start: 0, end: 360 }, scale: { start: 0.9, end: 0.9 },
      alpha: { start: 0.95, end: 0.3 }, frequency: 650, quantity: 1,
    });
    this.weather.setDepth(8);
  }

  applyHat() { return this.placeHat(); }

  // seats the hat on the capybara's head from measured per-evolution head geometry
  placeHat() {
    if (!this.hat || !this.capy) return;
    const id = (STATE.hats && STATE.hats.active) || 'none';
    if (id === 'none') { this.hat.setVisible(false); return; }
    this.hat.setTexture('hat_' + id).setVisible(true);
    const head = HEADS[Math.min(HEADS.length - 1, this.evoIdx || 0)];
    const hat = HATS.find(h => h.id === id) || HATS[1];
    const bb = hat.bb || { w: 96, h: 96, bottom: 96 };
    const scale = this.capy.displayHeight / 128;

    // fit: width from the head, height clamped so the hat never towers over the sprite
    let w = head.w * HAT_W;
    let h = w * (bb.h / bb.w);
    const maxH = head.w * HAT_MAX_H;
    if (h > maxH) { w *= maxH / h; h = maxH; }
    const size = w * 96 / bb.w;           // canvas size that makes the ART w units wide
    const bottomOff = bb.bottom / 96 - 0.5; // art bottom offset from the canvas centre

    const brimY = head.top + head.w * HAT_BRIM;                       // sprite row of the brim
    const targetY = this.capy.y - this.capy.displayHeight / 2 + brimY * scale;
    const cx = this.capy.x + (head.cx - 64) * scale;
    this.hat.setDisplaySize(size * scale, size * scale);
    this.hat.setPosition(cx, targetY - bottomOff * size * scale);
    // expose the art box for the geometry audit
    this.hat.setData('art', {
      x0: cx - w * scale / 2, x1: cx + w * scale / 2,
      top: targetY - h * scale, bottom: targetY, w: w, h: h,
    });
  }

  // one consistent progress bar: frame below, fill inset, grows from the left edge
  progressBar(x, y, w, h, frac, fill = 0x7dff8a) {
    const f = Math.min(1, Math.max(0, frac || 0));
    const frame = this.add.image(x, y, 'bar_frame').setDisplaySize(w + 10, h + 14);
    const inner = this.add.rectangle(x - w / 2, y, w * f, h - 2, fill).setOrigin(0, 0.5);
    return [frame, inner];
  }

  // ---------------- EVENT ----------------
  rollEventTasks() {
    const ev = STATE.event;
    if (!ev) return;
    if (!ev.tasks || !ev.tasks.length || ev.taskDay !== dayKey()) {
      ev.taskDay = dayKey();
      ev.tasks = makeEventTasks();
      saveState(STATE, true);
    }
  }

  addPumpkins(n) {
    if (!eventActive() || !STATE.event) return;
    STATE.event.pumpkins += n;
    STATE.event.pumpkinsTotal = (STATE.event.pumpkinsTotal || 0) + n;
    this.eventTask('pumpkins', n);
    this.updateHud();
  }

  eventTask(id, n) {
    const ev = STATE.event;
    if (!ev || !ev.tasks) return;
    const tk = ev.tasks.find(x => x.id === id);
    if (tk && !tk.claimed) tk.progress = Math.min(tk.target, tk.progress + n);
  }

  dropPumpkin(x, y) {
    this.addPumpkins(1);
    if (!this.pumpIcon) return;
    const ico = this.add.image(x, y, 'pumpkin').setDisplaySize(30, 30).setDepth(12);
    this.tweens.add({
      targets: ico, x: this.pumpIcon.x, y: this.pumpIcon.y, scaleX: 0.5, scaleY: 0.5,
      duration: 620, ease: 'Cubic.easeIn', onComplete: () => ico.destroy(),
    });
  }

  eventCoins(sec) { return Math.max(100, Math.ceil(cps() * sec)); }

  rewardLabel(r) {
    if (r.hat) return t('hat_' + r.hat);
    if (r.boost) return t('boost') + ' ' + r.boost + 'm';
    if (r.gems) return '+' + r.gems;
    return fmt(this.eventCoins(r.sec));
  }

  claimTier(i, prem) {
    const ev = STATE.event;
    const tr = PASS_TIERS[i];
    if (!ev || ev.pumpkins < tr.need) { SFX.error(); return; }
    if (prem && !ev.premium) { SFX.error(); this.toast(t('passPremium')); return; }
    const key = prem ? 'claimedPrem' : 'claimedFree';
    if (ev[key].includes(i)) return;
    ev[key].push(i);
    ev.tierClaimed = ev.claimedFree.length + ev.claimedPrem.length;
    const r = prem ? tr.prem : tr.free;
    if (r.sec) {
      const c = this.eventCoins(r.sec);
      STATE.coins += c; STATE.totalEarnedRun += c; STATE.totalEarnedAll += c;
      this.questProgress('coins', c);
    }
    if (r.gems) STATE.gems = (STATE.gems || 0) + r.gems;
    if (r.hat) {
      if (!STATE.hats.owned.includes(r.hat)) STATE.hats.owned.push(r.hat);
      STATE.hats.active = r.hat;
      this.applyHat();
    }
    if (r.boost) STATE.boostUntil = Math.max(STATE.boostUntil, Date.now()) + r.boost * 60000;
    SFX.daily();
    this.emitterStar.explode(10, this.scale.width / 2, this.scale.height / 2);
    this.emitterFire.explode(2, this.scale.width / 2, this.scale.height / 2);
    this.updateHud();
    saveState(STATE, true);
    this.closeModal();
    this.openEvent();
  }

  claimEventTask(tk) {
    if (tk.claimed || tk.progress < tk.target) return;
    tk.claimed = true;
    const spec = EVENT_TASKS.find(x => x.id === tk.id);
    if (spec) {
      this.addPumpkins(spec.rewardP);
      const c = this.eventCoins(spec.sec);
      STATE.coins += c; STATE.totalEarnedRun += c; STATE.totalEarnedAll += c;
      this.questProgress('coins', c);
    }
    SFX.daily();
    this.emitterCoin.explode(10, this.scale.width / 2, this.scale.height / 2);
    this.updateHud();
    saveState(STATE, true);
    this.closeModal();
    this.openEvent();
  }

  openEvent() {
    if (!eventActive()) { this.toast(t('eventOff')); return; }
    this.rollEventTasks();
    const ev = STATE.event;
    this.openModal('eventTitle', (m, area) => {
      const content = this.add.container(0, 0);
      m.add(content);
      let y = area.top;
      content.add([
        this.add.image(m.cx, y + 20, 'banner').setDisplaySize(area.width, 46),
        this.add.image(area.left + 26, y + 20, 'pumpkin').setDisplaySize(30, 30),
        this.add.text(m.cx + 10, y + 8, fmt(ev.pumpkins) + ' ' + t('pumpkins'), { fontFamily: FONT, fontSize: '10px', padding: { x: 2, y: 3 }, color: '#5a2b0e' }).setOrigin(0.5, 0),
        this.add.text(m.cx + 10, y + 26, t('eventEnds') + ': ' + eventDaysLeft() + ' ' + t('days'), { fontFamily: FONT, fontSize: '6px', padding: { x: 2, y: 3 }, color: '#5a2b0e' }).setOrigin(0.5, 0),
      ]);
      y += 52;
      content.add(this.add.text(area.left + 4, y + 2, t('pass') + ' ' + passTierReached(ev.pumpkins) + '/' + PASS_TIERS.length, { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffd24a' }));
      const pb = this.makeButton(area.right - 62, y + 10, 124, 28, ev.premium ? t('passOwned') : t('passPremium'), (img) => {
        if (ev.premium || img.getData('claimed')) return;
        if ((STATE.gems || 0) < PASS_PREMIUM_COST) { SFX.error(); this.toast(t('noGems')); return; }
        STATE.gems -= PASS_PREMIUM_COST;
        ev.premium = true;
        SFX.buy();
        this.emitterStar.explode(10, area.right - 62, y + 10);
        saveState(STATE, true);
        this.closeModal();
        this.openEvent();
      }, ev.premium ? 'green' : 'orange', 7);
      if (ev.premium) { this.setDisabled(pb, true); pb.img.disableInteractive(); }
      content.add([pb.img, pb.txt]);
      y += 40;
      content.add(this.add.nineslice(m.cx, y + 6, 'banner_small', undefined, 150, 26, 40, 40, 8, 8));
      content.add(this.add.text(m.cx, y + 6, t('tasks'), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }).setOrigin(0.5));
      y += 20;
      for (const tk of ev.tasks) {
        const done = tk.progress >= tk.target;
        content.add(this.add.rectangle(m.cx, y + 17, area.width, 34, 0x0d2c55, 0.85));
        content.add(this.add.nineslice(m.cx, y + 17, 'row_plate_alt', undefined, area.width, 34, 16, 16, 10, 10));
        content.add(this.add.text(area.left + 10, y + 4, t('task_' + tk.id), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#ffffff' }));
        content.add(this.add.text(area.left + 10, y + 20, fmt(tk.progress) + '/' + fmt(tk.target), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: done ? '#7dff8a' : '#9fd0ff' }));
        const frac = Math.min(1, tk.progress / tk.target);
        content.add(this.progressBar(area.left + 128, y + 24, 76, 8, frac));
        const b = this.makeButton(area.right - 44, y + 17, 76, 26, tk.claimed ? t('claimed') : t('dailyClaim'), () => this.claimEventTask(tk), tk.claimed ? 'green' : (done ? 'orange' : 'red'), 7);
        this.setDisabled(b, tk.claimed || !done);
        if (tk.claimed || !done) b.img.disableInteractive();
        content.add([b.img, b.txt]);
        y += 40;
      }
      y += 10;
      content.add(this.add.nineslice(m.cx, y + 6, 'banner_small', undefined, 210, 26, 40, 40, 8, 8));
      content.add(this.add.text(m.cx, y + 6, t('tier') + ' | ' + t('dailyClaim'), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }).setOrigin(0.5));
      y += 20;
      PASS_TIERS.forEach((tr, i) => {
        const reached = ev.pumpkins >= tr.need;
        const gotF = ev.claimedFree.includes(i);
        const gotP = ev.claimedPrem.includes(i);
        content.add(this.add.nineslice(m.cx, y + 19, i % 2 ? 'row_plate_alt' : 'row_plate', undefined, area.width, 38, 16, 16, 10, 10));
        if (reached) content.add(this.add.image(area.left + 12, y + 19, 'pumpkin').setDisplaySize(14, 14));
        content.add(this.add.text(area.left + 12, y + 4, (i + 1) + '. ' + fmt(tr.need), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: reached ? '#ffb347' : '#5f8fbf' }));
        content.add(this.add.text(area.left + 12, y + 22, fmt(ev.pumpkins) + '/' + fmt(tr.need), { fontFamily: FONT, fontSize: '6px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }));
        const bxF = area.left + 118, bxP = area.left + 236;
        const bF = this.makeButton(bxF, y + 19, 108, 28, gotF ? t('claimed') : this.rewardLabel(tr.free), () => this.claimTier(i, false), gotF ? 'green' : (reached ? 'orange' : 'red'), 7);
        this.setDisabled(bF, gotF || !reached);
        if (gotF || !reached) bF.img.disableInteractive();
        const bP = this.makeButton(bxP, y + 19, 108, 28, gotP ? t('claimed') : this.rewardLabel(tr.prem), () => this.claimTier(i, true), gotP ? 'green' : ((reached && ev.premium) ? 'blue' : 'red'), 7);
        this.setDisabled(bP, gotP || !reached || !ev.premium);
        if (gotP || !reached || !ev.premium) bP.img.disableInteractive();
        content.add([bF.img, bF.txt, bP.img, bP.txt]);
        y += 42;
      });
      this.attachDragScroll(content, area, y + 30);
    }, 0.85);
  }

  // ---------------- AUTO-CLICK (perk) ----------------
  autoClick() {
    const crit = Math.random() < critChance(STATE);
    const gain = clickPower() * (crit ? 5 : 1);
    STATE.totalClicks++;
    this.earn(gain, true);
    this.questProgress('clicks', 1);
    this.eventTask('clicks', 1);
    if (eventActive() && Math.random() < 0.10) this.addPumpkins(1);
    if (Math.random() < 0.12) this.emitterCoin.explode(1, this.capy.x, this.capy.y - this.capy.displayHeight * 0.3);
  }

  // ---------------- SHARED DRAG SCROLL ----------------
  attachDragScroll(content, area, contentH) {
    const maskShape = this.add.graphics();
    maskShape.fillStyle(0xffffff).fillRect(area.left - 4, area.top, area.width + 8, area.height);
    content.setMask(maskShape.createGeometryMask());
    maskShape.setVisible(false); // geometry only
    content.setData('clip', { y0: area.top, y1: area.top + area.height });
    if (this.modal) this.modal.add(maskShape);
    let offsetY = 0;
    const applyScroll = () => {
      offsetY = Phaser.Math.Clamp(offsetY, Math.min(-(contentH - area.height + 30), 0), 0);
      content.y = offsetY;
    };
    let dragStart = null;
    const move = p => { if (dragStart !== null && p.isDown) { offsetY += p.y - dragStart; dragStart = p.y; applyScroll(); } };
    const up = () => { dragStart = null; };
    const down = p => { if (p.x > area.left && p.x < area.right && p.y > area.top && p.y < area.top + area.height) dragStart = p.y; };
    this.input.on('pointermove', move);
    this.input.on('pointerup', up);
    this.input.on('pointerdown', down);
    const prev = this.modalCleanup;
    this.modalCleanup = () => {
      if (prev) prev();
      this.input.off('pointermove', move);
      this.input.off('pointerup', up);
      this.input.off('pointerdown', down);
    };
  }

  // ---------------- QUESTS ----------------
  openQuests() {
    this.openModal('quests', (m, area) => {
      STATE.quests.forEach((q, i) => {
        const y = area.top + 30 + i * 92;
        m.add(this.add.rectangle(m.cx, y, area.width, 82, 0x0d2c55, 0.8));
        m.add(this.add.nineslice(m.cx, y, 'row_plate', undefined, area.width, 82, 16, 16, 12, 12));
        const typeKey = 'quest_' + q.type;
        m.add(this.add.text(area.left + 10, y - 26, t(typeKey) + ': ' + fmt(q.target), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffffff' }));
        m.add(this.add.text(area.left + 10, y - 6, t('questProgress') + ': ' + fmt(Math.floor(q.progress)) + '/' + fmt(q.target), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }));
        m.add(this.add.text(area.left + 10, y + 12, t('questReward') + ': ' + fmt(q.reward), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#ffd24a' }));
        if (q.done && !q.claimed) {
          const b = this.makeButton(area.right - 55, y + 8, 90, 30, t('dailyClaim'), () => {
            this.emitterStar.explode(8, area.right - 55, y + 8);
            STATE.coins += q.reward;
            q.claimed = true;
            SFX.coin();
            STATE.questSeed++;
            STATE.quests[i] = makeQuest(this.questCtx(), i);
            this.updateHud();
            this.closeModal();
            this.openQuests();
          }, 'green', 8);
          m.add([b.img, b.txt]);
        } else if (q.claimed) {
          m.add(this.add.text(area.right - 55, y + 8, t('claimed'), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#7dff8a' }).setOrigin(0.5));
        } else {
          // progress bar (shared frame, left-anchored fill)
          const frac = Math.min(1, q.progress / q.target);
          m.add(this.progressBar(area.right - 55, y + 8, 90, 10, frac));
        }
      });
      // achievements summary
      const yA = area.top + 30 + 3 * 92 + 8;
      m.add(this.add.text(area.left + 10, yA, `${t('achievements')}: ${STATE.achievements.length}/${ACHIEVEMENTS.length}`, { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }));
      m.add(this.add.text(area.left + 10, yA + 20, `${t('totalClicks')}: ${fmt(STATE.totalClicks)}`, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }));
      m.add(this.add.text(area.left + 10, yA + 36, `${t('totalEarned')}: ${fmt(STATE.totalEarnedAll)}`, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }));
    }, 0.8);
  }

  // ---------------- DAILY ----------------
  canClaimDaily() {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    return STATE.dailyLast !== today.getTime();
  }

  openDaily() {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const can = this.canClaimDaily();
    this.openModal('dailyTitle', (m, area) => {
      // streak row: 7 days
      const nextS = can ? this.nextStreak() : STATE.dailyStreak;
      const claimedCount = can ? (((nextS - 1) % 7 + 7) % 7) : ((((STATE.dailyStreak - 1) % 7 + 7) % 7) + 1);
      const dayInCycle = can ? (((nextS - 1) % 7 + 7) % 7) : (claimedCount - 1);
      const cell = Math.min(52, (area.width - 20) / 7);
      for (let d = 0; d < 7; d++) {
        const x = area.left + 10 + d * cell + cell / 2;
        const y = area.top + 30;
        const claimed = d < claimedCount;
        const cur = d === dayInCycle;
        const cellPlate = this.add.image(x, y, 'cell_plate').setDisplaySize(cell - 6, cell - 6);
        if (claimed) cellPlate.setTint(0x8fe8a4);
        m.add(cellPlate);
        if (cur) m.add(this.add.rectangle(x, y, cell - 2, cell - 2, 0x000000, 0).setStrokeStyle(3, 0xffd24a));
        m.add(this.add.text(x, y - 8, String(d + 1), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: cur ? '#ffd24a' : '#9fd0ff' }).setOrigin(0.5));
        m.add(this.add.text(x, y + 10, fmt(dailyReward(d + 1, cpsBase())), { fontFamily: FONT, fontSize: '6px', padding: { x: 2, y: 3 }, color: '#ffffff' }).setOrigin(0.5));
      }
      const chestY = area.top + 116;
      const glow = this.add.image(m.cx, chestY + 62, 'pedestal_glow').setDisplaySize(210, 94);
      const ped = this.add.image(m.cx, chestY + 60, 'pedestal').setDisplaySize(162, 66);
      const chest = this.add.image(m.cx, chestY, can ? 'chest_closed' : 'chest_open').setDisplaySize(122, 122);
      m.add([glow, ped, chest]);
      this.tweens.add({ targets: glow, alpha: { from: 0.75, to: 1 }, duration: 1100, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
      const yBtn = area.top + 226;
      if (can) {
        const nextStreak = this.nextStreak();
        const dayNum = ((nextStreak - 1) % 7) + 1;
        const reward = dailyReward(dayNum, cpsBase());
        const gemBonus = dayNum === 7 ? DAILY_GEMS_DAY7 : 0;
        const b = this.makeButton(m.cx, yBtn, 180, 44, t('dailyClaim') + ' +' + fmt(reward), () => {
          if (b.img.getData('claimed')) return;
          b.img.setData('claimed', true);
          this.setDisabled(b, true);
          b.img.disableInteractive();
          STATE.coins += reward;
          if (gemBonus) STATE.gems = (STATE.gems || 0) + gemBonus;
          STATE.dailyLast = today.getTime();
          STATE.dailyStreak = nextStreak;
          STATE.dailyTotal++;
          SFX.daily();
          // chest opening ceremony
          chest.setTexture('chest_open');
          this.tweens.add({ targets: chest, scaleX: chest.scaleX * 1.15, scaleY: chest.scaleY * 1.15, duration: 200, yoyo: true });
          this.emitterCoin.explode(12, m.cx, chestY - 20);
          this.emitterStar.explode(6, m.cx, chestY - 10);
          this.emitterFire.explode(3, m.cx, chestY);
          this.updateHud();
          saveState(STATE, true);
          const mref = this.modal;
          this.time.delayedCall(950, () => { if (this.modal === mref) this.closeModal(); });
        }, 'green', 9);
        m.add([b.img, b.txt]);
      } else {
        m.add(this.add.text(m.cx, yBtn, t('dailyComeBack'), { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }).setOrigin(0.5));
      }
      m.add(this.add.text(m.cx, yBtn + 42, `${t('streak')}: ${STATE.dailyStreak}`, { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }).setOrigin(0.5));
    }, 0.62);
  }

  nextStreak() {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const yesterday = today.getTime() - 86400000;
    if (STATE.dailyLast === yesterday) return STATE.dailyStreak + 1;
    return 1;
  }

  // ---------------- BOOST ----------------
  openBoost() {
    const left = Math.max(0, (STATE.boostUntil - Date.now()) / 1000);
    this.openModal('boostTitle', (m, area) => {
      const y0 = area.top + 6;
      m.add(this.add.image(m.cx, y0 + 26, 'icon_boost').setDisplaySize(52, 52));
      m.add(this.add.text(m.cx, y0 + 62, left > 0 ? t('boostActive') + ' ' + fmtTime(left) : t('boostDesc'), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: left > 0 ? '#7dff8a' : '#9fd0ff' }).setOrigin(0.5));
      const yAd = y0 + 108;
      const cd = Math.max(0, REWARDED_COOLDOWN - (Date.now() - (STATE.lastAdAt || 0)) / 1000);
      const bAd = this.makeButton(m.cx, yAd, 220, 40, cd > 0 ? t('adWait') + ' ' + fmtTime(cd) : t('boostAd'), () => {
        if (cd > 0) { SFX.error(); return; }
        STATE.lastAdAt = Date.now();
        Y.showRewarded(() => {
          STATE.boostUntil = Math.max(STATE.boostUntil, Date.now()) + BOOST_DURATION * 1000;
          SFX.daily();
          this.updateHud();
          saveState(STATE, true);
          this.closeModal();
          this.openBoost();
        });
      }, cd > 0 ? 'red' : 'green', 8);
      if (cd > 0) { this.setDisabled(bAd, true); bAd.img.disableInteractive(); }
      m.add([bAd.img, bAd.txt, this.add.image(m.cx - 128, yAd, 'icon_tv').setDisplaySize(32, 32)]);
      const yGem = yAd + 54;
      const bGem = this.makeButton(m.cx, yGem, 220, 40, t('boostGem'), () => {
        if ((STATE.gems || 0) < GEM_BOOST_COST) { SFX.error(); this.toast(t('noGems')); return; }
        STATE.gems -= GEM_BOOST_COST;
        STATE.boostUntil = Math.max(STATE.boostUntil, Date.now()) + GEM_BOOST_DURATION * 1000;
        SFX.daily();
        this.emitterStar.explode(8, m.cx, yGem);
        this.updateHud();
        saveState(STATE, true);
        this.closeModal();
        this.openBoost();
      }, 'blue', 8);
      m.add([bGem.img, bGem.txt, this.add.image(m.cx - 128, yGem, 'icon_gem').setDisplaySize(30, 30)]);
    }, 0.55);
  }

  // ---------------- PRESTIGE ----------------
  openPrestige() {
    const pend = pendingStars(STATE.totalEarnedRun);
    this.openModal('prestigeTitle', (m, area) => {
      m.add(this.add.image(m.cx - 120, area.top - 18, 'trophy').setDisplaySize(40, 40));
      m.add(this.add.text(m.cx, area.top + 20, t('prestigeDesc'), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffffff', align: 'center', wordWrap: { width: area.width } }).setOrigin(0.5, 0));
      m.add(this.add.text(m.cx, area.top + 80, '* ' + STATE.stars + '  (x' + starMultiplier(STATE.stars).toFixed(2) + ')', { fontFamily: FONT, fontSize: '11px', padding: { x: 2, y: 4 }, color: '#ffd24a' }).setOrigin(0.5));
      m.add(this.add.text(m.cx, area.top + 110, t('prestigeStars') + ': ' + pend, { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: pend > 0 ? '#7dff8a' : '#ff8899' }).setOrigin(0.5));
      if (pend <= 0) {
        m.add(this.add.text(m.cx, area.top + 140, t('prestigeNeed') + ': ' + fmt(nextPrestigeNeed(STATE.prestiges)), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }).setOrigin(0.5));
        const db = this.makeButton(m.cx, area.top + 190, 200, 44, t('prestigeNow') + ' +0*', null, 'red', 9);
        this.setDisabled(db, true);
        db.img.disableInteractive();
        m.add([db.img, db.txt]);
      } else {
        const b = this.makeButton(m.cx, area.top + 150, 200, 44, t('prestigeNow') + ' +' + pend + '*', () => this.doPrestige(pend), 'red', 9);
        m.add([b.img, b.txt]);
      }
    }, 0.55);
  }

  doPrestige(pend) {
    STATE.stars += pend;
    STATE.prestiges++;
    STATE.coins = 0;
    STATE.totalEarnedRun = 0;
    STATE.upgrades = {};
    // NOTE: boost, gems, perks, hats and event progress survive a prestige
    STATE.cpsBase = 0;
    this.evoIdx = 0;
    this.applyEvolutionSprite(false);
    SFX.prestige();
    this.flash();
    this.emitterSpark.explode(60, this.capy.x, this.capy.y);
    this.emitterFire.explode(5, this.capy.x, this.capy.y);
    this.closeModal();
    this.updateHud();
    saveState(STATE, true);
    Y.submitScore(STATE.bestScore = Math.max(STATE.bestScore, STATE.totalEarnedAll));
    Y.showInterstitial();
  }

  // ---------------- SETTINGS ----------------
  openSettings() {
    this.openModal('settings', (m, area) => {
      let y = area.top + 16;
      const mkToggle = (labelKey, get, set) => {
        m.add(this.add.text(area.left + 10, y, t(labelKey), { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffffff' }));
        const b = this.makeButton(area.right - 50, y + 6, 80, 30, get() ? t('on') : t('off'), (img, txt) => {
          set(!get());
          txt.setText(get() ? t('on') : t('off'));
          SFX.ui();
        }, 'blue', 8);
        m.add([b.img, b.txt]);
        y += 44;
      };
      mkToggle('sound', () => STATE.settings.sound, v => { STATE.settings.sound = v; setSound(v); saveState(STATE, true); });
      mkToggle('music', () => STATE.settings.music, v => { STATE.settings.music = v; setMusic(v); if (v) startMusic(); saveState(STATE, true); });
      m.add(this.add.text(area.left + 10, y, t('language'), { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffffff' }));
      y += 26;
      LANGS.forEach((lng, i) => {
        const x = area.left + 30 + i * 70;
        const active = getLanguage() === lng;
        const b = this.makeButton(x, y, 60, 28, lng.toUpperCase(), () => {
          STATE.settings.lang = lng;
          setLanguage(lng);
          saveState(STATE, true);
          this.layout();
          this.closeModal();
          this.openSettings();
        }, active ? 'orange' : 'blue', 8);
        m.add([b.img, b.txt]);
      });
      y += 40;
      m.add(this.add.text(area.left + 10, y, `${t('bestScore')}: ${fmt(STATE.bestScore)}`, { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }));
      y += 20;
      m.add(this.add.text(area.left + 10, y, `v1.4 | Yandex Games`, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#5f8fbf' }));
    }, 0.6);
  }

  // ---------------- OFFLINE ----------------
  checkOffline() {
    const now = Date.now();
    const ob = offlineBonus(STATE);
    const elapsed = Math.min(ob.cap, (now - (STATE.lastSeen || now)) / 1000);
    if (elapsed > 60 && cpsBase() > 0) {
      const gain = Math.ceil(cpsBase() * starMultiplier(STATE.stars) * elapsed * ob.rate);
      this.time.delayedCall(600, () => {
        this.openModal('offlineTitle', (m, area) => {
          m.add(this.add.text(m.cx, area.top + 20, t('offlineDesc'), { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffffff', align: 'center', wordWrap: { width: area.width } }).setOrigin(0.5, 0));
          m.add(this.add.text(m.cx, area.top + 70, '+' + fmt(gain), { fontFamily: FONT, fontSize: '16px', padding: { x: 2, y: 6 }, color: '#ffd24a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5));
          m.add(this.add.text(m.cx, area.top + 100, fmtTime(elapsed), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }).setOrigin(0.5));
          const b = this.makeButton(m.cx, area.top + 150, 180, 44, t('offlineClaim'), () => {
            STATE.coins += gain;
            STATE.totalEarnedRun += gain;
            STATE.totalEarnedAll += gain;
            SFX.coin();
            this.checkEvolution();
            this.updateHud();
            this.closeModal();
            saveState(STATE, true);
          }, 'green', 9);
          m.add([b.img, b.txt]);
        }, 0.5);
      });
    }
  }
}

// ================================================================
const config = {
  type: Phaser.AUTO,
  parent: 'game',
  backgroundColor: '#4aa0ff',
  pixelArt: true,
  scale: {
    mode: Phaser.Scale.RESIZE,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    width: '100%',
    height: '100%',
  },
  scene: [BootScene, GameScene],
};

async function boot() {
  // SDK init BEFORE game start
  await Y.initSDK();
  // wait for pixel font
  try { await Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 2500))]); } catch (e) {}
  new Phaser.Game(config);
}
boot();

