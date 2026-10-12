<script setup lang="ts">
const { data: zones } = await useFetch<any[]>('/api/risk')
const { data: aft } = await useFetch<any>('/api/aftershock')
</script>
<template>
  <div class="space-y-8">
    <section class="card p-6 md:p-8">
      <p class="text-xs uppercase tracking-widest text-amber-500">Proyecto comunitario · Panamá</p>
      <h1 class="mt-2 text-3xl font-bold md:text-4xl">¿Por qué existe este predictor?</h1>
      <div class="mt-4 max-w-3xl space-y-3 text-sm leading-relaxed text-slate-300">
        <p>
          Panamá está en la unión de las placas Cocos, Nazca y Caribe: tiembla todas las semanas,
          pero la información útil está dispersa entre catálogos globales. Este proyecto es un
          <strong>PoC de investigación</strong>: une el catálogo sísmico USGS (1970–hoy) con clima
          (temperatura, humedad, presión) y estima
          <strong>P(sismo M4+ en los próximos 7 días)</strong> por zona del país.
        </p>
        <p>
          No es predicción determinista — <strong>nadie puede predecir terremotos con fecha y hora</strong> —
          sino pronóstico probabilístico honesto: publicamos aciertos <em>y</em> fallos
          (el modelo marcó Nivel 3 días antes del M7.7 de Azuero de oct-2026).
          Todo el código, datos y comparativas son abiertos para la comunidad.
        </p>
      </div>
      <div class="mt-5 flex flex-wrap gap-3 text-sm">
        <NuxtLink class="btn" to="/pronostico">Ver pronóstico</NuxtLink>
        <NuxtLink class="btn" to="/comparativa">Comparativa de modelos</NuxtLink>
        <NuxtLink class="btn" to="/estudios">Área de estudio</NuxtLink>
      </div>
    </section>

    <section v-if="aft?.modo_secuencia" class="card border-red-500/40 p-6">
      <p class="text-xs uppercase tracking-widest text-red-400">Modo secuencia · segundo evaluador ETAS</p>
      <h2 class="mt-1 text-xl font-bold">Réplicas activas ({{ aft.grandes_30d }} sismos M6+ en 30d)</h2>
      <p class="mt-1 text-sm text-slate-400">Probabilidad de réplica M4+ en 24h / 1h por zona, física de Omori — verificado contra el feed en vivo.</p>
      <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div v-for="(v, z) in aft.zonas" :key="z" class="rounded-xl border border-white/10 bg-black/30 p-3 text-center">
          <p class="text-xs font-semibold">{{ z }}</p>
          <p class="num mt-1 text-2xl font-bold" :class="(v.p24 as number) >= 0.5 ? 'text-red-300' : 'text-slate-200'">{{ ((v.p24 as number) * 100).toFixed(0) }}%</p>
          <p class="num text-xs text-slate-400">24h · 1h: {{ ((v.p1h as number) * 100).toFixed(1) }}%</p>
        </div>
      </div>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold">Niveles actuales por zona</h2>
      <div v-if="zones?.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ZoneCard v-for="z in zones" :key="z.zone" :zone="z.zone" :nivel="z.nivel"
          :p4="z.p_M4_7d" :p5="z.p_M5_7d" :p6="z.p_M6_7d" :mensaje="z.mensaje"
          :curva="z.curva_diaria" :curva5="z.curva_m5" :curva6="z.curva_m6" :bandas="z.bandas_gr" :fecha="z.date" />
      </div>
      <p v-else class="card p-4 text-sm text-slate-400">API no disponible — arranca el backend: <code>uvicorn src.serve.app:app --port 8001</code></p>
    </section>

    <section class="card p-6 text-sm text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">Cómo leer esto</h2>
      <p>Nivel 3 🟢 tranquilo · 4 🟡 leve posible · 5 🟠 intermedio posible · 6 🔴 fuerte posible.
      Los niveles 7–10 no se pronostican: solo hubo 5 sismos M7+ en 56 años, insuficiente para entrenar.
      Detalle y evidencia en <NuxtLink class="underline" to="/alertas">Alertas</NuxtLink>.</p>
    </section>
  </div>
</template>
