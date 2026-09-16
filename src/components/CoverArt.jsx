/** Обложка-заглушка: фиолетовый CSS-градиент + типографика (до выгрузки реальных обложек) */
export default function CoverArt({ m }) {
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
