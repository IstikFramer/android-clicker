import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import Icon from './Icon.jsx'

const LINKS = [
  { to: '/', label: 'Главная' },
  { to: '/catalog', label: 'Каталог' },
  { to: '/rankings', label: 'Ранки' },
  { to: '/favorites', label: 'Избранное' },
]

export default function Navbar({ glow, onToggleGlow }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const submit = (e) => {
    e.preventDefault()
    const query = q.trim()
    navigate(query ? `/search?q=${encodeURIComponent(query)}` : '/search')
    setQ('')
    setOpen(false)
  }

  return (
    <div className="nav-shell">
      <nav className="nav">
        <Link to="/" className="nav-brand">
          <Icon name="logo" size={42} />
          <span className="nav-wordmark">MANGVERSE</span>
          <span className="nav-year">2026</span>
        </Link>

        <div className="nav-links">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              {l.label}
            </NavLink>
          ))}
        </div>

        <div className="nav-actions">
          <form className="nav-search" onSubmit={submit} role="search">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Поиск…"
              aria-label="Поиск"
            />
            <button className="icon-btn" type="submit" aria-label="Найти">
              <Icon name="search" size={34} />
            </button>
          </form>
          <Link to="/rankings" className="icon-btn" title="Новые главы">
            <Icon name="bell" size={38} />
          </Link>
          <button
            type="button"
            className={`icon-btn ${glow ? '' : 'off'}`}
            title={glow ? 'Неоновое свечение: вкл' : 'Неоновое свечение: выкл'}
            onClick={onToggleGlow}
          >
            <Icon name="settings" size={38} />
          </button>
          <Link to="/favorites" className="icon-btn" title="Мой список">
            <Icon name="user" size={38} />
          </Link>
          <button
            className="burger"
            onClick={() => setOpen(!open)}
            aria-label="Меню"
            aria-expanded={open}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </nav>

      {open && (
        <div className="nav-mobile">
          <form className="search-big" onSubmit={submit} role="search">
            <Icon name="search" size={30} />
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Манга, автор или жанр…"
              aria-label="Поиск"
            />
          </form>
          <div className="nav-mobile-links">
            {LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                onClick={() => setOpen(false)}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                {l.label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
