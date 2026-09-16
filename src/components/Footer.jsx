import { Link } from 'react-router-dom'
import Icon from './Icon.jsx'
import { GENRES } from '../data/manga.js'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="footer-brand">
              <Icon name="logo" size={40} />
              <span className="nav-wordmark">MANGVERSE</span>
              <span className="nav-year">2026</span>
            </div>
            <p className="footer-about">
              Манга-платформа 2026 года: каталог, главы, ранки и избранное — всё в одном тёмном
              пространстве.
            </p>
          </div>
          <div>
            <h4>Навигация</h4>
            <div className="footer-links">
              <Link to="/">Главная</Link>
              <Link to="/catalog">Каталог</Link>
              <Link to="/rankings">Ранки</Link>
              <Link to="/search">Поиск</Link>
              <Link to="/favorites">Избранное</Link>
            </div>
          </div>
          <div>
            <h4>Жанры</h4>
            <div className="chips">
              {GENRES.slice(0, 6).map((g) => (
                <Link key={g} className="chip" to={`/catalog?genre=${encodeURIComponent(g)}`}>
                  {g}
                </Link>
              ))}
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2026 MANGVERSE. Все права на вселенную защищены.</span>
          <span>Сделано в темноте, но не в одиночестве.</span>
        </div>
      </div>
    </footer>
  )
}
