import { defineConfig } from 'vite';
import { resolve } from 'path';

// Yandex Games build: relative base so the ZIP works from any path,
// assets are copied as-is (no hashing) for a clean dist/ layout.
export default defineConfig({
  base: './',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    assetsDir: 'build',
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      input: resolve(__dirname, 'index.html'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: true,
  },
});
