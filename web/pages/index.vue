<script setup lang="ts">
import { useLiveFeed } from '~/composables/useLiveFeed'

const { data: zones } = await useFetch<any[]>('/api/risk')
const { data: aft } = await useFetch<any>('/api/aftershock')
const { data: ing } = await useFetch<any>('/api/ingesta')
const hace120d = new Date(Date.now() - 120 * 864e5).toISOString().slice(0, 10)
const { data: sismos } = await useFetch<any[]>('/api/quakes', { params: { minmag: 4.0, start: hace120d } })
const { connected } = useLiveFeed()

const ahora = Date.now()
const en7d = (sismos.value ?? []).filter((q) => Date.parse(q.time) >= ahora - 7 * 864e5)
const en30d = (sismos.value ?? []).filter((q) => Date.parse(q.time) >= ahora - 30 * 864e5)
const recientes = [...(sismos.value ?? [])].sort((a, b) => b.time.localeCompare(a.time)).slice(0, 8)
const maxNivel = (zones.value ?? []).reduce((m, z) => Math.max(m, z.nivel ?? 0), 0)
const maxP = (zones.value ?? []).reduce((m: any, z: any) => (!m || z.p_M4_7d > m.p_M4_7d ? z : m), null)
const fmtFecha = (t: string) => new Date(t).toLocaleString('es-PA', { timeZone: 'UTC', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) + ' UTC'
// Probabilidades siempre visibles (las tarjetas ocultan <1%): 1 decimal si >=1%, 2 si >=0.01%, si no "<0.01%".
const fmtP = (p: number) => p >= 0.01 ? (p * 100).toFixed(1) + '%' : p >= 0.0001 ? (p * 100).toFixed(2) + '%' : '<0.01%'
// M7+ por extrapolación Gutenberg-Richter (b=1) desde P(M6+): misma fórmula del API, no salida directa del modelo.
const gr7 = (p6: number) => p6 / 10
const porNivel = [...(zones.value ?? [])].sort((a, b) => b.nivel - a.nivel || b.p_M4_7d - a.p_M4_7d)
</script>
<template>
  <div class="space-y-8">
    <section>
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 class="text-3xl font-bold">Tablero sísmico de Panamá</h1>
          <p class="mt-1 text-sm text-slate-400">
            Pronóstico probabilístico P(M4+ a 7 días) por zona · Sismicidad observada USGS ·
            <span class="num">{{ ing?.catalog_max ? 'catálogo al ' + String(ing.catalog_max).slice(0, 10) : 'catálogo 1970–hoy' }}</span>
          </p>
        </div>
        <p class="flex items-center gap-2 text-xs" :class="connected ? 'text-green-400' : 'text-slate-500'">
          <span class="inline-block h-2 w-2 rounded-full" :class="connected ? 'bg-green-400' : 'bg-slate-600'" />
          {{ connected ? 'canal en vivo' : 'conectando…' }}
        </p>
      </div>
      <div v-if="zones?.length" class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div class="card p-3">
          <p class="text-[11px] uppercase tracking-wide text-slate-500">Nivel máx. nacional</p>
          <p class="num mt-1 text-2xl font-bold">{{ maxNivel }}<span class="text-sm font-normal text-slate-500">/6</span></p>
        </div>
        <div class="card p-3">
          <p class="text-[11px] uppercase tracking-wide text-slate-500">P(M4+ 7d) máx.</p>
          <p class="num mt-1 text-2xl font-bold">{{ maxP ? (maxP.p_M4_7d * 100).toFixed(1) + '%' : '—' }}</p>
          <p class="text-[11px] text-slate-500">{{ maxP?.zone ?? '' }}</p>
        </div>
        <div class="card p-3">
          <p class="text-[11px] uppercase tracking-wide text-slate-500">M4+ últimos 7 d</p>
          <p class="num mt-1 text-2xl font-bold">{{ en7d.length }}</p>
          <p class="text-[11px] text-slate-500">observados</p>
        </div>
        <div class="card p-3">
          <p class="text-[11px] uppercase tracking-wide text-slate-500">M4+ últimos 30 d</p>
          <p class="num mt-1 text-2xl font-bold">{{ en30d.length }}</p>
          <p class="text-[11px] text-slate-500">observados</p>
        </div>
        <div class="card p-3">
          <p class="text-[11px] uppercase tracking-wide text-slate-500">Latencia USGS</p>
          <p class="num mt-1 text-2xl font-bold">{{ ing?.delay_min ?? '—' }}<span v-if="ing?.delay_min" class="text-sm font-normal text-slate-500"> min</span></p>
          <p class="text-[11px] text-slate-500">retraso del catálogo</p>
        </div>
        <div class="card p-3">
          <p class="text-[11px] uppercase tracking-wide text-slate-500">Catálogo</p>
          <p class="num mt-1 text-2xl font-bold">{{ ing?.total ?? '—' }}</p>
          <p class="text-[11px] text-slate-500">sismos M4+ desde 1970</p>
        </div>
      </div>
    </section>

    <section v-if="aft?.modo_secuencia" class="card border-red-500/40 p-5">
      <div class="flex flex-wrap items-baseline justify-between gap-2">
        <h2 class="font-semibold text-red-300">Modo secuencia — réplicas activas ({{ aft.grandes_30d }} M6+ en 30 d)</h2>
        <NuxtLink class="text-xs underline text-slate-400" to="/alertas">Ver escala de alertas</NuxtLink>
      </div>
      <div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div v-for="(v, z) in aft.zonas" :key="z" class="rounded-lg border border-white/10 bg-black/30 p-3 text-center">
          <p class="text-xs font-semibold">{{ z }}</p>
          <p class="num mt-1 text-xl font-bold" :class="(v.p24 as number) >= 0.5 ? 'text-red-300' : 'text-slate-200'">{{ ((v.p24 as number) * 100).toFixed(0) }}%</p>
          <p class="num text-[11px] text-slate-400">réplica M4+ en 24 h</p>
        </div>
      </div>
    </section>

    <section>
      <div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 class="text-lg font-semibold">Rango de probabilidades — eventos mayores (7 días)</h2>
      </div>
      <p class="mb-3 max-w-4xl text-xs leading-relaxed text-slate-400">M4+–M6+ del modelo por zona. M7+ por extrapolación Gutenberg-Richter (b=1) desde P(M6+), no es salida directa del modelo.</p>
      <div v-if="porNivel.length" class="card overflow-x-auto">
        <table class="w-full min-w-[560px] text-sm">
          <thead>
            <tr class="border-b border-white/10 text-left text-[11px] uppercase tracking-wide text-slate-500">
              <th class="px-4 py-2 font-medium">Zona</th>
              <th class="px-4 py-2 font-medium">Nivel</th>
              <th class="px-4 py-2 text-right font-medium">M4+ 7d</th>
              <th class="px-4 py-2 text-right font-medium">M5+ 7d</th>
              <th class="px-4 py-2 text-right font-medium">M6+ 7d</th>
              <th class="px-4 py-2 text-right font-medium">M7+ 7d (GR)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="z in porNivel" :key="z.zone" class="border-b border-white/5 last:border-0">
              <td class="px-4 py-2 font-semibold">{{ z.zone }}</td>
              <td class="px-4 py-2"><LevelBadge :nivel="z.nivel" /></td>
              <td class="num px-4 py-2 text-right text-slate-100">{{ fmtP(z.p_M4_7d) }}</td>
              <td class="num px-4 py-2 text-right text-orange-200">{{ fmtP(z.p_M5_7d) }}</td>
              <td class="num px-4 py-2 text-right text-red-300">{{ fmtP(z.p_M6_7d) }}</td>
              <td class="num px-4 py-2 text-right text-slate-400">{{ fmtP(gr7(z.p_M6_7d)) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section>
      <div class="mb-3 flex items-baseline justify-between">
        <h2 class="text-lg font-semibold">Actividad telúrica reciente</h2>
        <NuxtLink class="text-xs underline text-slate-400" to="/mapa">Ver en el mapa tectónico</NuxtLink>
      </div>
      <div v-if="recientes.length" class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/10 text-left text-[11px] uppercase tracking-wide text-slate-500">
              <th class="px-4 py-2 font-medium">Fecha (UTC)</th>
              <th class="px-4 py-2 font-medium">Mag.</th>
              <th class="px-4 py-2 font-medium">Prof. km</th>
              <th class="px-4 py-2 font-medium">Lugar</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="q in recientes" :key="q.id ?? q.time + q.place" class="border-b border-white/5 last:border-0">
              <td class="num whitespace-nowrap px-4 py-2 text-slate-300">{{ fmtFecha(q.time) }}</td>
              <td class="num px-4 py-2 font-semibold" :class="q.mag >= 6 ? 'text-red-300' : q.mag >= 5 ? 'text-orange-300' : 'text-amber-200'">M{{ q.mag.toFixed(1) }}</td>
              <td class="num px-4 py-2 text-slate-300">{{ Math.round(q.depth) }}</td>
              <td class="px-4 py-2 text-slate-400">{{ q.place }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="card p-4 text-sm text-slate-400">Sin datos recientes — verifica que el backend esté corriendo.</p>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold">Pronóstico por zona — próximos 7 días</h2>
      <div v-if="zones?.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ZoneCard v-for="z in [...zones].sort((a, b) => b.nivel - a.nivel)" :key="z.zone" :zone="z.zone" :nivel="z.nivel"
          :p4="z.p_M4_7d" :p5="z.p_M5_7d" :p6="z.p_M6_7d" :mensaje="z.mensaje"
          :curva="z.curva_diaria" :curva5="z.curva_m5" :curva6="z.curva_m6" :bandas="z.bandas_gr" :fecha="z.date" />
      </div>
      <p v-else class="card p-4 text-sm text-slate-400">API no disponible — arranca el backend: <code>uvicorn src.serve.app:app --port 8001</code></p>
    </section>

    <section class="card p-6">
      <h2 class="font-semibold text-slate-100">Divulgación científica — qué muestra este tablero</h2>
      <div class="mt-3 max-w-4xl space-y-3 text-sm leading-relaxed text-slate-300">
        <p>
          Panamá se deforma entre la subducción de la placa de Cocos bajo el Caribe (fosa
          Mesoamericana, frente al Pacífico), la zona de fractura de Panamá y el cinturón
          deformado del norte. Cada punto del mapa es un sismo real del catálogo USGS con fecha,
          magnitud y profundidad: el movimiento telúrico observado, sin interpolar ni suavizar.
        </p>
        <p>
          El pronóstico es <strong>probabilístico, no determinista</strong>: nadie puede anticipar
          fecha y hora de un terremoto. Publicamos aciertos y fallos (el modelo marcó Nivel 3 días
          antes del M7.7 de Azuero de oct-2026) y los niveles 7–10 no se pronostican: solo hubo
          5 sismos M7+ en 56 años, insuficiente para entrenar. La latencia del propio USGS
          (arriba) limita lo "en vivo" que puede ser cualquier tablero.
        </p>
      </div>
      <div class="mt-4 flex flex-wrap gap-3 text-sm">
        <NuxtLink class="btn" to="/mapa">Mapa tectónico</NuxtLink>
        <NuxtLink class="btn" to="/comparativa">Comparativa de modelos</NuxtLink>
        <NuxtLink class="btn" to="/estudios">Estudios y veredictos</NuxtLink>
      </div>
    </section>
  </div>
</template>
