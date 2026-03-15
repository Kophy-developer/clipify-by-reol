import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ingest': { target: 'http://localhost:8000', changeOrigin: true },
      '/status': { target: 'http://localhost:8000', changeOrigin: true },
      '/results': { target: 'http://localhost:8000', changeOrigin: true },
      '/retry': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
