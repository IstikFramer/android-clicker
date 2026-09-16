import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { manga } from '../data/manga.js'
import { fmtViews } from '../lib/utils.js'
import CoverArt from '../components/CoverArt.jsx'

const TABS = [
  { id: 'rating', label: 'По рейтингу' },
  { id: 'views', label: 'По просмотрам' },
]

export default function Rankings() {
  const [tab, setTab] = useState('rating')

  const list = useMemo(() => {
    const r = [...manga]
    if (tab === 'views') r.sort((a, b) => b.views - a.views)
    else r.sort((a, b) => b.rating - a.rating)
    return r
  }, [tab])

  return (
    <div className="container">
      <section className="page-hero">
        <img className="bg" src="/images/bg/catalog.jpg" alt="" />
        <div className="veil" />
        <div className="inner">
          <h1>Ранки</h1>
          <p>Самое яркое во вселенной. Обновляется по мере выгрузки новых манг.</p>
        </div>
      </section>

      <div className="rank-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`chip ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="rank-list">
        {list.map((m, i) => (
          <Link key={m.id} to={`/manga/${m.id}`} className={`rank-row ${i < 3 ? `top${i + 1}` : ''}`}>
            <span className="rank-pos">{i + 1}</span>
            <span className="rank-cover">
              <CoverArt m={m} />
            </span>
            <span className="rank-info">
              <h3>{m.title}</h3>
              <p>
                {m.genres.slice(0, 2).join(' · ')} · {m.status === 'ongoing' ? 'онгоинг' : 'завершена'}
              </p>
            </span>
            <span className="rank-metric">
              {tab === 'views' ? fmtViews(m.views) : `★ ${m.rating.toFixed(1)}`}
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
