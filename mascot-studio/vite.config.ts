import { defineConfig } from 'vite';

export default defineConfig({
  base: '/mascot-viewer/',
  build: {
    outDir: '../web/mascot-viewer',
    emptyOutDir: true,
    target: 'es2022',
    sourcemap: true,
  },
  server: { fs: { allow: ['..'], deny: ['**/.local/**','**/.env*','**/.git/**','**/.aws/**','**/.codex/**','**/.agents/**'] } },
});
