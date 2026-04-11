import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load .env so we can read VITE_API_BASE as the proxy target
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE ?? 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      proxy: {
        // All /api/* requests are forwarded to the backend.
        // secure: false accepts self-signed TLS certs in dev.
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
