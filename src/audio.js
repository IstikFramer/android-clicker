// ===== Retro SFX + chiptune music via Web Audio API (no external files, CC0 by construction) =====
let ctx = null;
let soundOn = true;
let musicOn = true;
let musicTimer = null;
let musicStep = 0;

function ac() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    ctx = new AC();
  }
  if (ctx.state === 'suspended') ctx.resume();
  return ctx;
}

function blip(freq, dur, type = 'square', vol = 0.15, slide = 0) {
  if (!soundOn) return;
  try {
    const c = ac();
    const o = c.createOscillator();
    const g = c.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, c.currentTime);
    if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(30, freq + slide), c.currentTime + dur);
    g.gain.setValueAtTime(vol, c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + dur);
    o.connect(g).connect(c.destination);
    o.start();
    o.stop(c.currentTime + dur + 0.02);
  } catch (e) { /* ignore */ }
}

function noise(dur, vol = 0.1) {
  if (!soundOn) return;
  try {
    const c = ac();
    const len = Math.floor(c.sampleRate * dur);
    const buf = c.createBuffer(1, len, c.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
    const src = c.createBufferSource();
    src.buffer = buf;
    const g = c.createGain();
    g.gain.value = vol;
    src.connect(g).connect(c.destination);
    src.start();
  } catch (e) { /* ignore */ }
}

export const SFX = {
  click() {
    blip(500 + Math.random() * 200, 0.07, 'square', 0.08, 300);
  },
  coin() {
    blip(900, 0.06, 'square', 0.06);
    setTimeout(() => blip(1350, 0.09, 'square', 0.06), 55);
  },
  buy() {
    blip(400, 0.08, 'triangle', 0.15, 200);
    setTimeout(() => blip(600, 0.1, 'triangle', 0.15, 300), 70);
    setTimeout(() => blip(800, 0.14, 'square', 0.1, 200), 140);
  },
  error() {
    blip(180, 0.15, 'sawtooth', 0.12, -60);
  },
  evolve() {
    [523, 659, 784, 1047, 1319].forEach((f, i) => setTimeout(() => blip(f, 0.16, 'square', 0.12), i * 90));
    noise(0.4, 0.05);
  },
  prestige() {
    [262, 330, 392, 523, 659, 784, 1047].forEach((f, i) => setTimeout(() => blip(f, 0.2, 'triangle', 0.14), i * 100));
  },
  daily() {
    [659, 784, 988].forEach((f, i) => setTimeout(() => blip(f, 0.12, 'square', 0.1), i * 80));
  },
  quest() {
    [784, 988, 1175].forEach((f, i) => setTimeout(() => blip(f, 0.1, 'square', 0.1), i * 70));
  },
  crit() {
    [880, 1175, 1568].forEach((f, i) => setTimeout(() => blip(f, 0.1, 'square', 0.12), i * 50));
    noise(0.15, 0.08);
  },
  ui() {
    blip(700, 0.05, 'square', 0.06);
  },
};

// ---- tiny chiptune loop ----
const MELODY = [
  523, 0, 659, 0, 784, 0, 659, 0,
  587, 0, 698, 0, 880, 0, 698, 0,
  523, 0, 659, 0, 784, 0, 1047, 0,
  880, 0, 784, 0, 659, 0, 587, 0,
];
const BASS = [131, 0, 131, 0, 147, 0, 147, 0, 131, 0, 131, 0, 165, 0, 147, 0];

function musicNote(freq, dur, type, vol) {
  if (!freq) return;
  try {
    const c = ac();
    const o = c.createOscillator();
    const g = c.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.setValueAtTime(vol, c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + dur);
    o.connect(g).connect(c.destination);
    o.start();
    o.stop(c.currentTime + dur + 0.02);
  } catch (e) { /* ignore */ }
}

export function startMusic() {
  stopMusic();
  if (!musicOn) return;
  musicStep = 0;
  musicTimer = setInterval(() => {
    if (!musicOn || document.hidden) return;
    const step = musicStep % MELODY.length;
    musicNote(MELODY[step], 0.18, 'square', 0.028);
    musicNote(BASS[step % BASS.length], 0.22, 'triangle', 0.05);
    musicStep++;
  }, 190);
}

export function stopMusic() {
  if (musicTimer) clearInterval(musicTimer);
  musicTimer = null;
}

export function setSound(on) { soundOn = !!on; }
export function setMusic(on) {
  musicOn = !!on;
  if (musicOn) startMusic(); else stopMusic();
}
export function unlockAudio() { try { ac(); } catch (e) {} }
