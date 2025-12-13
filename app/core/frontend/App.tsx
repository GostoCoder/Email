/**
 * Application principale React
 * Point d'entrée de l'interface utilisateur avec routage
 * Utilise le design system Reception avec glassmorphism
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Home, Settings, Send, FileText, UserX } from 'lucide-react';

// Import des composants de chaque feature
import Dashboard from '@/features/dashboard/view/Dashboard';
import Configuration from '@/features/configuration/view/Configuration';
import Campaign from '@/features/campaign/view/Campaign';
import Templates from '@/features/templates/view/Templates';
import Suppression from '@/features/suppression/view/Suppression';

// Import des styles globaux
import '@/core/shared/styles/App.css';

interface NavLinkProps {
  to: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const NavLink: React.FC<NavLinkProps> = ({ to, icon, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`nav-link ${isActive ? 'active' : ''}`}
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">
            <Send size={32} color="rgb(0, 89, 96)" />
            <h1>Outil Emailing</h1>
          </div>
          <div className="nav-links">
            <NavLink to="/" icon={<Home size={20} />}>
              Dashboard
            </NavLink>
            <NavLink to="/configuration" icon={<Settings size={20} />}>
              Configuration
            </NavLink>
            <NavLink to="/campaign" icon={<Send size={20} />}>
              Campagne
            </NavLink>
            <NavLink to="/templates" icon={<FileText size={20} />}>
              Templates
            </NavLink>
            <NavLink to="/suppression" icon={<UserX size={20} />}>
              Liste de Suppression
            </NavLink>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/configuration" element={<Configuration />} />
            <Route path="/campaign" element={<Campaign />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/suppression" element={<Suppression />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
