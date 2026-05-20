import { Link, Outlet, useLocation } from 'react-router-dom'

export default function App() {
  const { pathname } = useLocation()
  return (
    <div className="container">
      <header className="header">
        <div className="brand">
          <h1>Student · CS5610 · Project 2 — Auto MPG</h1>
          <small>Train a model, then predict MPG from car specs.</small>
        </div>
        <nav className="nav">
          <Link to="/" style={{fontWeight: pathname==='/'?'700':undefined}}>Home</Link>
          <Link to="/train" style={{fontWeight: pathname.startsWith('/train')?'700':undefined}}>Train</Link>
          <Link to="/estimate" style={{fontWeight: pathname.startsWith('/estimate')?'700':undefined}}>Estimate</Link>
        </nav>
      </header>

      <Outlet />

      <footer className="footer">
        Student · CS5610 Project 2
      </footer>
    </div>
  )
}
