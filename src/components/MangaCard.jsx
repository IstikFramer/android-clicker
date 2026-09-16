import { Link } from 'react-router-dom'
import CoverArt from './CoverArt.jsx'

export default function MangaCard({ m }) {
  return (
    <Link className="manga-card" to={`/manga/${m.id}`}>
      <div className="cover-wrap">
        <CoverArt m={m} />
        <span className="chip-rating">★ {m.rating.toFixed(1)}</span>
        <span className={`chip-status ${m.status}`}>
          {m.status === 'ongoing' ? 'Онгоинг' : 'Завершена'}
        </span>
      </div>
      <div className="manga-card-body">
        <h3>{m.title}</h3>
        <p>{m.genres.slice(0, 3).join(' · ')}</p>
      </div>
    </Link>
  )
}
