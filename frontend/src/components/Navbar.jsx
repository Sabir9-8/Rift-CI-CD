import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Zap } from 'lucide-react'

const Navbar = () => {
  const location = useLocation()
  const isActive = (path) => location.pathname === path ? 'active' : ''

  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        <div className="logo-icon">
          <Zap size={24} color="white" />
        </div>
        <span>RiftAgent</span>
      </Link>
      
      <div className="nav-links">
        <Link to="/" className={isActive('/')}>Home</Link>
        <Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link>
        <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
        <a href="#docs">Docs</a>
      </div>
      
      <div>
        <Link to="/dashboard">
          <button className="btn btn-primary">Get Started</button>
        </Link>
      </div>
    </nav>
  )
}

export default Navbar

