import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Debug环境配置 - 代理到backend服务
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
        target: 'http://backend:8000',  // Debug环境使用backend服务名
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist'
  }
})