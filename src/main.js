// ===== CAPYBARA CLICKER — main game (Phaser 3) =====
import Phaser from 'phaser';
import { t, setLanguage, getLanguage, LANGS } from './i18n.js';
import {
  UPGRADES, upgradeCost, EVOLUTIONS, evolutionIndex, pendingStars,
  PRESTIGE_MIN, starMultiplier, dailyReward, BOOST_DURATION, BOOST_MULT,
  OFFLINE_RATE, OFFLINE_CAP_SEC, ACHIEVEMENTS, totalUpgrades, makeQuest, IAP_PRODUCTS,
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

function pickBg() {
  const now = new Date();
  if (now.getMonth() === 11) return 'bg_winter'; // festive December
  const h = now.getHours();
  if (h >= 20 || h < 6) return 'bg_night';
  if ((h >= 6 && h < 8) || (h >= 17 && h < 20)) return 'bg_sunset';
  return 'bg_day';
}

// ================================================================
class BootScene extends Phaser.Scene {
  constructor() { super('boot'); }
  create() {
    const W = this.scale.width, H = this.scale.height;
    this.add.rectangle(W / 2, H / 2, W, H, 0x4aa0ff);
    const title = this.add.text(W / 2, H * 0.4, t('title'), { fontFamily: FONT, fontSize: '18px', color: '#ffffff', stroke: '#1a4a8a', strokeThickness: 4, align: 'center' }).setOrigin(0.5);
    const load = this.add.text(W / 2, H * 0.5, t('loading'), { fontFamily: FONT, fontSize: '10px', color: '#ffffff' }).setOrigin(0.5);
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
    for (const b of ['day', 'sunset', 'night', 'winter']) this.load.image('bg_' + b, `assets/backgrounds/bg_${b}.jpg?v=3`);
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
    this.bg = this.add.image(W / 2, H / 2, pickBg());
    this.shadow = this.add.ellipse(W / 2, H * 0.4, 100, 30, 0x0a2a12, 0.3);
    this.capy = this.add.image(W / 2, H * 0.38, 'capy_evo1');
    this.capy.setInteractive({ useHandCursor: true });
    this.capy.on('pointerdown', p => this.onCapyClick(p));

    this.emitterCoin = this.add.particles(0, 0, 'part_coin', {
      speed: { min: 80, max: 220 }, angle: { min: 200, max: 340 },
      gravity: 500, lifespan: 700, scale: { start: 1, end: 0.4 },
      emitting: false,
    });
    this.emitterSpark = this.add.particles(0, 0, 'part_spark', {
      speed: { min: 50, max: 260 }, lifespan: 600, scale: { start: 1.4, end: 0 },
      emitting: false,
    });

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
    this.clearUI();
    this.bg.setScale(Math.max(W / this.bg.width, H / this.bg.height)); // cover: crop, never stretch
    const capySize = Math.min(W * 0.62, H * 0.30);
    this.capy.setPosition(W / 2, H * 0.36).setDisplaySize(capySize, capySize);
    this.capyBaseY = H * 0.36;
    this.capyBaseScaleX = this.capy.scaleX;
    this.capyBaseScaleY = this.capy.scaleY;
    this.shadow.setPosition(W / 2, H * 0.36 + capySize * 0.42).setDisplaySize(capySize * 0.62, capySize * 0.2);
    this.applyEvolutionSprite(false);

    // ---- top HUD ----
    const hudH = 96;
    this.U(this.add.rectangle(W / 2, hudH / 2, W, hudH, 0x123a6a, 1));
    this.U(this.add.rectangle(W / 2, hudH - 2, W, 4, 0x3a7ac9, 1));
    this.txtCoins = this.U(this.add.text(W / 2, 26, '0', { fontFamily: FONT, fontSize: '20px', color: '#ffd24a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5));
    this.coinIcon = this.U(this.add.image(0, 26, 'part_coin').setDisplaySize(22, 22));
    this.txtCps = this.U(this.add.text(W / 2, 56, '', { fontFamily: FONT, fontSize: '9px', color: '#bfe3ff' }).setOrigin(0.5));
    this.txtClick = this.U(this.add.text(W / 2, 74, '', { fontFamily: FONT, fontSize: '9px', color: '#ffe9b0' }).setOrigin(0.5));
    this.txtStars = this.U(this.add.text(W - 10, 12, '', { fontFamily: FONT, fontSize: '10px', color: '#ffd24a', stroke: '#000', strokeThickness: 3 }).setOrigin(1, 0));

    // ---- bottom bar ----
    const barH = 64;
    this.U(this.add.rectangle(W / 2, H - barH / 2, W, barH, 0x123a6a, 1));
    this.U(this.add.rectangle(W / 2, H - barH + 2, W, 4, 0x3a7ac9, 1));
    const btns = [
      { key: 'shop', icon: 'icon_orange', cb: () => this.openShop() },
      { key: 'quests', icon: 'icon_grass', cb: () => this.openQuests() },
      { key: 'daily', icon: 'icon_gift', cb: () => this.openDaily() },
      { key: 'boost', icon: 'part_spark', cb: () => this.tryBoost() },
      { key: 'prestige', icon: 'icon_leafgold', cb: () => this.openPrestige() },
      { key: 'settings', icon: 'icon_duck', cb: () => this.openSettings() },
    ];
    const n = btns.length;
    const bw = Math.min(56, (W - 16) / n - 6);
    btns.forEach((b, i) => {
      const x = W / 2 + (i - (n - 1) / 2) * (bw + 8);
      const y = H - barH / 2;
      const zone = this.U(this.add.zone(x, y, bw + 8, barH).setInteractive({ useHandCursor: true }));
      this.U(this.add.circle(x, y - 6, bw * 0.42, 0x0d2c55, 1));
      const img = this.U(this.add.image(x, y - 6, b.icon).setDisplaySize(bw * 0.62, bw * 0.62));
      const lbl = this.U(this.add.text(x, y + 18, t('tabs')[b.key], { fontFamily: FONT, fontSize: '6px', color: '#bfe3ff' }).setOrigin(0.5));
      zone.on('pointerdown', () => { SFX.ui(); b.cb(); });
      this['bar_' + b.key] = { zone, img, lbl, x, y };
    });

    this.dailyBadge = this.U(this.add.circle(0, 0, 6, 0xff4a6a).setVisible(false));
    this.prestigeBadge = this.U(this.add.circle(0, 0, 6, 0xffd24a).setVisible(false));
    this.boostTimer = this.U(this.add.text(0, 0, '', { fontFamily: FONT, fontSize: '8px', color: '#7dff8a', stroke: '#000', strokeThickness: 3 }).setVisible(false));

    this.updateHud();
  }

  updateHud() {
    if (!this.txtCoins) return;
    this.txtCoins.setText(fmt(STATE.coins) + ' ' + t('coins'));
    if (this.coinIcon) this.coinIcon.setPosition(this.scale.width / 2 - this.txtCoins.width / 2 - 24, 26);
    this.txtCps.setText(fmt(cps()) + ' ' + t('perSec'));
    this.txtClick.setText('+' + fmt(clickPower()) + ' ' + t('perClick'));
    this.txtStars.setText(STATE.stars > 0 ? '*' + STATE.stars : '');
    // badges
    if (this.bar_daily) {
      const canDaily = this.canClaimDaily();
      this.dailyBadge.setPosition(this.bar_daily.x + 22, this.bar_daily.y - 26).setVisible(canDaily);
      const pend = pendingStars(STATE.totalEarnedRun);
      this.prestigeBadge.setPosition(this.bar_prestige.x + 22, this.bar_prestige.y - 26).setVisible(pend > 0);
      const left = (STATE.boostUntil - Date.now()) / 1000;
      if (left > 0) {
        this.boostTimer.setVisible(true).setText(fmtTime(left))
          .setPosition(this.bar_boost.x, this.bar_boost.y - 34);
      } else this.boostTimer.setVisible(false);
    }
  }

  // ---------------- clicks & earn ----------------
  onCapyClick(p) {
    unlockAudio();
    const gain = clickPower();
    STATE.totalClicks++;
    this.earn(gain, true);
    this.questProgress('clicks', 1);
    SFX.click();
    this.capySetHappy(140);
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
    this.emitterCoin.explode(3, this.capy.x, this.capy.y - this.capy.displayHeight * 0.3);
    // floating text
    const ft = this.add.text(p.x || this.capy.x, (p.y || this.capy.y) - 30, '+' + fmt(gain), { fontFamily: FONT, fontSize: '12px', color: '#ffd24a', stroke: '#000', strokeThickness: 3 }).setOrigin(0.5);
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
    const title = this.add.text(W / 2, H / 2 - ph / 2 + 26, t(titleKey), { fontFamily: FONT, fontSize: '13px', color: '#ffd24a', stroke: '#000', strokeThickness: 3 }).setOrigin(0.5);
    // close btn
    const cb = this.add.image(W / 2 + pw / 2 - 26, H / 2 - ph / 2 + 24, 'part_heart').setDisplaySize(20, 20).setInteractive({ useHandCursor: true }).setTint(0xff2244);
    cb.on('pointerdown', () => { SFX.ui(); this.closeModal(); });
    const closeTxt = this.add.text(W / 2 + pw / 2 - 26, H / 2 - ph / 2 + 44, 'X', { fontFamily: FONT, fontSize: '8px', color: '#ff8899' }).setOrigin(0.5);
    const inner = this.add.rectangle(W / 2, H / 2, pw - 10, ph - 10, 0x000000, 0).setStrokeStyle(2, 0x3a7ac9, 0.9);
    const under = this.add.rectangle(W / 2, H / 2 - ph / 2 + 42, 120, 3, 0xffd24a, 1);
    m.add([dim, panel, inner, title, under, cb, closeTxt]);
    this.modal = { container: m, W, H, pw, ph, cx: W / 2, cy: H / 2, add: (o) => { m.add(o); return o; } };
    builder(this.modal, { top: H / 2 - ph / 2 + 60, left: W / 2 - pw / 2 + 14, right: W / 2 + pw / 2 - 14, width: pw - 28, height: ph - 80 });
    return this.modal;
  }

  closeModal() {
    if (this.modal) {
      if (this.modalCleanup) { this.modalCleanup(); this.modalCleanup = null; }
      this.modal.container.destroy();
      this.modal = null;
      Y.gameplayStart();
    }
  }

  makeButton(x, y, w, h, label, cb, style = 'orange', fontSize = 9) {
    const TEX = { orange: 'btn_orange', blue: 'btn_blue', green: 'btn_green', red: 'btn_red' };
    const INK = { orange: '#5a2b0e', blue: '#0e2a5a', green: '#0e4a1a', red: '#5a0e1a' };
    const img = this.add.image(x, y, TEX[style] || TEX.orange).setDisplaySize(w, h).setInteractive({ useHandCursor: true });
    const txt = this.add.text(x, y, label, { fontFamily: FONT, fontSize: fontSize + 'px', color: INK[style] || INK.orange, stroke: '#ffffff', strokeThickness: 0 }).setOrigin(0.5);
    img.on('pointerdown', () => cb && cb(img, txt));
    img.on('pointerover', () => img.setTint(0xffe0c0));
    img.on('pointerout', () => img.clearTint());
    return { img, txt };
  }

  // ---------------- SHOP ----------------
  openShop() {
    this.openModal('shop', async (m, area) => {
      const rows = [];
      const rowH = 56;
      const content = this.add.container(0, 0);
      m.add(content);
      UPGRADES.forEach((u, i) => {
        const y = area.top + 14 + i * (rowH + 6);
        const row = this.add.container(0, y);
        const bgRow = this.add.rectangle(m.cx, 0, area.width, rowH, i % 2 ? 0x0d2c55 : 0x14386a, 0.85);
        const accent = this.add.rectangle(area.left + 2, 0, 4, rowH - 10, 0xffd24a, 0.9);
        const icon = this.add.image(area.left + 26, 0, u.icon).setDisplaySize(40, 40);
        const owned = STATE.upgrades[u.id] || 0;
        const name = this.add.text(area.left + 54, -14, t('up_' + u.id), { fontFamily: FONT, fontSize: '8px', color: '#ffffff' });
        const desc = this.add.text(area.left + 54, 2, `${t('up_' + u.id + '_d')}  ${t('level')}:${owned}`, { fontFamily: FONT, fontSize: '7px', color: '#9fd0ff' });
        const cost = upgradeCost(u, owned);
        const btn = this.makeButton(area.right - 52, 0, 84, 34, fmt(cost), null, 'orange', 8);
        btn.img.removeAllListeners('pointerdown');
        btn.img.on('pointerdown', () => this.buyUpgrade(u, btn.txt, desc));
        row.add([bgRow, accent, icon, name, desc, btn.img, btn.txt]);
        rows.push({ row, btn, u, y });
        content.add(row);
      });
      let contentH = UPGRADES.length * (rowH + 6);
      // ---- IAP (gems) section: real Yandex Payments, or ?demo_pay=1 mock preview ----
      {
        const demoPay = new URLSearchParams(location.search).has('demo_pay') && !Y.hasPayments();
        if (Y.hasPayments() || demoPay) {
          let catalog = [];
          if (Y.hasPayments()) { try { catalog = await Y.getCatalog(); } catch (e) { catalog = []; } }
          if (!this.modal) return; // closed while catalog was loading
          const priceOf = (p) => {
            const found = catalog.find(c => c.id === p.id);
            if (found && found.priceValue) return String(found.priceValue).replace(/\u00A0/g, ' ');
            return p.price + ' \u20BD';
          };
          const y0 = area.top + 14 + contentH + 6;
          content.add(this.add.text(m.cx, y0, t('iap'), { fontFamily: FONT, fontSize: '10px', color: '#7df9ff', stroke: '#000', strokeThickness: 3 }).setOrigin(0.5, 0));
          content.add(this.add.text(m.cx, y0 + 22, t('iapDesc'), { fontFamily: FONT, fontSize: '7px', color: '#9fd0ff', align: 'center', wordWrap: { width: area.width - 20 } }).setOrigin(0.5, 0));
          IAP_PRODUCTS.forEach((p, j) => {
            const y = y0 + 52 + j * (rowH + 6) + rowH / 2;
            const row = this.add.container(0, y);
            const bgRow = this.add.rectangle(m.cx, 0, area.width, rowH, 0x2a1a5a, 0.85);
            const accent = this.add.rectangle(area.left + 2, 0, 4, rowH - 10, 0x7df9ff, 0.9);
            const icon = this.add.image(area.left + 26, 0, 'part_coin').setDisplaySize(36, 36);
            const name = this.add.text(area.left + 54, -10, '+' + fmt(p.coins) + ' ' + t('coins'), { fontFamily: FONT, fontSize: '8px', color: '#ffd24a' });
            const desc = this.add.text(area.left + 54, 6, demoPay ? 'DEMO' : 'YANDEX', { fontFamily: FONT, fontSize: '7px', color: '#9fd0ff' });
            const btn = this.makeButton(area.right - 52, 0, 84, 34, priceOf(p), null, 'blue', 7);
            btn.img.removeAllListeners('pointerdown');
            btn.img.on('pointerdown', () => this.buyIAP(p));
            row.add([bgRow, accent, icon, name, desc, btn.img, btn.txt]);
            content.add(row);
          });
          contentH += 6 + 52 + IAP_PRODUCTS.length * (rowH + 6);
        }
      }
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
    if (txt) txt.setText(fmt(upgradeCost(u, owned + 1)));
    if (desc) desc.setText(`${t('up_' + u.id + '_d')}  ${t('level')}:${owned + 1}`);
    this.updateHud();
    saveState(STATE, true);
  }

  async buyIAP(p) {
    const demoPay = new URLSearchParams(location.search).has('demo_pay') && !Y.hasPayments();
    const grant = () => {
      STATE.coins += p.coins;
      STATE.totalEarnedRun += p.coins;
      STATE.totalEarnedAll += p.coins;
      this.questProgress('coins', p.coins);
      SFX.buy();
      this.toast('+' + fmt(p.coins));
      this.checkEvolution();
      this.updateHud();
      saveState(STATE, true);
    };
    if (demoPay) { grant(); return; } // mock purchase for local preview/testing
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
        m.add(this.add.text(area.left + 10, y - 26, t(typeKey) + ': ' + fmt(q.target), { fontFamily: FONT, fontSize: '8px', color: '#ffffff' }));
        m.add(this.add.text(area.left + 10, y - 6, t('questProgress') + ': ' + fmt(Math.floor(q.progress)) + '/' + fmt(q.target), { fontFamily: FONT, fontSize: '7px', color: '#9fd0ff' }));
        m.add(this.add.text(area.left + 10, y + 12, t('questReward') + ': ' + fmt(q.reward), { fontFamily: FONT, fontSize: '7px', color: '#ffd24a' }));
        if (q.done && !q.claimed) {
          const b = this.makeButton(area.right - 55, y + 8, 90, 30, t('dailyClaim'), () => {
            STATE.coins += q.reward;
            q.claimed = true;
            SFX.coin();
            STATE.questSeed++;
            STATE.quests[i] = makeQuest(this.questCtx(), i);
            this.updateHud();
            this.closeModal();
            this.openQuests();
          }, 'orange', 8);
          m.add([b.img, b.txt]);
        } else if (q.claimed) {
          m.add(this.add.text(area.right - 55, y + 8, t('claimed'), { fontFamily: FONT, fontSize: '7px', color: '#7dff8a' }).setOrigin(0.5));
        } else {
          // progress bar
          const frac = Math.min(1, q.progress / q.target);
          m.add(this.add.rectangle(area.right - 55, y + 8, 90, 10, 0x081a33));
          m.add(this.add.rectangle(area.right - 55 - 45 + 45 * frac, y + 8, 90 * frac, 10, 0x7dff8a).setOrigin(0.5, 0.5));
        }
      });
      // achievements summary
      const yA = area.top + 30 + 3 * 92 + 8;
      m.add(this.add.text(area.left + 10, yA, `${t('achievements')}: ${STATE.achievements.length}/${ACHIEVEMENTS.length}`, { fontFamily: FONT, fontSize: '8px', color: '#ffd24a' }));
      m.add(this.add.text(area.left + 10, yA + 20, `${t('totalClicks')}: ${fmt(STATE.totalClicks)}`, { fontFamily: FONT, fontSize: '7px', color: '#9fd0ff' }));
      m.add(this.add.text(area.left + 10, yA + 36, `${t('totalEarned')}: ${fmt(STATE.totalEarnedAll)}`, { fontFamily: FONT, fontSize: '7px', color: '#9fd0ff' }));
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
        m.add(this.add.text(x, y - 8, String(d + 1), { fontFamily: FONT, fontSize: '8px', color: cur ? '#ffd24a' : '#9fd0ff' }).setOrigin(0.5));
        m.add(this.add.text(x, y + 10, fmt(dailyReward(d + 1, cpsBase())), { fontFamily: FONT, fontSize: '6px', color: '#ffffff' }).setOrigin(0.5));
      }
      const yBtn = area.top + 100;
      if (can) {
        const nextStreak = this.nextStreak();
        const reward = dailyReward(((nextStreak - 1) % 7) + 1, cpsBase());
        const b = this.makeButton(m.cx, yBtn, 180, 44, t('dailyClaim') + ' +' + fmt(reward), () => {
          STATE.coins += reward;
          STATE.dailyLast = today.getTime();
          STATE.dailyStreak = nextStreak;
          STATE.dailyTotal++;
          SFX.daily();
          this.updateHud();
          saveState(STATE, true);
          this.closeModal();
        }, 'green', 9);
        m.add([b.img, b.txt]);
      } else {
        m.add(this.add.text(m.cx, yBtn, t('dailyComeBack'), { fontFamily: FONT, fontSize: '9px', color: '#9fd0ff' }).setOrigin(0.5));
      }
      m.add(this.add.text(m.cx, yBtn + 40, `${t('streak')}: ${STATE.dailyStreak}`, { fontFamily: FONT, fontSize: '8px', color: '#ffd24a' }).setOrigin(0.5));
    }, 0.5);
  }

  nextStreak() {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const yesterday = today.getTime() - 86400000;
    if (STATE.dailyLast === yesterday) return STATE.dailyStreak + 1;
    return 1;
  }

  // ---------------- BOOST (rewarded) ----------------
  tryBoost() {
    if (STATE.boostUntil > Date.now()) { this.toast(t('boostActive')); return; }
    Y.showRewarded(() => {
      STATE.boostUntil = Date.now() + BOOST_DURATION * 1000;
      SFX.daily();
      this.toast(t('boostActive') + ' 2:00');
      this.updateHud();
    });
  }

  // ---------------- PRESTIGE ----------------
  openPrestige() {
    const pend = pendingStars(STATE.totalEarnedRun);
    this.openModal('prestigeTitle', (m, area) => {
      m.add(this.add.text(m.cx, area.top + 20, t('prestigeDesc'), { fontFamily: FONT, fontSize: '8px', color: '#ffffff', align: 'center', wordWrap: { width: area.width } }).setOrigin(0.5, 0));
      m.add(this.add.text(m.cx, area.top + 80, '* ' + STATE.stars + '  (x' + starMultiplier(STATE.stars).toFixed(2) + ')', { fontFamily: FONT, fontSize: '11px', color: '#ffd24a' }).setOrigin(0.5));
      m.add(this.add.text(m.cx, area.top + 110, t('prestigeStars') + ': ' + pend, { fontFamily: FONT, fontSize: '9px', color: pend > 0 ? '#7dff8a' : '#ff8899' }).setOrigin(0.5));
      if (pend <= 0) {
        m.add(this.add.text(m.cx, area.top + 140, t('prestigeNeed') + ': ' + fmt(PRESTIGE_MIN), { fontFamily: FONT, fontSize: '8px', color: '#9fd0ff' }).setOrigin(0.5));
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
        m.add(this.add.text(area.left + 10, y, t(labelKey), { fontFamily: FONT, fontSize: '9px', color: '#ffffff' }));
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
      m.add(this.add.text(area.left + 10, y, t('language'), { fontFamily: FONT, fontSize: '9px', color: '#ffffff' }));
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
      m.add(this.add.text(area.left + 10, y, `${t('bestScore')}: ${fmt(STATE.bestScore)}`, { fontFamily: FONT, fontSize: '8px', color: '#9fd0ff' }));
      y += 20;
      m.add(this.add.text(area.left + 10, y, `v1.1 | Yandex Games`, { fontFamily: FONT, fontSize: '7px', color: '#5f8fbf' }));
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
          m.add(this.add.text(m.cx, area.top + 20, t('offlineDesc'), { fontFamily: FONT, fontSize: '9px', color: '#ffffff', align: 'center', wordWrap: { width: area.width } }).setOrigin(0.5, 0));
          m.add(this.add.text(m.cx, area.top + 70, '+' + fmt(gain), { fontFamily: FONT, fontSize: '16px', color: '#ffd24a', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5));
          m.add(this.add.text(m.cx, area.top + 100, fmtTime(elapsed), { fontFamily: FONT, fontSize: '8px', color: '#9fd0ff' }).setOrigin(0.5));
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

