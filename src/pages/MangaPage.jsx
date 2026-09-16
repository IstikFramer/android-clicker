import { Link, useParams } from 'react-router-dom'
import { getManga, manga } from '../data/manga.js'
import { fmtViews, fmtDate, plural } from '../lib/utils.js'
import CoverArt from '../components/CoverArt.jsx'
import MangaCard from '../components/MangaCard.jsx'
import FavButton from '../components/FavButton.jsx'
import Icon from '../components/Icon.jsx'
import NotFound from './NotFound.jsx'

export default function MangaPage() {
  const { id } = useParams()
  const m = getManga(id)
  if (!m) return <NotFound />

  const similar = manga
    .filter((x) => x.id !== m.id && x.genres.some((g) => m.genres.includes(g)))
    .slice(0, 4)
  const chapters = [...m.chapters].reverse()
  const first = m.chapters[0]
  const last = m.chapters[m.chapters.length - 1]

  return (
    <div className="container">
      <div className="manga-head">
        <div className="manga-cover">
          <CoverArt m={m} />
        </div>
        <div>
          <h1 className="manga-title">{m.title}</h1>
          <div className="meta-row">
            <span>
              Автор: <b style={{ color: 'var(--t1)' }}>{m.author}</b>
            </span>
            {m.artist && <span>Художник: {m.artist}</span>}
            <span>{m.year}</span>
            <span className={`status-text ${m.status}`}>
              {m.status === 'ongoing' ? 'Онгоинг' : 'Завершена'}
            </span>
            <span>
              <b>★ {m.rating.toFixed(1)}</b>
            </span>
            <span>{fmtViews(m.views)} просмотров</span>
          </div>
          <div className="chips">
            {m.genres.map((g) => (
              <Link key={g} className="chip" to={`/catalog?genre=${encodeURIComponent(g)}`}>
                {g}
              </Link>
            ))}
          </div>
          <div className="manga-actions">
            <Link to={`/reader/${m.id}/${first.number}`} className="btn btn-primary">
              <Icon name="book" size={26} />
              Читать с 1-й главы
            </Link>
            <Link to={`/reader/${m.id}/${last.number}`} className="btn btn-ghost">
              <Icon name="bell" size={26} />
              Свежая глава
            </Link>
            <FavButton id={m.id} />
          </div>
        </div>
      </div>

      <div className="desc glass">
        <h3>О серии</h3>
        {m.description}
      </div>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>Главы</h2>
            <div className="sub">
              {m.chapters.length} {plural(m.chapters.length, 'глава', 'главы', 'глав')}
            </div>
          </div>
        </div>
        <div className="chapter-list">
          {chapters.map((c) => (
            <Link key={c.number} className="chapter" to={`/reader/${m.id}/${c.number}`}>
              <span className="chapter-num">№ {c.number}</span>
              <span className="chapter-info">
                <b>«{c.title}»</b>
                <span>{fmtDate(c.date)}</span>
              </span>
              <span className="btn btn-ghost btn-sm">Читать</span>
            </Link>
          ))}
        </div>
      </section>

      {similar.length > 0 && (
        <section className="section">
          <div className="section-head">
            <div>
              <h2>Похожие манги</h2>
              <div className="sub">Те же жанры, другие пути</div>
            </div>
          </div>
          <div className="grid grid-4">
            {similar.map((x) => (
              <MangaCard key={x.id} m={x} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
