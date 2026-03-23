import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import mermaid from 'astro-mermaid';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://docs.reform-lab.eu',
  server: { port: 4322 },
  integrations: [
    mermaid(),
    react(),
    starlight({
      title: 'ReformLab Docs',
      social: [
        { icon: 'github', href: 'https://github.com/reformlab/reformlab', label: 'GitHub' },
      ],
      customCss: [
        '@fontsource-variable/inter/index.css',
        '@fontsource/ibm-plex-mono/400.css',
        './src/styles/custom.css',
      ],
      sidebar: [
        { label: 'Home', link: '/' },
        { label: 'Use Cases', link: '/use-cases/' },
        { label: 'Getting Started', link: '/getting-started/' },
        { label: 'Domain Model', link: '/domain-model/' },
        { label: 'Contributing', link: '/contributing/' },
        { label: 'API Reference', link: '/api-reference/' },
      ],
    }),
  ],
});
