// ===== Save system: localStorage + Yandex Cloud Saves =====
import { SAVE_KEY } from './config.js';
import { cloudSave, cloudLoad } from './yandex.js';

export function defaultState() {
  return {
    coins: 0,
    totalEarnedRun: 0,
    totalEarnedAll: 0,
    totalClicks: 0,
    upgrades: {},
    stars: 0,
    prestiges: 0,
    maxEvolution: 0,
    dailyLast: 0,      // last claim day timestamp (start of day)
    dailyStreak: 0,
    dailyTotal: 0,
    achievements: [],
    quests: [],
    questSeed: 0,
    settings: { sound: true, music: true, lang: null },
    lastSeen: Date.now(),
    boostUntil: 0,
    gems: 0,
    lastAdAt: 0,
    perks: {},
    hats: { owned: ['none'], active: 'none' },
    event: null,
    bestScore: 0,
  };
}

function localSave(state) {
  try {
    localStorage.setItem(SAVE_KEY, JSON.stringify({ t: Date.now(), s: state }));
  } catch (e) { /* ignore */ }
}

function localLoad() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    return obj && obj.s ? obj : null;
  } catch (e) { return null; }
}

export async function loadState() {
  const local = localLoad();
  let cloud = null;
  try { cloud = await cloudLoad(); } catch (e) { cloud = null; }
  let chosen = null;
  if (local && cloud && cloud.t && local.t) {
    chosen = cloud.t > local.t ? cloud : local;
  } else {
    chosen = cloud || local;
  }
  const state = Object.assign(defaultState(), chosen ? chosen.s : {});
  state.settings = Object.assign({ sound: true, music: true, lang: null }, state.settings || {});
  state.upgrades = state.upgrades || {};
  state.perks = state.perks || {};
  state.hats = Object.assign({ owned: ['none'], active: 'none' }, state.hats || {});
  if (!state.hats.owned.includes('none')) state.hats.owned.push('none');
  return { state, savedAt: chosen ? (chosen.t || Date.now()) : Date.now() };
}

let saveTimer = null;
export function saveState(state, alsoCloud = false) {
  state.lastSeen = Date.now();
  localSave(state);
  if (alsoCloud) {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      cloudSave({ t: Date.now(), s: state });
    }, 800);
  }
}
