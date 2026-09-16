/** Сгенерированная иконка на изумрудной плашке (public/images/icons) */
export default function Icon({ name, size = 40, className = '' }) {
  return (
    <img
      className={`icon-chip ${className}`}
      src={`/images/icons/${name}.png`}
      width={size}
      height={size}
      style={{ width: size, height: size }}
      alt=""
      loading="lazy"
      draggable={false}
    />
  )
}
