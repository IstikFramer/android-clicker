/** Обложка: реальный арт (m.cover), а до его появления — CSS-градиент с типографикой */
export default function CoverArt({ m }) {
  if (m.cover) {
    return (
      <div className="cover cover-img">
        <img src={m.cover} alt={`Обложка: ${m.title}`} loading="lazy" />
        <span className="cover-badge">MANGVERSE</span>
      </div>
    )
  }
  const [c1, c2] = m.color
  return (
    <div
      className="cover"
      style={{ background: `linear-gradient(150deg, ${c1} 0%, ${c2} 62%, #07040d 130%)` }}
    >
      <div className="cover-grid" />
      <div className="cover-glow" />
      <span className="cover-letter">{m.title.trim().charAt(0).toUpperCase()}</span>
      <span className="cover-badge">MANGVERSE</span>
      <span className="cover-title">{m.title}</span>
    </div>
  )
}
