import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Debug环境配置 - 代理到backend-debug服务
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
        target: 'http://backend-debug:8000',  // Debug环境使用backend-debug服务名
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist'
  }
})