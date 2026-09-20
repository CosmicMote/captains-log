import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load .env so we can read VITE_API_BASE as the proxy target
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE ?? 'http://localhost:8000'

  return {
    // Relative asset URLs, resolved against the <base href> tag in index.html.
    // That tag is set at container start from BASE_PATH, so one build can be
    // served from any sub-path.
    base: './',
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
