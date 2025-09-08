import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,  // 在Docker中启用文件轮询
    },
    hmr: {
      host: 'localhost',  // HMR websocket 主机
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',  // Docker环境中使用服务名
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist'
  }
})