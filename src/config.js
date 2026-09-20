// ===== Game balance & data =====

export const UPGRADES = [
  { id: 'orange',  icon: 'icon_orange',   type: 'click', value: 1,   baseCost: 15 },
  { id: 'grass',   icon: 'icon_grass',    type: 'cps',   value: 1,   baseCost: 25 },
  { id: 'duck',    icon: 'icon_duck',     type: 'cps',   value: 5,   baseCost: 300 },
  { id: 'friend',  icon: 'icon_friend',   type: 'cps',   value: 20,  baseCost: 1800 },
  { id: 'spring',  icon: 'icon_spring',   type: 'cps',   value: 75,  baseCost: 10000 },
  { id: 'orchard', icon: 'icon_orchard',  type: 'cps',   value: 300, baseCost: 75000 },
  { id: 'leaf',    icon: 'icon_leafgold', type: 'mult',  value: 2,   baseCost: 5000, growth: 4 },
];

// cost = baseCost * growth^owned  (spec: 1.15)
export function upgradeCost(u, owned) {
  const g = u.growth || 1.15;
  return Math.ceil(u.baseCost * Math.pow(g, owned));
}

// Evolution stages by TOTAL earned coins (this run)
export const EVOLUTIONS = [
  { total: 0,        sprite: 'capy_evo1' },
  { total: 2000,     sprite: 'capy_evo2' },
  { total: 80000,    sprite: 'capy_evo3' },
  { total: 700000,   sprite: 'capy_evo4' },
  { total: 8000000,  sprite: 'capy_evo5' },
];

export function evolutionIndex(totalEarned) {
  let idx = 0;
  for (let i = 0; i < EVOLUTIONS.length; i++) {
    if (totalEarned >= EVOLUTIONS[i].total) idx = i;
  }
  return idx;
}

// Prestige: 1st at 1M, 2nd at 3M, 3rd at 6M, 4th at 10M ... (triangular * 1e6)
export function prestigeThreshold(n) {
  return 1e6 * n * (n + 1) / 2;
}
export const PRESTIGE_MIN = 1e6; // first prestige, for hints
export function nextPrestigeNeed(prestiges) {
  return prestigeThreshold((prestiges || 0) + 1);
}
// stars earned = how many thresholds you cleared past your current prestige count
export function pendingStars(totalRun, prestiges) {
  let k = 0;
  while (totalRun >= prestigeThreshold((prestiges || 0) + k + 1)) k++;
  return k;
}
// each star +30%, and the bonus itself grows (quadratic) so late prestiges matter
export function starMultiplier(stars) {
  return 1 + stars * 0.30 + 0.015 * stars * stars;
}

// Daily streak: 7-day cycle, reward grows
export function dailyReward(day, cps) {
  const base = Math.max(200, cps * 120);
  return Math.ceil(base * day);
}

// Boost (rewarded ad): x2 income for 120s
export const BOOST_DURATION = 120;
export const BOOST_MULT = 2;

// Offline income: 50% of cps, capped at 8 hours
export const OFFLINE_RATE = 0.5;
export const OFFLINE_CAP_SEC = 8 * 3600;

// Interstitial cooldown
export const INTERSTITIAL_COOLDOWN = 130; // seconds (spec: 120-150)

export const ACHIEVEMENTS = [
  { id: 'clicks1',    check: s => s.totalClicks >= 100,      reward: 150 },
  { id: 'clicks2',    check: s => s.totalClicks >= 1000,     reward: 2500 },
  { id: 'clicks3',    check: s => s.totalClicks >= 5000,     reward: 25000 },
  { id: 'earn1',      check: s => s.totalEarnedAll >= 1000,     reward: 150 },
  { id: 'earn2',      check: s => s.totalEarnedAll >= 100000,   reward: 10000 },
  { id: 'earn3',      check: s => s.totalEarnedAll >= 10000000, reward: 500000 },
  { id: 'event1',     check: s => (s.event && s.event.pumpkinsTotal >= 100) || false, reward: 20000 },
  { id: 'event2',     check: s => (s.event && s.event.tierClaimed >= 10) || false, reward: 500000 },
  { id: 'ups1',       check: s => totalUpgrades(s) >= 10,    reward: 1000 },
  { id: 'ups2',       check: s => totalUpgrades(s) >= 40,    reward: 25000 },
  { id: 'evo1',       check: s => s.maxEvolution >= 2,       reward: 1500 },
  { id: 'evo2',       check: s => s.maxEvolution >= 4,       reward: 250000 },
  { id: 'evo3',       check: s => s.maxEvolution >= 5,       reward: 2500000 },
  { id: 'prestige1',  check: s => s.prestiges >= 1,          reward: 0 },
  { id: 'daily1',     check: s => s.dailyTotal >= 3,         reward: 1500 },
  { id: 'daily2',     check: s => s.dailyTotal >= 7,         reward: 12000 },
];

export function totalUpgrades(s) {
  return Object.values(s.upgrades).reduce((a, b) => a + b, 0);
}

// Quest generation: cycles through types with scaling targets
export function makeQuest(state, slot) {
  const types = ['clicks', 'coins', 'buy'];
  const type = types[(state.questSeed + slot) % types.length];
  const run = state.totalEarnedAll;
  let target, reward;
  if (type === 'clicks') {
    target = 50 + Math.floor(run / 500) * 25 + slot * 30;
    target = Math.min(target, 5000);
    reward = Math.max(100, Math.ceil(target * (1 + state.cpsBase * 0.1)));
  } else if (type === 'coins') {
    target = Math.max(500, Math.ceil(run * 0.15)) * (slot + 1);
    reward = Math.ceil(target * 0.15);
  } else {
    target = 3 + slot * 2 + Math.floor(state.prestiges);
    target = Math.min(target, 25);
    reward = Math.max(200, Math.ceil((state.cpsBase + 1) * 30 * (slot + 1)));
  }
  return { type, target, reward, progress: 0, done: false, claimed: false };
}

