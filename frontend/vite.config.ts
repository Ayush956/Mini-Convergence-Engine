import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4200,
    // The app calls /api on its own origin, both locally and deployed, so
    // there is no environment branch anywhere in the source. Locally the dev
    // server forwards those calls to the FastAPI process.
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
});
