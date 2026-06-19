import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },

  modules: ['@pinia/nuxt', '@vueuse/nuxt'],

  css: ['~/assets/css/main.css'],

  // Tailwind v4 via the official Vite plugin (config lives in main.css @theme).
  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    public: {
      // Override with NUXT_PUBLIC_API_BASE. Defaults to the local FastAPI server.
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
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    },
  },
})
