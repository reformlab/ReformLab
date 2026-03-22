import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        '@brand': new URL('../_bmad-output/branding', import.meta.url).pathname,
      },
    },
  },
  output: 'static',
});
