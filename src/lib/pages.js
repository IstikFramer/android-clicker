/* Генератор placeholder-страницы (SVG data-URI).
   Используется, пока в данных главы нет реальных url страниц. */

function mulberry32(a) {
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function hashStr(s) {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0
  return Math.abs(h)
}

const LAYOUTS = [
  [[1], [2], [1]],
  [[2], [1], [2]],
  [[1], [1], [2]],
  [[2], [2], [1]],
]
const WEIGHTS = [0.44, 0.27, 0.29]

export function pageArt({ index, total, title, seed = 0 }) {
  const rnd = mulberry32(seed * 7919 + index * 104729 + 17)
  const W = 800
  const H = 1180
  const P = 54
  const gap = 26
  const layout = LAYOUTS[Math.floor(rnd() * LAYOUTS.length)]
  const innerH = H - P * 2 - 70

  const panels = []
  let y = P
  layout.forEach((row, ri) => {
    const rh = Math.floor(innerH * WEIGHTS[ri])
    if (row.length === 1) {
      panels.push({ x: P, y, w: W - P * 2, h: rh })
    } else {
      const cw = (W - P * 2 - gap) / 2
      panels.push({ x: P, y, w: cw, h: rh })
      panels.push({ x: P + cw + gap, y, w: cw, h: rh })
    }
    y += rh + gap
  })

  const parts = []
  parts.push('<rect width="800" height="1180" fill="url(#bg)"/>')

  const letter = (title || 'M').trim().charAt(0).toUpperCase()
  parts.push(
    `<text x="${W / 2}" y="${H / 2 + 130}" font-family="Arial, sans-serif" font-size="560" font-weight="900" fill="rgba(167,139,250,0.06)" text-anchor="middle">${letter}</text>`,
  )

  for (const p of panels) {
    parts.push(
      `<rect x="${p.x}" y="${p.y}" width="${p.w.toFixed(0)}" height="${p.h}" rx="18" fill="url(#panel)" stroke="rgba(167,139,250,0.28)" stroke-width="1.5"/>`,
    )
    // «текстовые» строки внутри панели
    const lines = 3 + Math.floor(rnd() * 4)
    for (let li = 0; li < lines; li++) {
      const ly = p.y + 46 + li * 30
      if (ly > p.y + p.h - 34) break
      const lw = (p.w - 70) * (0.45 + rnd() * 0.5)
      parts.push(
        `<rect x="${p.x + 34}" y="${ly}" width="${lw.toFixed(0)}" height="9" rx="4.5" fill="rgba(196,181,253,0.14)"/>`,
      )
    }
    // иногда «реплика»
    if (rnd() > 0.45) {
      const ex = p.x + 40 + rnd() * Math.max(p.w - 190, 60)
      const ey = p.y + p.h - 70 - rnd() * 30
      parts.push(
        `<ellipse cx="${ex.toFixed(0)}" cy="${ey.toFixed(0)}" rx="62" ry="34" fill="rgba(12,7,22,0.65)" stroke="rgba(196,181,253,0.3)" stroke-width="1.5"/>`,
        `<rect x="${(ex - 38).toFixed(0)}" y="${(ey - 4).toFixed(0)}" width="76" height="8" rx="4" fill="rgba(196,181,253,0.25)"/>`,
      )
    }
  }

  parts.push(`<rect x="0" y="${H - 70}" width="${W}" height="70" fill="rgba(7,4,13,0.85)"/>`)
  parts.push(`<text x="${P}" y="${H - 28}" font-family="Arial" font-size="20" fill="rgba(185,174,205,0.8)">MANGVERSE</text>`)
  parts.push(
    `<text x="${W - P}" y="${H - 28}" font-family="Arial" font-size="20" fill="rgba(185,174,205,0.8)" text-anchor="end">Стр. ${index} / ${total}</text>`,
  )

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1a1030"/>
      <stop offset="0.55" stop-color="#120a22"/>
      <stop offset="1" stop-color="#0a0614"/>
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#241640"/>
      <stop offset="1" stop-color="#150d28"/>
    </linearGradient>
  </defs>
  ${parts.join('\n  ')}
</svg>`

  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg)
}
