// ===== Game balance & data =====

export const UPGRADES = [
  { id: 'orange',  icon: 'icon_orange',   type: 'click', value: 1,   baseCost: 15 },
  { id: 'grass',   icon: 'icon_grass',    type: 'cps',   value: 1,   baseCost: 25 },
  { id: 'duck',    icon: 'icon_duck',     type: 'cps',   value: 5,   baseCost: 250 },
  { id: 'friend',  icon: 'icon_friend',   type: 'cps',   value: 20,  baseCost: 1500 },
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
  { total: 1000,     sprite: 'capy_evo2' },
  { total: 50000,    sprite: 'capy_evo3' },
  { total: 1000000,  sprite: 'capy_evo4' },
  { total: 50000000, sprite: 'capy_evo5' },
];

export function evolutionIndex(totalEarned) {
  let idx = 0;
  for (let i = 0; i < EVOLUTIONS.length; i++) {
    if (totalEarned >= EVOLUTIONS[i].total) idx = i;
  }
  return idx;
}

// Prestige: stars = floor(sqrt(totalRun / 1e6)); each star +25% income
export function pendingStars(totalRun) {
  return Math.floor(Math.sqrt(totalRun / 1e6));
}
export const PRESTIGE_MIN = 1e6;
export function starMultiplier(stars) {
  return 1 + stars * 0.25;
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
  { id: 'clicks1',    check: s => s.totalClicks >= 100,      reward: 500 },
  { id: 'clicks2',    check: s => s.totalClicks >= 1000,     reward: 5000 },
  { id: 'clicks3',    check: s => s.totalClicks >= 10000,    reward: 50000 },
  { id: 'earn1',      check: s => s.totalEarnedAll >= 1000,     reward: 300 },
  { id: 'earn2',      check: s => s.totalEarnedAll >= 100000,   reward: 20000 },
  { id: 'earn3',      check: s => s.totalEarnedAll >= 10000000, reward: 1000000 },
  { id: 'ups1',       check: s => totalUpgrades(s) >= 10,    reward: 2000 },
  { id: 'ups2',       check: s => totalUpgrades(s) >= 50,    reward: 50000 },
  { id: 'evo1',       check: s => s.maxEvolution >= 2,       reward: 5000 },
  { id: 'evo2',       check: s => s.maxEvolution >= 4,       reward: 500000 },
  { id: 'evo3',       check: s => s.maxEvolution >= 5,       reward: 5000000 },
  { id: 'prestige1',  check: s => s.prestiges >= 1,          reward: 0 },
  { id: 'daily1',     check: s => s.dailyTotal >= 3,         reward: 3000 },
  { id: 'daily2',     check: s => s.dailyTotal >= 7,         reward: 25000 },
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
    reward = Math.max(100, Math.ceil(target * (2 + state.cpsBase * 0.1)));
  } else if (type === 'coins') {
    target = Math.max(500, Math.ceil(run * 0.15)) * (slot + 1);
    reward = Math.ceil(target * 0.2);
  } else {
    target = 3 + slot * 2 + Math.floor(state.prestiges);
    target = Math.min(target, 25);
    reward = Math.max(200, Math.ceil((state.cpsBase + 1) * 60 * (slot + 1)));
  }
  return { type, target, reward, progress: 0, done: false, claimed: false };
}

// IAP products (Yandex Payments)
export const IAP_PRODUCTS = [
  { id: 'coins_small', coins: 10000,    price: '29' },
  { id: 'coins_big',   coins: 100000,   price: '199' },
  { id: 'coins_mega',  coins: 1000000,  price: '999' },
];

export const SAVE_KEY = 'capy_clicker_save_v1';
