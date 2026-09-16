import { useEffect, useState } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import Home from './pages/Home.jsx'
import Catalog from './pages/Catalog.jsx'
import MangaPage from './pages/MangaPage.jsx'
import Reader from './pages/Reader.jsx'
import SearchPage from './pages/SearchPage.jsx'
import Rankings from './pages/Rankings.jsx'
import Favorites from './pages/Favorites.jsx'
import NotFound from './pages/NotFound.jsx'

export default function App() {
  const { pathname } = useLocation()
  const [glow, setGlow] = useState(() => {
    try {
      return localStorage.getItem('mangverse:glow') !== '0'
    } catch {
      return true
    }
  })

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  useEffect(() => {
    document.body.classList.toggle('no-glow', !glow)
    try {
      localStorage.setItem('mangverse:glow', glow ? '1' : '0')
    } catch {
      /* noop */
    }
  }, [glow])

  const isReader = pathname.startsWith('/reader/')

  return (
    <>
      <Navbar glow={glow} onToggleGlow={() => setGlow((g) => !g)} />
      <main className="site-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/manga/:id" element={<MangaPage />} />
          <Route path="/reader/:id/:chapter" element={<Reader />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/rankings" element={<Rankings />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      {!isReader && <Footer />}
    </>
  )
}
