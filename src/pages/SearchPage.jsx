import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { manga } from '../data/manga.js'
import MangaCard from '../components/MangaCard.jsx'
import Icon from '../components/Icon.jsx'

const SUGGESTIONS = ['фантастика', 'фэнтези', 'Ноктюрн', 'сигнал', 'тень']

export default function SearchPage() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') || ''

  const results = useMemo(() => {
    const query = q.trim().toLowerCase()
    if (!query) return []
    return manga.filter(
      (m) =>
        m.title.toLowerCase().includes(query) ||
        m.author.toLowerCase().includes(query) ||
        m.genres.some((g) => g.toLowerCase().includes(query)),
    )
  }, [q])

  const setQ = (v) => setParams(v ? { q: v } : {}, { replace: true })

  return (
    <div className="container">
      <section className="page-hero">
        <img className="bg" src="/images/bg/catalog.jpg" alt="" />
        <div className="veil" />
        <div className="inner">
          <h1>Поиск</h1>
          <p>Название, автор или жанр — во всей вселенной MANGVERSE.</p>
        </div>
      </section>

      <div className="filters glass" style={{ marginTop: 26 }}>
        <div className="search-big">
          <Icon name="search" size={32} />
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Что ищем?"
            aria-label="Поиск"
          />
        </div>
      </div>

      {!q ? (
        <div className="empty" style={{ paddingTop: 40 }}>
          <Icon name="grid" size={72} />
          <h3>Попробуй поискать</h3>
          <div className="chips">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" onClick={() => setQ(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      ) : results.length ? (
        <>
          <p className="result-count">Найдено: {results.length}</p>
          <div className="grid grid-4">
            {results.map((m) => (
              <MangaCard key={m.id} m={m} />
            ))}
          </div>
        </>
      ) : (
        <div className="empty">
          <Icon name="search" size={72} />
          <h3>Ничего не нашлось</h3>
          <p>Проверь написание или попробуй короче.</p>
        </div>
      )}
    </div>
  )
}
