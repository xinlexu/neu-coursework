import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Allow requests from a dev server running on localhost:5500
  server: {
    cors: {
      // single origin (string) or array of origins
      origin: 'http://localhost:5500',
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
    }
  },
  // define constants available at build time
  define: {
    // Use in code as __LOCALHOST_5500__
    __LOCALHOST_5500__: JSON.stringify('http://localhost:5500')
  }
})
