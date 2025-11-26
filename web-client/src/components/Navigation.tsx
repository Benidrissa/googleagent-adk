import { Link, useLocation } from 'react-router-dom'
import '../App.css'

export default function Navigation() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path ? 'active' : ''
  }

  return (
    <nav className="navigation">
      <div className="nav-header">
        <h2>🤰 Pregnancy Companion</h2>
      </div>
      <ul className="nav-links">
        <li>
          <Link to="/" className={isActive('/')}>
            <span className="nav-icon">💬</span>
            <span className="nav-label">Chat</span>
          </Link>
        </li>
        <li>
          <Link to="/logs" className={isActive('/logs')}>
            <span className="nav-icon">📋</span>
            <span className="nav-label">Logs</span>
          </Link>
        </li>
        <li>
          <Link to="/evaluation" className={isActive('/evaluation')}>
            <span className="nav-icon">📊</span>
            <span className="nav-label">Evaluation</span>
          </Link>
        </li>
      </ul>
      <div className="nav-footer">
        <p className="nav-version">ADK Agent v1.0</p>
      </div>
    </nav>
  )
}
