<template>
  <div class="min-h-screen">
    <header class="sticky top-0 z-10 border-b border-white/10 bg-[#0a0e14]/90 backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
          <span class="inline-block h-3 w-3 rounded-full bg-amber-500" />
          Sismos Panamá <span class="text-xs font-normal text-slate-400">PoC</span>
        </NuxtLink>
        <nav class="flex flex-wrap gap-4 text-sm">
          <NuxtLink class="navlink" to="/pronostico">Pronóstico</NuxtLink>
          <NuxtLink class="navlink" to="/mapa">Mapa</NuxtLink>
          <NuxtLink class="navlink" to="/comparativa">Comparativa</NuxtLink>
          <NuxtLink class="navlink" to="/alertas">Alertas</NuxtLink>
          <NuxtLink class="navlink" to="/estudios">Estudios</NuxtLink>
          <NuxtLink class="navlink" to="/docs">Docs</NuxtLink>
          <NuxtLink class="navlink" to="/ingesta">Ingesta</NuxtLink>
        </nav>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-8">
      <NuxtPage />
    </main>
    <footer class="mx-auto max-w-6xl px-4 pb-10 text-xs text-slate-500">
      Investigación comunitaria · Probabilidades, no predicción determinista · Datos: USGS + Open-Meteo ·
      <span class="num">API :8001</span>
    </footer>
  </div>
</template>
