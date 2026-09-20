// ===== Yandex Games SDK v2 wrapper: every call try/catch with localStorage fallback =====
import { INTERSTITIAL_COOLDOWN } from './config.js';

let ysdk = null;
let player = null;
let payments = null;
let lastInterstitial = 0;
let adOpen = false;

export function isAdOpen() { return adOpen; }

export async function initSDK() {
  try {
    if (typeof YaGames === 'undefined') return null;
    ysdk = await Promise.race([
      YaGames.init(),
      new Promise((_, rej) => setTimeout(() => rej(new Error('sdk timeout')), 5000)),
    ]);
    try {
      player = await ysdk.getPlayer({ scopes: false });
    } catch (e) { player = null; }
    try {
      payments = await ysdk.getPayments();
    } catch (e) { payments = null; }
    return ysdk;
  } catch (e) {
    ysdk = null;
    return null;
  }
}

export function getSDK() { return ysdk; }
export function hasPayments() { return !!payments; }

export function getLang(fallback) {
  try {
    if (ysdk && ysdk.environment && ysdk.environment.i18n) {
      return ysdk.environment.i18n.lang || fallback;
    }
  } catch (e) { /* ignore */ }
  return fallback || 'ru';
}

export function gameplayStart() {
  try { ysdk && ysdk.features && ysdk.features.LoadingAPI && ysdk.features.LoadingAPI.ready(); } catch (e) {}
  try { ysdk && ysdk.gameplayStart && ysdk.gameplayStart(); } catch (e) {}
}

export function gameplayStop() {
  try { ysdk && ysdk.gameplayStop && ysdk.gameplayStop(); } catch (e) {}
}

export function showInterstitial() {
  try {
    if (!ysdk) return;
    const now = Date.now() / 1000;
    if (now - lastInterstitial < INTERSTITIAL_COOLDOWN) return;
    lastInterstitial = now;
    adOpen = true;
    gameplayStop();
    ysdk.adv.showFullscreenAdv({
      callbacks: {
        onClose: () => { adOpen = false; gameplayStart(); },
        onError: () => { adOpen = false; gameplayStart(); },
      },
    });
  } catch (e) { adOpen = false; }
}

// Rewarded: only from a player-initiated button
export function showRewarded(onReward) {
  try {
    if (!ysdk) { onReward && onReward(); return; } // offline fallback: grant anyway in dev
    adOpen = true;
    gameplayStop();
    let rewarded = false;
    ysdk.adv.showRewardedVideo({
      callbacks: {
        onRewarded: () => { rewarded = true; onReward && onReward(); },
        onClose: () => { adOpen = false; gameplayStart(); },
        onError: () => { adOpen = false; gameplayStart(); },
      },
    });
  } catch (e) {
    adOpen = false;
    onReward && onReward();
  }
}

export async function submitScore(score) {
  try {
    if (!ysdk) return;
    const lb = await ysdk.getLeaderboards();
    await lb.setLeaderboardScore('totalCoins', Math.floor(score));
  } catch (e) { /* ignore */ }
}

// Cloud saves with localStorage fallback handled by caller
export async function cloudSave(data) {
  try {
    if (!player) return false;
    await player.setData(data, true);
    return true;
  } catch (e) { return false; }
}

export async function cloudLoad() {
  try {
    if (!player) return null;
    const data = await player.getData();
    return data && Object.keys(data).length ? data : null;
  } catch (e) { return null; }
}

export async function getCatalog() {
  try {
    if (!payments) return [];
    return await payments.getCatalog();
  } catch (e) { return []; }
}

export async function purchase(id) {
  try {
    if (!payments) return null;
    const products = await payments.getCatalog();
    const product = products.find(p => p.id === id);
    if (!product) return null;
    const res = await payments.purchase({ id });
    await payments.consumePurchase(res.purchaseData.purchaseToken);
    return product;
  } catch (e) { return null; }
}

export function onVisibility(cb) {
  document.addEventListener('visibilitychange', () => cb(document.hidden));
}
