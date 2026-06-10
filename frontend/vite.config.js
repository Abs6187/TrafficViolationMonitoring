import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In dev mode, proxy /api calls to the Flask backend running on port 5000.
    // Without this, /api calls would go to the Vite dev server (port 5173) and fail.
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
