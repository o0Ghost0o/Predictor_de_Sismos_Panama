<script setup lang="ts">
const { data: live } = await useFetch<any[]>('/api/live')
const { data: ing } = await useFetch<any>('/api/ingesta')
const magColor = (m: number) => m >= 6 ? 'text-red-300' : m >= 5 ? 'text-orange-300' : m >= 4 ? 'text-yellow-200' : 'text-slate-300'
// Histórico del catálogo propio (7 días por defecto, como todo el sitio)
const preset = ref('7d')
const fini = ref(''); const ffin = ref('')
const hist = ref<any[]>([])
const histLoading = ref(false)
async function loadHist() {
  histLoading.value = true
  const now = new Date()
  let start = ''
  if (preset.value === 'custom') start = fini.value
  else if (preset.value === 'all') start = '1970-01-01'
  else {
    const days = { '24h': 1, '7d': 7, '30d': 30, '1y': 365 }[preset.value] ?? 1
    start = new Date(now.getTime() - days * 864e5).toISOString().slice(0, 10)
  }
  const params: any = { minmag: 0 }
  if (start) params.start = start
  if (preset.value === 'custom' && ffin.value) params.end = ffin.value
  const r: any[] = await $fetch('/api/quakes', { params })
  hist.value = [...r].reverse()
  histLoading.value = false
}
watch(preset, loadHist)
onMounted(loadHist)
const feed = ref<any[]>([])
watchEffect(() => { if (live.value?.length) feed.value = [...live.value] })
const { connected, last } = useLiveFeed((q) => {
  feed.value = [{ mag: q.mag, place: q.place, time: q.time, depth: q.depth, url: `https://earthquake.usgs.gov/earthquakes/eventpage/${q.id}`, fresh: true }, ...feed.value].slice(0, 30)
})
</script>
<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Ingesta y alimentación</h1>
      <p class="text-sm text-slate-400">Fuentes, estado y sismicidad en vivo (USGS, bbox Panamá 6.5–10N / 83.5–77W).</p>
    </div>
    <div class="grid gap-4 md:grid-cols-2">
      <div class="card p-5 text-sm text-slate-300">
        <h2 class="mb-2 font-semibold text-slate-100">Lotes históricos</h2>
        <ul class="num space-y-1">
          <li>quakes_full: {{ ing?.total ?? '…' }} eventos M4.0–7.7 (1970–hoy)</li>
          <li>weather_full: 103,660 zone-days (ERA5/Open-Meteo)</li>
          <li>dataset_hybrid: 103,685 filas × 21 cols</li>
        </ul>
        <p class="mt-3 text-xs text-slate-500">Re-entrenar: <code>python -m src.features.build … && python -m src.models.train …</code></p>
      </div>
      <div class="card p-5 text-sm text-slate-300">
        <h2 class="mb-2 font-semibold text-slate-100">Recurrente (cron/launchd diario)</h2>
        <ol class="list-decimal space-y-1 pl-5 text-xs">
          <li><code>api_usgs</code> últimos 30d → append quakes</li>
          <li><code>weather</code> mes en curso → append clima</li>
          <li><code>features.build</code> + <code>prospective issue/score</code></li>
        </ol>
        <p class="mt-3 text-xs text-slate-500">Pendiente: IGC-UPA local (M2+, ×10–50 eventos) · GNSS · RSS EMSC/PTWC.</p>
      </div>
    </div>
    <div class="card border-emerald-500/30 p-4 text-sm">
      <h2 class="mb-1 font-semibold">Live — dilatación mínima</h2>
      <p v-if="ing?.ts" class="num text-slate-300">
        Último sondeo: {{ new Date(ing.ts).toLocaleString('es-PA') }} ·
        nuevos: {{ ing.nuevos }} · catálogo hasta: {{ ing.catalog_max }} ·
        <strong>retraso {{ ing.delay_min }} min</strong> · total {{ ing.total }}
      </p>
      <p v-else class="text-slate-500">live_loop sin correr: <code>uv run python -m src.ingest.live_loop --interval 300</code></p>
      <p class="mt-1 text-xs text-slate-500">El dial ETAS lee el catálogo al vuelo: un M nuevo mueve p24 en minutos, sin reentrenar.</p>
    </div>
    <div class="card p-4">
      <h2 class="mb-1 font-semibold">RSS sísmico — RSN Costa Rica</h2>
      <p class="mb-2 text-xs text-slate-500">Feed real, cubre el borde fronterizo Chiriquí/Bocas.</p>
      <RssFeed />
    </div>
    <div class="card p-4">
      <h2 class="mb-2 font-semibold">
        En vivo — últimos sismos en Panamá (USGS)
        <span class="ml-2 text-xs font-normal" :class="connected ? 'text-emerald-300' : 'text-slate-500'">
          ● {{ connected ? 'socket live' : 'reconenectando…' }}
        </span>
      </h2>
      <div v-if="last" class="mb-3 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
        Nuevo sismo: <strong>{{ last.place }}</strong> ·
        <span class="num font-semibold">M{{ last.mag?.toFixed(1) }}</span> ·
        {{ new Date(last.time).toLocaleString('es-PA') }}
      </div>
      <div v-if="feed?.length" class="divide-y divide-white/5 text-sm">
        <div v-for="(e, i) in feed" :key="e.url ?? i" class="flex items-center justify-between gap-3 py-2">
          <a :href="e.url" target="_blank" class="hover:underline">{{ e.place }}</a>
          <div class="flex shrink-0 items-center gap-3 text-xs text-slate-400">
            <span>{{ new Date(e.time).toLocaleString('es-PA') }}</span>
            <span class="num font-semibold" :class="magColor(e.mag)">M{{ e.mag?.toFixed(1) }}</span>
          </div>
        </div>
      </div>
      <p v-else class="text-sm text-slate-500">Sin datos en vivo (revisa conexión con USGS).</p>
    </div>
    <div class="card p-4">
      <h2 class="mb-1 font-semibold">Histórico del catálogo (1970–hoy)</h2>
      <div class="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <button v-for="p in [['24h','24h'],['7d','7 días'],['30d','30 días'],['1y','1 año'],['all','Todo'],['custom','Custom']]" :key="p[0]"
          class="btn !px-3 !py-1 text-xs" :class="preset === p[0] ? '!border-amber-500' : ''" @click="preset = p[0]; if (p[0] !== 'custom') loadHist()">{{ p[1] }}</button>
        <template v-if="preset === 'custom'">
          <input v-model="fini" type="date" class="input !py-1 text-xs" />
          <input v-model="ffin" type="date" class="input !py-1 text-xs" />
          <button class="btn !px-3 !py-1 text-xs" @click="loadHist()">Buscar</button>
        </template>
        <span class="num ml-auto text-xs text-slate-500">{{ histLoading ? '…' : `${hist.length} eventos en rango${hist.length ? ` · ${new Date(hist[hist.length-1].time).toLocaleDateString('es-PA')} → ${new Date(hist[0].time).toLocaleDateString('es-PA')}` : ''}` }}</span>
      </div>
      <div v-if="hist.length" class="max-h-[480px] divide-y divide-white/5 overflow-y-auto text-sm">
        <div v-for="(e, i) in hist" :key="i" class="flex items-center justify-between gap-3 py-1.5">
          <span>{{ e.place }}</span>
          <div class="flex shrink-0 items-center gap-3 text-xs text-slate-400">
            <span>{{ new Date(e.time).toLocaleString('es-PA') }}</span>
            <span class="num font-semibold" :class="magColor(e.mag)">M{{ e.mag?.toFixed(1) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
