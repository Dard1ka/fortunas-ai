import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import mkcert from 'vite-plugin-mkcert'
import { VitePWA } from 'vite-plugin-pwa'

// HTTPS toggle:
//   npm run dev          → http (faster startup; OK for desktop testing)
//   npm run dev:https    → https via mkcert (required for mic on phones)
const useHttps = process.env.VITE_HTTPS === '1'

// Target backend untuk proxy /api. Default = backend lokal. Set VITE_API_TARGET
// untuk arahkan ke VPS, mis: VITE_API_TARGET=http://103.93.134.22
const apiTarget = process.env.VITE_API_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [
    react(),
    // mkcert auto-generates a locally-trusted CA + leaf cert the first time
    // it runs, so phones on the same WiFi can connect via HTTPS without a
    // scary cert warning. Only enabled when VITE_HTTPS=1.
    ...(useHttps ? [mkcert()] : []),
    VitePWA({
      registerType: 'autoUpdate',
      // Manifest dikelola manual di public/manifest.webmanifest (satu sumber
      // kebenaran yang juga di-test paritasnya) — plugin hanya membuat SW.
      manifest: false,
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,woff2,webmanifest}'],
        navigateFallback: '/index.html',
        // Jangan intersep /api dan /media — itu urusan backend/nginx.
        navigateFallbackDenylist: [/^\/api\//, /^\/media\//],
      },
    }),
  ],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: false,
  },
  server: {
    // host: true → bind to 0.0.0.0 so phones on the same WiFi can reach the
    // dev server at http(s)://<your-LAN-IP>:3000.
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
