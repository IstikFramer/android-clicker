import { Link } from 'react-router-dom'
import Icon from '../components/Icon.jsx'

export default function NotFound() {
  return (
    <div className="container">
      <div className="empty" style={{ paddingTop: 120, paddingBottom: 120 }}>
        <Icon name="book" size={90} />
        <h3 style={{ fontSize: 34 }}>404</h3>
        <p>Страница потерялась во вселенной. Скорее всего, манга где-то рядом.</p>
        <Link to="/" className="btn btn-primary">
          Вернуться к базе
        </Link>
      </div>
    </div>
  )
}
