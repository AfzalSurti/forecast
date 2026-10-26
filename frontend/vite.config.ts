import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [react()],
    build: {
      rollupOptions: {
        output: {
          manualChunks: { recharts: ['recharts'] },
        },
      },
    },
    server: {
      proxy: {
        // In dev, forward API calls to the local FastAPI server.
        '/api': env.VITE_DEV_API_PROXY ?? 'http://localhost:8000',
      },
    },
  };
});
