import { NavLink, Routes, Route, Outlet } from "react-router-dom";
import Home from "./pages/Home";
import Counter from "./pages/Counter";
import Clock from "./pages/Clock";

function Layout() {
  return (
    <div className="container">
      <header className="topbar">
        <h1 className="brand">Week7 HW · Student</h1>
        <nav className="nav">
          <NavLink end to="/" className="link">Home</NavLink>
          <NavLink to="/counter" className="link">Counter</NavLink>
          <NavLink to="/clock" className="link">Clock</NavLink>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="footer">© 2025 Student</footer>
    </div>
  );
}

function NotFound() {
  return <p style={{ padding: "1rem" }}>Page not found.</p>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="counter" element={<Counter />} />
        <Route path="clock" element={<Clock />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}