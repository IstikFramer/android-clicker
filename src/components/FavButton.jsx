import { useState } from 'react'
import { isFav, toggleFav } from '../lib/storage.js'
import Icon from './Icon.jsx'

export default function FavButton({ id }) {
  const [fav, setFav] = useState(() => isFav(id))
  return (
    <button
      type="button"
      className={`fav-btn ${fav ? 'active' : ''}`}
      aria-pressed={fav}
      onClick={() => setFav(toggleFav(id))}
    >
      <Icon name="star" size={30} />
      {fav ? 'В избранном' : 'В избранное'}
    </button>
  )
}
