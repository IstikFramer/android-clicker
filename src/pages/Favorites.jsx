import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { manga } from '../data/manga.js'
import { getFavs } from '../lib/storage.js'
import MangaCard from '../components/MangaCard.jsx'
import Icon from '../components/Icon.jsx'

export default function Favorites() {
  const [favs] = useState(() => getFavs())
  const list = useMemo(
    () => favs.map((id) => manga.find((m) => m.id === id)).filter(Boolean),
    [favs],
  )

  return (
    <div className="container">
      <section className="page-hero">
        <img className="bg" src="/images/bg/catalog.jpg" alt="" />
        <div className="veil" />
        <div className="inner">
          <h1>Моё избранное</h1>
          <p>Хранится локально в этом браузере — без аккаунтов и лишнего.</p>
        </div>
      </section>

      {list.length ? (
        <div className="grid grid-4" style={{ marginTop: 30 }}>
          {list.map((m) => (
            <MangaCard key={m.id} m={m} />
          ))}
        </div>
      ) : (
        <div className="empty">
          <Icon name="star" size={80} />
          <h3>Пока пусто</h3>
          <p>Открой понравившуюся мангу и нажми «В избранное» — она появится здесь.</p>
          <Link to="/catalog" className="btn btn-primary">
            В каталог
          </Link>
        </div>
      )}
    </div>
  )
}
