import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'node:child_process'

// Dev-only auth: seed the deployed-environment token from the Lemma CLI so `npm run dev`
// opens signed in. Never runs during `vite build`, so nothing ships in the bundle.
function lemmaDevAuth(env: Record<string, string>): Plugin {
  const command = env.VITE_LEMMA_DEV_TOKEN_CMD ?? 'lemma auth print-token'
  return {
    name: 'lemma-dev-auth',
    apply: 'serve',
    transformIndexHtml() {
      if (!command.trim()) return
      try {
        const token = execSync(command, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()
        if (!token) return
        return [{ tag: 'script', injectTo: 'head-prepend',
          children: `try{localStorage.setItem("lemma_token",${JSON.stringify(token)})}catch(e){}` }]
      } catch { return }
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    base: mode === 'production' ? env.VITE_LEMMA_APP_BASE_PATH || '/' : '/',
    plugins: [react(), lemmaDevAuth(env)],
    resolve: { dedupe: ['react', 'react-dom', '@tanstack/react-query'] },
  }
})
