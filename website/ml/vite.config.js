import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GitHub Pages deploys under /Fluex/ — use that as base in production
// In dev (npm run dev) base is '/' so localhost works normally
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_URL || '/',
  server: {
    port: 5173,
    open: true
  }
})
