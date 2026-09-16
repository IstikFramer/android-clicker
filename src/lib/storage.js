const KEY = 'mangverse:favorites'

/** Избранное (id манг) из localStorage */
export function getFavs() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY))
    return Array.isArray(raw) ? raw : []
  } catch {
    return []
  }
}

export function isFav(id) {
  return getFavs().includes(id)
}

/** Возвращает true, если после нажатия манга в избранном */
export function toggleFav(id) {
  const cur = getFavs()
  const next = cur.includes(id) ? cur.filter((x) => x !== id) : [id, ...cur]
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    /* приватный режим и т.п. */
  }
  return next.includes(id)
}
