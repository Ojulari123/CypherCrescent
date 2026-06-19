import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },

  modules: ['@pinia/nuxt', '@vueuse/nuxt'],

  // Disable SSR for all routes. Auth is client-only (tokens in localStorage),
  // and SSR causes a flash because the server-rendered HTML arrives before
  // CSS + theme state are ready.
  routeRules: {
    '/**': { ssr: false },
  },

  css: ['~/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },

  app: {
    head: {
      title: 'Cypher Crescent — Crypto Portfolio Tracker',
      htmlAttrs: { lang: 'en' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Track your crypto portfolio, holdings, watchlist and live market data.' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap' },
      ],
      script: [
        {
          innerHTML: `(function(){var t=localStorage.getItem('cc_theme');if(t?t==='dark':true)document.documentElement.classList.add('dark')})()`,
          type: 'text/javascript',
        },
      ],
    },
  },
})
