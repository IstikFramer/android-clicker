import { Link } from 'react-router-dom'
import { manga, GENRES, totalChapters, totalViews } from '../data/manga.js'
import { fmtViews, fmtDateShort } from '../lib/utils.js'
import MangaCard from '../components/MangaCard.jsx'
import CoverArt from '../components/CoverArt.jsx'
import Icon from '../components/Icon.jsx'

export default function Home() {
  const top = [...manga].sort((a, b) => b.rating - a.rating).slice(0, 4)
  const news = manga
    .map((m) => ({ m, ch: m.chapters[m.chapters.length - 1] }))
    .sort((a, b) => b.ch.date.localeCompare(a.ch.date))
    .slice(0, 6)

  return (
    <div className="container">
      <section className="hero">
        <div className="hero-bg">
          <img src="/images/bg/hero.jpg" alt="" />
        </div>
        <div className="hero-veil" />
        <div className="hero-content">
          <span className="hero-badge">Новая платформа · 2026</span>
          <h1>
            Твоя манга в <span className="grad">новой вселенной</span>
          </h1>
          <p>
            Тёмное пространство, где живут истории: каталог, главы, ранки и избранное. Без шума —
            только манга.
          </p>
          <div className="hero-cta">
            <Link to="/catalog" className="btn btn-primary">
              <Icon name="book" size={26} />
              Открыть каталог
            </Link>
            <Link to="/rankings" className="btn btn-ghost">
              <Icon name="star" size={26} />
              Топ рейтингов
            </Link>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <b>{manga.length}</b>
              <span>манг в каталоге</span>
            </div>
            <div className="stat">
              <b>{totalChapters}</b>
              <span>глав вышло</span>
            </div>
            <div className="stat">
              <b>{fmtViews(totalViews)}</b>
              <span>просмотров всего</span>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>Горячие сейчас</h2>
            <div className="sub">Лидеры рейтинга читателей</div>
          </div>
          <Link to="/rankings" className="link-all">
            Все ранки →
          </Link>
        </div>
        <div className="grid grid-4">
          {top.map((m) => (
            <MangaCard key={m.id} m={m} />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>Новые главы</h2>
            <div className="sub">Свежее из вселенной</div>
          </div>
        </div>
        <div className="chapter-list">
          {news.map(({ m, ch }) => (
            <Link key={`${m.id}-${ch.number}`} className="news-row" to={`/reader/${m.id}/${ch.number}`}>
              <div className="news-cover">
                <CoverArt m={m} />
              </div>
              <div className="news-body">
                <h4>{m.title}</h4>
                <p>
                  Глава {ch.number} · «{ch.title}»
                </p>
              </div>
              <span className="news-date">{fmtDateShort(ch.date)}</span>
              <span className="btn btn-ghost btn-sm">Читать</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>По жанрам</h2>
            <div className="sub">Выбери свой путь сквозь тьму</div>
          </div>
        </div>
        <div className="chips">
          <Icon name="grid" size={30} />
          {GENRES.map((g) => (
            <Link key={g} className="chip" to={`/catalog?genre=${encodeURIComponent(g)}`}>
              {g}
            </Link>
          ))}
        </div>
      </section>

      <section className="cta">
        <Icon name="bell" size={54} />
        <div className="cta-body">
          <h3>Не пропускай новые главы</h3>
          <p>
            Ранки и каталог обновляются по мере выгрузки новых манг — загляни сюда чаще.
          </p>
        </div>
        <Link to="/catalog" className="btn btn-primary">
          В каталог
        </Link>
      </section>
    </div>
  )
}
