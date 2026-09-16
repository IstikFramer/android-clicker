import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// MANGVERSE — dev-сервер доступен извне (0.0.0.0) для live-превью
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // живой превью-хост (e2b.app) должен приниматься
    allowedHosts: true,
  },
})