// IAP products: gem packs (Yandex Payments; DEMO grants in preview without SDK)
export const IAP_PRODUCTS = [
  { id: 'gems_small', gems: 10,  price: '29' },
  { id: 'gems_mid',   gems: 60,  price: '199' },
  { id: 'gems_big',   gems: 350, price: '999' },
];

// Rewarded-ad cooldown (anti-abuse): 5 minutes between rewarded videos
export const REWARDED_COOLDOWN = 300;

// Permanent perks (bought with gems, NEVER reset by prestige)
export const PERKS = [
  { id: 'auto',    icon: 'icon_duck', levels: [{ cost: 60, value: 1 }, { cost: 180, value: 3 }, { cost: 450, value: 8 }] },
  { id: 'offline', icon: 'cloud',     levels: [{ cost: 80, value: 1 }, { cost: 200, value: 2 }] },
  { id: 'crit',    icon: 'burst',     levels: [{ cost: 40, value: 5 }, { cost: 90, value: 10 }, { cost: 160, value: 15 }, { cost: 260, value: 20 }, { cost: 400, value: 25 }] },
];
export function perkLevel(s, id) { return (s.perks && s.perks[id]) || 0; }
export function autoClickRate(s) {
  const L = perkLevel(s, 'auto');
  return L > 0 ? PERKS[0].levels[L - 1].value : 0;
}
export function offlineBonus(s) {
  const L = perkLevel(s, 'offline');
  if (L >= 2) return { rate: 1.0, cap: 24 * 3600 };
  if (L === 1) return { rate: 0.75, cap: 16 * 3600 };
  return { rate: OFFLINE_RATE, cap: OFFLINE_CAP_SEC };
}
export function critChance(s) { return 0.05 + perkLevel(s, 'crit') * 0.05; }

// Cosmetics: hats worn by the capybara (permanent)
export const HATS = [
  { id: 'none',    cost: 0 },
  { id: 'pumpkin', cost: 60 },
  { id: 'leaf',    cost: 120 },
  { id: 'beanie',  cost: 200 },
];

// Coin packs: gems -> coins scaled to current CPS
export const COIN_PACKS = [
  { gems: 5,  sec: 600,   min: 1000 },
  { gems: 15, sec: 3600,  min: 10000 },
  { gems: 40, sec: 14400, min: 100000 },
];
export function packCoins(p, cpsVal) {
  return Math.max(p.min, Math.ceil(cpsVal * p.sec));
}

// Gem sinks: x2 boost + coin exchange + day-7 drip
export const GEM_BOOST_COST = 15;
export const GEM_BOOST_DURATION = 300; // seconds
export const EXCHANGE_GEMS = 5;
export const EXCHANGE_COINS = 1000;
export const DAILY_GEMS_DAY7 = 5;

export const SAVE_KEY = 'capy_clicker_save_v1';

// ================= AUTUMN EVENT =================
// Autumn event: Sep 1 - Dec 1 of the CURRENT year (so it is live every autumn)
export const EVENT = { id: 'autumn' + new Date().getUTCFullYear() };
export function eventWindow(now = Date.now()) {
  const y = new Date(now).getUTCFullYear();
  return { start: Date.UTC(y, 8, 1), end: Date.UTC(y, 11, 1) };
}
export function eventActive(now = Date.now()) {
  const w = eventWindow(now);
  return now >= w.start && now < w.end;
}
export function eventDaysLeft(now = Date.now()) {
  const w = eventWindow(now);
  return Math.max(0, Math.ceil((w.end - now) / 86400000));
}

// Battle pass: 10 tiers. need = cumulative pumpkins. rewards: coins = seconds of CPS, gems, hat, boost minutes
export const PASS_TIERS = [
  { need: 20,   free: { sec: 60 },        prem: { sec: 300 } },
  { need: 60,   free: { sec: 180 },       prem: { sec: 900 } },
  { need: 130,  free: { gems: 5 },        prem: { gems: 10 } },
  { need: 240,  free: { sec: 600 },       prem: { sec: 1800 } },
  { need: 400,  free: { sec: 1200 },      prem: { hat: 'leaf' } },
  { need: 620,  free: { gems: 10 },       prem: { gems: 25 } },
  { need: 900,  free: { sec: 2400 },      prem: { sec: 5400 } },
  { need: 1250, free: { sec: 3600 },      prem: { boost: 10 } },
  { need: 1700, free: { gems: 20 },       prem: { gems: 60 } },
  { need: 2300, free: { sec: 7200 },      prem: { hat: 'pumpkin' } },
];
export const PASS_PREMIUM_COST = 100;

// Daily event tasks (reset once per day)
export const EVENT_TASKS = [
  { id: 'pumpkins', target: 25,  rewardP: 15, sec: 300 },
  { id: 'clicks',   target: 400, rewardP: 20, sec: 300 },
  { id: 'buy',      target: 8,   rewardP: 15, sec: 300 },
];
export function dayKey(now = Date.now()) {
  const d = new Date(now);
  return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
}
export function makeEventTasks() {
  return EVENT_TASKS.map(x => ({ id: x.id, target: x.target, progress: 0, claimed: false }));
}
export function passTierReached(pumpkins) {
  let n = 0;
  for (const t of PASS_TIERS) if (pumpkins >= t.need) n++;
  return n;
}
