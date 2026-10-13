import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  devtools: { enabled: false },
  runtimeConfig: {
    public: {
      // URL del websocket en vivo. En Coolify: wss://<dominio-del-api>/ws/live.
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws/live',
      // Google Maps JS API (llave publica del navegador). En Coolify se fija en la UI.
      googleMapsKey: process.env.NUXT_PUBLIC_GOOGLE_MAPS_KEY || ''
    }
  },
  css: ['~/assets/css/main.css'],
  vite: { plugins: [tailwindcss()] },
  app: {
    head: {
      title: 'Sismos Panamá — Pronóstico probabilístico',
      meta: [
        { name: 'description', content: 'PoC de pronóstico probabilístico de sismos M4+ a 7 días para Panamá. Investigación, no alerta oficial.' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' }
      ],
      htmlAttrs: { lang: 'es', class: 'dark' }
    }
  }
})
