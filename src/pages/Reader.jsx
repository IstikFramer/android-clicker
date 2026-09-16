import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getManga } from '../data/manga.js'
import { pageArt, hashStr } from '../lib/pages.js'
import { fmtDate } from '../lib/utils.js'
import NotFound from './NotFound.jsx'

export default function Reader() {
  const { id, chapter } = useParams()
  const navigate = useNavigate()
  const m = getManga(id)
  const ch = m ? m.chapters.find((c) => c.number === Number(chapter)) : null
  const total = m ? m.chapters.length : 0
  const [idx, setIdx] = useState(0)

  const pages = useMemo(() => {
    if (!m || !ch) return []
    if (Array.isArray(ch.pages)) return ch.pages
    return Array.from({ length: ch.pages }, (_, i) =>
      pageArt({ index: i + 1, total: ch.pages, title: m.title, seed: hashStr(m.id) }),
    )
  }, [m, ch])

  useEffect(() => {
    setIdx(0)
  }, [id, chapter])

  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [idx, chapter, id])

  const prev = () => {
    if (idx > 0) setIdx(idx - 1)
    else if (ch && ch.number > 1) navigate(`/reader/${m.id}/${ch.number - 1}`)
    else if (m) navigate(`/manga/${m.id}`)
  }

  const next = () => {
    if (idx < pages.length - 1) setIdx(idx + 1)
    else if (ch && ch.number < total) navigate(`/reader/${m.id}/${ch.number + 1}`)
    else if (m) navigate(`/manga/${m.id}`)
  }

  useEffect(() => {
    const h = (e) => {
      if (e.key === 'ArrowRight') next()
      else if (e.key === 'ArrowLeft') prev()
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  })

  if (!m || !ch) return <NotFound />

  const progress = ((idx + 1) / pages.length) * 100

  return (
    <div className="container">
      <div className="reader-top">
        <Link to={`/manga/${m.id}`} className="reader-back">
          ← {m.title}
        </Link>
        <div className="reader-title">
          Глава {ch.number} · {ch.title} <span>({fmtDate(ch.date)})</span>
        </div>
        <select
          className="select"
          value={ch.number}
          onChange={(e) => navigate(`/reader/${m.id}/${e.target.value}`)}
          aria-label="Выбор главы"
        >
          {[...m.chapters].reverse().map((c) => (
            <option key={c.number} value={c.number}>
              Глава {c.number}
            </option>
          ))}
        </select>
      </div>

      <div className="reader-stage">
        <div className="reader-page">
          <img key={idx} src={pages[idx]} alt={`Страница ${idx + 1} из ${pages.length}`} />
        </div>
        <div className="chapter-nav">
          {ch.number > 1 ? (
            <Link to={`/reader/${m.id}/${ch.number - 1}`} className="btn btn-ghost btn-sm">
              ← Глава {ch.number - 1}
            </Link>
          ) : (
            <span />
          )}
          {ch.number < total ? (
            <Link to={`/reader/${m.id}/${ch.number + 1}`} className="btn btn-ghost btn-sm">
              Глава {ch.number + 1} →
            </Link>
          ) : (
            <Link to={`/manga/${m.id}`} className="btn btn-ghost btn-sm">
              К манге
            </Link>
          )}
        </div>
      </div>

      <div className="reader-bar">
        <button className="btn btn-ghost btn-sm" onClick={prev}>
          ← Назад
        </button>
        <div className="progress">
          <i style={{ width: `${progress}%` }} />
        </div>
        <span className="page-ind">
          {idx + 1} / {pages.length}
        </span>
        <button className="btn btn-primary btn-sm" onClick={next}>
          Далее →
        </button>
      </div>
    </div>
  )
}
