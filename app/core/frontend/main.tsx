/**
 * Point d'entrée principal de l'application React
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import '@/core/shared/styles/index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
