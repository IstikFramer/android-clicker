/** 248300 → '248K', 1200000 → '1,2M' */
export function fmtViews(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(1).replace('.', ',')}M`
  if (n >= 1e3) return `${Math.round(n / 1e3)}K`
  return String(n)
}

/** Русские множественные формы: plural(5, 'глава', 'главы', 'глав') */
export function plural(n, one, few, many) {
  const m10 = n % 10
  const m100 = n % 100
  if (m10 === 1 && m100 !== 11) return one
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few
  return many
}

/** '2026-09-16' → '16 сентября 2026' */
export function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

/** '2026-09-16' → '16 сент.' */
export function fmtDateShort(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}
