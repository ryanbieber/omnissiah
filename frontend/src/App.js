import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import Maintenance from './pages/Maintenance';
import Cars from './pages/Cars';
import Tasks from './pages/Tasks';
import Budgets from './pages/Budgets';
import Admin from './pages/Admin';

function App() {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              🏠 Omnissiah
            </Link>
            <div className={`nav-menu ${navOpen ? 'active' : ''}`}>
              <Link to="/" className="nav-link" onClick={() => setNavOpen(false)}>
                Dashboard
              </Link>
              <Link to="/maintenance" className="nav-link" onClick={() => setNavOpen(false)}>
                Maintenance
              </Link>
              <Link to="/cars" className="nav-link" onClick={() => setNavOpen(false)}>
                Cars
              </Link>
              <Link to="/tasks" className="nav-link" onClick={() => setNavOpen(false)}>
                Tasks
              </Link>
              <Link to="/budgets" className="nav-link" onClick={() => setNavOpen(false)}>
                Budgets
              </Link>
              <Link to="/admin" className="nav-link admin-link" onClick={() => setNavOpen(false)}>
                Admin
              </Link>
            </div>
            <div 
              className={`hamburger ${navOpen ? 'active' : ''}`}
              onClick={() => setNavOpen(!navOpen)}
            >
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/cars" element={<Cars />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/budgets" element={<Budgets />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>&copy; 2024 Omnissiah - Home Assistant Maintenance Management | API: {process.env.REACT_APP_API_URL}</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
