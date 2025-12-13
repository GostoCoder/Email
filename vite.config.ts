import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
// Configuration Vite pour l'architecture MVVM Feature-First
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Alias pour l'architecture MVVM
      '@': path.resolve(__dirname, './app'),
      '@core': path.resolve(__dirname, './app/core'),
      '@features': path.resolve(__dirname, './app/features'),
      '@shared': path.resolve(__dirname, './app/core/shared'),
      '@/core/shared/components': path.resolve(__dirname, './app/core/shared/components'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // Nécessaire pour Docker
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Output pour être servi par Flask en production
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          // Séparation des chunks pour de meilleures performances
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['lucide-react', 'clsx'],
        },
      },
    },
  },
  root: './app/core/frontend',
})
