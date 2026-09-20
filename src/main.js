// ===== CAPYBARA CLICKER — main game (Phaser 3) =====
import Phaser from 'phaser';
import { t, setLanguage, getLanguage, LANGS } from './i18n.js';
import {
  UPGRADES, upgradeCost, EVOLUTIONS, evolutionIndex, pendingStars,
  PRESTIGE_MIN, starMultiplier, dailyReward, BOOST_DURATION, BOOST_MULT,
  OFFLINE_RATE, OFFLINE_CAP_SEC, ACHIEVEMENTS, totalUpgrades, makeQuest, IAP_PRODUCTS,
  GEM_BOOST_COST, GEM_BOOST_DURATION, EXCHANGE_GEMS, EXCHANGE_COINS, DAILY_GEMS_DAY7,
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
  if (now.getMonth() === 11) return land ? 'bgpc_winter' : 'bg_winter'; // festive December
  const h = now.getHours();
  const p = land ? 'bgpc_' : 'bg_';
  if (h >= 20 || h < 6) return p + 'night';
  if ((h >= 6 && h < 8) || (h >= 17 && h < 20)) return p + 'sunset';
  return p + 'day';
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
    for (const b of ['day', 'sunset', 'night', 'winter']) this.load.image('bg_' + b, `assets/backgrounds/bg_${b}.jpg?v=3`);
    for (const b of ['day', 'sunset', 'night', 'winter']) this.load.image('bgpc_' + b, `assets/backgrounds/bgpc_${b}.jpg?v=1`);
    this.load.image('part_coin', 'assets/particles/part_coin.png?v=3');
    this.load.image('part_spark', 'assets/particles/part_spark.png?v=3');
    this.load.image('part_heart', 'assets/particles/part_heart.png?v=3');
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
    this.clouds = [];
    for (let i = 0; i < 3; i++) this.clouds.push(this.add.image(-200, 100, 'cloud').setAlpha(0.92));
    this.mound = this.add.image(W / 2, H * 0.4, 'mound');
    this.capy = this.add.image(W / 2, H * 0.38, 'capy_evo1');
    this.capy.setInteractive({ useHandCursor: true });
    this.capy.on('pointerdown', p => this.onCapyClick(p));
    this.combo = 0; this.lastClickT = 0; this.comboTimer = null;
    this.comboTxt = this.add.text(W / 2, H * 0.2, '', { fontFamily: FONT, fontSize: '12px', padding: { x: 2, y: 4 }, color: '#7dff8a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5).setVisible(false);

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

    // quests init
    if (!STATE.quests || STATE.quests.length === 0) {
      STATE.quests = [makeQuest(this.questCtx(), 0), makeQuest(this.questCtx(), 1), makeQuest(this.questCtx(), 2)];
    }

    this.layout();
    this.startCapyIdle();
    this.scale.on('resize', () => { this.closeModal(); this.layout(); });

    // ---- income tick ----
    this.time.addEvent({ delay: 100, loop: true, callback: () => {
      const gain = cps() / 10;
      if (gain > 0) this.earn(gain, false);
      this.updateHud();
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
  U(obj) { this.ui.push(obj); return obj; }

  clearUI() {
    for (const o of this.ui) { if (o && o.destroy) o.destroy(); }
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
    this.applyEvolutionSprite(false);

    // ---- top HUD ----
    const hudH = 96;
    this.U(this.add.rectangle(cx, hudH / 2, CW, hudH, 0x123a6a, 1));
    this.U(this.add.rectangle(cx, hudH - 2, CW, 4, 0x3a7ac9, 1));
    this.txtCoins = this.U(this.add.text(cx, 26, '0', { fontFamily: FONT, fontSize: '20px', padding: { x: 2, y: 7 }, color: '#ffd24a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5));
    this.coinIcon = this.U(this.add.image(0, 26, 'coin_gold').setDisplaySize(24, 24));
    this.txtCps = this.U(this.add.text(cx, 56, '', { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#bfe3ff' }).setOrigin(0.5));
    this.txtClick = this.U(this.add.text(cx, 74, '', { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#ffe9b0' }).setOrigin(0.5));
    this.txtStars = this.U(this.add.text(cx + CW / 2 - 10, 12, '', { fontFamily: FONT, fontSize: '10px', padding: { x: 2, y: 4 }, color: '#ffd24a', stroke: '#000', strokeThickness: 3 }).setOrigin(1, 0));
    this.txtGems = this.U(this.add.text(cx + CW / 2 - 10, 46, '', { fontFamily: FONT, fontSize: '10px', padding: { x: 2, y: 4 }, color: '#7df9ff', stroke: '#000', strokeThickness: 3 }).setOrigin(1, 0.5));
    this.gemIcon = this.U(this.add.image(0, 46, 'icon_gem').setDisplaySize(22, 22));
    const dz = this.U(this.add.zone(cx + CW / 2 - 50, 32, 100, 52).setInteractive({ useHandCursor: true }));
    dz.on('pointerdown', () => { SFX.ui(); this.openDonate(); });

    // ---- bottom bar ----
    const barH = 64;
    this.U(this.add.rectangle(cx, H - barH / 2, CW, barH, 0x123a6a, 1));
    this.U(this.add.rectangle(cx, H - barH + 2, CW, 4, 0x3a7ac9, 1));
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
      this.U(this.add.circle(x, y - 8, bw * 0.34, 0x0d2c55, 1));
      const img = this.U(this.add.image(x, y - 8, b.icon).setDisplaySize(bw * 0.56, bw * 0.56));
      const lbl = this.U(this.add.text(x, y + 20, t('tabs')[b.key], { fontFamily: FONT, fontSize: '6px', padding: { x: 2, y: 3 }, color: '#bfe3ff' }).setOrigin(0.5));
      zone.on('pointerdown', () => { SFX.ui(); b.cb(); const s0 = img.scaleX; this.tweens.killTweensOf(img); img.setScale(s0); this.tweens.add({ targets: img, scaleX: s0 * 0.85, scaleY: s0 * 0.85, duration: 90, yoyo: true }); });
      this['bar_' + b.key] = { zone, img, lbl, x, y };
    });

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
    if (this.txtGems) {
      this.txtGems.setText(fmt(STATE.gems || 0));
      if (this.gemIcon) this.gemIcon.setPosition(this.txtGems.x - this.txtGems.width - 16, 46);
    }
    // badges
    if (this.bar_daily) {
      const canDaily = this.canClaimDaily();
      this.dailyBadge.setPosition(this.bar_daily.x + 22, this.bar_daily.y - 26).setVisible(canDaily);
      const pend = pendingStars(STATE.totalEarnedRun);
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
    const crit = Math.random() < 0.05;
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
    if (this.combo >= 5) this.comboTxt.setVisible(true).setText(t('combo') + ' x' + this.combo);
    if (this.combo > 0 && this.combo % 25 === 0) this.emitterHeart.explode(8, this.capy.x, this.capy.y);
    // floating text
    const ft = this.add.text(p.x || this.capy.x, (p.y || this.capy.y) - 30, (crit ? t('crit') + ' +' : '+') + fmt(gain), { fontFamily: FONT, fontSize: crit ? '18px' : '12px', color: crit ? '#ff6a3d' : '#ffd24a', stroke: '#000', strokeThickness: crit ? 5 : 3, padding: { x: 2, y: crit ? 6 : 4 } }).setOrigin(0.5);
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
    }});
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
    const cb = this.add.image(W / 2 + pw / 2 - 26, H / 2 - ph / 2 + 24, 'part_heart').setDisplaySize(20, 20).setInteractive({ useHandCursor: true }).setTint(0xff2244);
    cb.on('pointerdown', () => { SFX.ui(); this.closeModal(); });
    const closeTxt = this.add.text(W / 2 + pw / 2 - 26, H / 2 - ph / 2 + 44, 'X', { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ff8899' }).setOrigin(0.5);
    const inner = this.add.rectangle(W / 2, H / 2, pw - 10, ph - 10, 0x000000, 0).setStrokeStyle(2, 0x3a7ac9, 0.9);
    const under = this.add.image(W / 2, H / 2 - ph / 2 + 42, 'strip_gold').setDisplaySize(140, 12);
    m.add([dim, panel, inner, title, under, cb, closeTxt]);
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
        const bgRow = this.add.rectangle(m.cx, 0, area.width, rowH, i % 2 ? 0x0d2c55 : 0x14386a, 0.85);
        const accent = this.add.rectangle(area.left + 2, 0, 4, rowH - 10, 0xffd24a, 0.9);
        const icon = this.add.image(area.left + 26, 0, u.icon).setDisplaySize(40, 40);
        const owned = STATE.upgrades[u.id] || 0;
        const name = this.add.text(area.left + 54, -14, t('up_' + u.id), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffffff' });
        const desc = this.add.text(area.left + 54, 2, `${t('up_' + u.id + '_d')}  ${t('level')}:${owned}`, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' });
        const cost = upgradeCost(u, owned);
        const btn = this.makeButton(area.right - 52, 0, 84, 34, fmt(cost), null, 'orange', 8);
        btn.img.removeAllListeners('pointerdown');
        btn.img.on('pointerdown', () => this.buyUpgrade(u, btn.txt, desc));
        this.setDisabled(btn, STATE.coins < cost);
        row.add([bgRow, accent, icon, name, desc, btn.img, btn.txt]);
        rows.push({ row, btn, u, y });
        content.add(row);
      });
      this.shopRows = rows;
      let contentH = 48 + UPGRADES.length * (rowH + 6);
      // (IAP moved to the Donate modal)
      // mask for scrolling
      const maskShape = this.add.graphics();
      maskShape.fillStyle(0xffffff).fillRect(area.left - 4, area.top, area.width + 8, area.height);
      content.setMask(maskShape.createGeometryMask());
      maskShape.setVisible(false); // mask Graphics must not render (only define geometry)
      m.add(maskShape); // added (invisible) so it is destroyed together with the modal
      let offsetY = 0;
      const maxY = 0;
      const minY = -(contentH - area.height + 30);
      const applyScroll = () => {
        offsetY = Phaser.Math.Clamp(offsetY, Math.min(minY, 0), maxY);
        content.y = offsetY;
      };
      // drag scroll
      let dragStart = null;
      this.input.on('pointermove', p => {
        if (dragStart !== null && p.isDown) {
          offsetY += p.y - dragStart;
          dragStart = p.y;
          applyScroll();
        }
      });
      this.input.on('pointerup', () => { dragStart = null; });
      const downHandler = p => {
        if (p.x > area.left && p.x < area.right && p.y > area.top && p.y < area.top + area.height) dragStart = p.y;
      };
      this.input.on('pointerdown', downHandler);
      this.modalCleanup = () => {
        this.input.off('pointermove');
        this.input.off('pointerup');
        this.input.off('pointerdown', downHandler);
      };
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
    this.openModal('iap', async (m, area) => {
      m.add(this.add.text(m.cx, area.top + 2, t('iapDesc'), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff', align: 'center', wordWrap: { width: area.width } }).setOrigin(0.5, 0));
      let catalog = [];
      if (Y.hasPayments()) { try { catalog = await Y.getCatalog(); } catch (e) { catalog = []; } }
      if (!this.modal) return;
      const demo = !Y.hasPayments();
      const priceOf = (p) => {
        const found = catalog.find(c => c.id === p.id);
        if (found && found.priceValue) return String(found.priceValue).replace(/ /g, ' ');
        return p.price + ' ₽';
      };
      const rowH = 58;
      IAP_PRODUCTS.forEach((p, j) => {
        const y = area.top + 52 + j * (rowH + 8) + rowH / 2;
        m.add(this.add.rectangle(m.cx, y, area.width, rowH, 0x2a1a5a, 0.9));
        m.add(this.add.rectangle(area.left + 2, y, 4, rowH - 10, 0x7df9ff, 0.9));
        m.add(this.add.image(area.left + 28, y, 'icon_gem').setDisplaySize(38, 38));
        m.add(this.add.text(area.left + 56, y - 8, '+' + fmt(p.gems) + ' ' + t('gems'), { fontFamily: FONT, fontSize: '9px', padding: { x: 2, y: 3 }, color: '#7df9ff' }).setOrigin(0, 0.5));
        const b = this.makeButton(area.right - 52, y, 84, 34, demo ? 'DEMO' : priceOf(p), () => this.buyIAP(p, area.right - 52, y), 'blue', 8);
        m.add([b.img, b.txt]);
      });
      // coin exchange for gems
      const yEx = area.top + 52 + IAP_PRODUCTS.length * (rowH + 8) + 26;
      m.add(this.add.text(m.cx, yEx - 14, t('exchangeD'), { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }).setOrigin(0.5));
      const bEx = this.makeButton(m.cx, yEx + 16, 190, 38, t('exchange'), () => {
        if ((STATE.gems || 0) < EXCHANGE_GEMS) { SFX.error(); this.toast(t('noGems')); return; }
        STATE.gems -= EXCHANGE_GEMS;
        STATE.coins += EXCHANGE_COINS;
        STATE.totalEarnedRun += EXCHANGE_COINS;
        STATE.totalEarnedAll += EXCHANGE_COINS;
        SFX.coin();
        this.emitterCoin.explode(10, m.cx, yEx + 16);
        this.questProgress('coins', EXCHANGE_COINS);
        this.updateHud();
        saveState(STATE, true);
      }, 'green', 9);
      m.add([bEx.img, bEx.txt]);
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

  // ---------------- QUESTS ----------------
  openQuests() {
    this.openModal('quests', (m, area) => {
      STATE.quests.forEach((q, i) => {
        const y = area.top + 30 + i * 92;
        m.add(this.add.rectangle(m.cx, y, area.width, 82, 0x0d2c55, 0.8));
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
          // progress bar
          const frac = Math.min(1, q.progress / q.target);
          m.add(this.add.rectangle(area.right - 55, y + 8, 90, 10, 0x081a33));
          m.add(this.add.rectangle(area.right - 55 - 45 + 45 * frac, y + 8, 90 * frac, 10, 0x7dff8a).setOrigin(0.5, 0.5));
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
        m.add(this.add.rectangle(x, y, cell - 6, cell - 6, claimed ? 0x2f8f4f : 0x0d2c55, 1, cur ? 0xffd24a : 0x000000, cur ? 3 : 0));
        m.add(this.add.text(x, y - 8, String(d + 1), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: cur ? '#ffd24a' : '#9fd0ff' }).setOrigin(0.5));
        m.add(this.add.text(x, y + 10, fmt(dailyReward(d + 1, cpsBase())), { fontFamily: FONT, fontSize: '6px', padding: { x: 2, y: 3 }, color: '#ffffff' }).setOrigin(0.5));
      }
      const chestY = area.top + 72;
      const chest = this.add.image(m.cx, chestY, can ? 'chest_closed' : 'chest_open').setDisplaySize(44, 44);
      m.add(chest);
      const yBtn = area.top + 118;
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
      m.add(this.add.text(m.cx, yBtn + 40, `${t('streak')}: ${STATE.dailyStreak}`, { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#ffd24a' }).setOrigin(0.5));
    }, 0.5);
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
      const bAd = this.makeButton(m.cx, yAd, 220, 40, t('boostAd'), () => {
        Y.showRewarded(() => {
          STATE.boostUntil = Math.max(STATE.boostUntil, Date.now()) + BOOST_DURATION * 1000;
          SFX.daily();
          this.updateHud();
          saveState(STATE, true);
          this.closeModal();
          this.openBoost();
        });
      }, 'green', 8);
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
        m.add(this.add.text(m.cx, area.top + 140, t('prestigeNeed') + ': ' + fmt(PRESTIGE_MIN), { fontFamily: FONT, fontSize: '8px', padding: { x: 2, y: 3 }, color: '#9fd0ff' }).setOrigin(0.5));
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
    STATE.boostUntil = 0;
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
      m.add(this.add.text(area.left + 10, y, `v1.3 | Yandex Games`, { fontFamily: FONT, fontSize: '7px', padding: { x: 2, y: 3 }, color: '#5f8fbf' }));
    }, 0.6);
  }

  // ---------------- OFFLINE ----------------
  checkOffline() {
    const now = Date.now();
    const elapsed = Math.min(OFFLINE_CAP_SEC, (now - (STATE.lastSeen || now)) / 1000);
    if (elapsed > 60 && cpsBase() > 0) {
      const gain = Math.ceil(cpsBase() * starMultiplier(STATE.stars) * elapsed * OFFLINE_RATE);
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

