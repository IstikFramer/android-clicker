import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { manga, GENRES } from '../data/manga.js'
import MangaCard from '../components/MangaCard.jsx'
import Icon from '../components/Icon.jsx'

const SORTS = [
  { id: 'rating', label: 'По рейтингу' },
  { id: 'views', label: 'По просмотрам' },
  { id: 'title', label: 'По названию (А → Я)' },
  { id: 'new', label: 'По новым главам' },
]

export default function Catalog() {
  const [params, setParams] = useSearchParams()
  const genre = params.get('genre') || 'all'
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('rating')
  const [status, setStatus] = useState('all')

  const list = useMemo(() => {
    let r = [...manga]
    if (genre !== 'all') r = r.filter((m) => m.genres.includes(genre))
    if (status !== 'all') r = r.filter((m) => m.status === status)
    const query = q.trim().toLowerCase()
    if (query) {
      r = r.filter(
        (m) =>
          m.title.toLowerCase().includes(query) ||
          m.author.toLowerCase().includes(query) ||
          m.genres.some((g) => g.toLowerCase().includes(query)),
      )
    }
    switch (sort) {
      case 'views':
        r.sort((a, b) => b.views - a.views)
        break
      case 'title':
        r.sort((a, b) => a.title.localeCompare(b.title, 'ru'))
        break
      case 'new':
        r.sort((a, b) =>
          b.chapters[b.chapters.length - 1].date.localeCompare(
            a.chapters[a.chapters.length - 1].date,
          ),
        )
        break
      default:
        r.sort((a, b) => b.rating - a.rating)
    }
    return r
  }, [genre, q, sort, status])

  const setGenre = (g) => setParams(g === 'all' ? {} : { genre: g })

  return (
    <div className="container">
      <section className="page-hero">
        <img className="bg" src="/images/bg/catalog.jpg" alt="" />
        <div className="veil" />
        <div className="inner">
          <h1>Каталог</h1>
          <p>
            Вся вселенная MANGVERSE: {manga.length} манг в тёмных тонах и неоновом свете.
          </p>
        </div>
      </section>

      <div className="filters glass" style={{ marginTop: 26 }}>
        <div className="filter-row">
          <span className="filter-label">Поиск</span>
          <div className="search-big">
            <Icon name="search" size={30} />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Название, автор или жанр…"
              aria-label="Поиск по каталогу"
            />
          </div>
        </div>
        <div className="filter-row">
          <span className="filter-label">Жанр</span>
          <div className="chips">
            <button className={`chip ${genre === 'all' ? 'active' : ''}`} onClick={() => setGenre('all')}>
              Все
            </button>
            {GENRES.map((g) => (
              <button
                key={g}
                className={`chip ${genre === g ? 'active' : ''}`}
                onClick={() => setGenre(g)}
              >
                {g}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-row">
          <span className="filter-label">Сортировка</span>
          <select className="select" value={sort} onChange={(e) => setSort(e.target.value)}>
            {SORTS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
          <span className="filter-label" style={{ minWidth: 'auto' }}>
            Статус
          </span>
          <select className="select" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="all">Все</option>
            <option value="ongoing">Онгоинги</option>
            <option value="done">Завершённые</option>
          </select>
        </div>
      </div>

      <p className="result-count">Найдено: {list.length}</p>
      {list.length ? (
        <div className="grid grid-4">
          {list.map((m) => (
            <MangaCard key={m.id} m={m} />
          ))}
        </div>
      ) : (
        <div className="empty">
          <Icon name="search" size={72} />
          <h3>В темноте ничего не найдено</h3>
          <p>Попробуй другие слова или сбрось фильтры.</p>
          <button
            className="btn btn-ghost"
            onClick={() => {
              setQ('')
              setStatus('all')
              setSort('rating')
              setParams({})
            }}
          >
            Сбросить фильтры
          </button>
        </div>
      )}
    </div>
  )
}
