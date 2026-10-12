import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  devtools: { enabled: false },
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
