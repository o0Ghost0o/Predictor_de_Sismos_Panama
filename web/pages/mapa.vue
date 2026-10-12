<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const rango = ref('30')
const fini = ref(''); const ffin = ref('')
const hora = ref(-1) // -1 = todas
const minmag = ref(4)
const counts = ref({ total: 0, visibles: 0 })
let map: any = null
let layer: any = null
let L: any = null

const magColor = (m: number) => m >= 6 ? '#ef4444' : m >= 5 ? '#f97316' : m >= 4 ? '#eab308' : '#94a3b8'

async function draw() {
  if (!map || !L) return
  const now = Date.now()
  let desde: string, hasta: string | null = null
  if (rango.value === 'custom') { desde = fini.value; hasta = ffin.value || null }
  else if (rango.value === '24h') desde = new Date(now - 864e5).toISOString()
  else if (rango.value === 'all') desde = new Date(0).toISOString()
  else desde = new Date(now - parseInt(rango.value) * 864e5).toISOString()
  const qs: any[] = await $fetch('/api/quakes', { params: { minmag: minmag.value } })
  layer.clearLayers()
  const sel = qs
    .filter((q) => q.time >= desde && (!hasta || q.time <= hasta + 'T23:59:59') && (hora.value < 0 || new Date(q.time).getUTCHours() === hora.value))
    .sort((a, b) => a.time.localeCompare(b.time)) // recientes encima (se dibujan últimos)
  counts.value = { total: qs.length, visibles: sel.length }
  for (const q of sel) {
    layer.addLayer(L.circleMarker([q.lat, q.lon], {
      radius: 3 + (q.mag - 2) * 2.2,
      color: magColor(q.mag), weight: 1.5, fillColor: magColor(q.mag), fillOpacity: 0.45
    }).bindTooltip(`<b>M${q.mag.toFixed(1)}</b> · ${q.place}<br>${new Date(q.time).toLocaleString('es-PA')}`))
  }
}

onMounted(async () => {
  L = (await import('leaflet')).default
  await import('leaflet/dist/leaflet.css')
  map = L.map('mapa').setView([8.4, -80.5], 7)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 12, attribution: '© OpenStreetMap' }).addTo(map)
  layer = L.layerGroup().addTo(map)
  await draw()
})
onUnmounted(() => map?.remove())
watch([rango, hora, minmag], draw)
</script>
<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">Mapa de epicentros</h1>
      <p class="text-sm text-slate-400">Burbuja ∝ magnitud · lo reciente se dibuja encima · <span class="num">{{ counts.visibles }}/{{ counts.total }}</span> visibles</p>
    </div>
    <div class="flex flex-wrap items-center gap-4 text-sm">
      <label>Ventana
        <select v-model="rango" class="input ml-1">
          <option value="24h">24 horas</option><option value="7">7 días</option><option value="30">30 días</option>
          <option value="365">1 año</option><option value="all">Todo</option><option value="custom">Custom</option>
        </select>
      </label>
      <template v-if="rango === 'custom'">
        <label>Desde <input v-model="fini" type="date" class="input ml-1" /></label>
        <label>Hasta <input v-model="ffin" type="date" class="input ml-1" /></label>
        <button class="btn text-sm" @click="draw()">Buscar</button>
      </template>
      <label>Hora UTC
        <select v-model.number="hora" class="input ml-1">
          <option :value="-1">Todas</option>
          <option v-for="h in 24" :key="h - 1" :value="h - 1">{{ h - 1 }}:00</option>
        </select>
      </label>
      <label>Mín M
        <select v-model.number="minmag" class="input ml-1">
          <option :value="0">Todas</option><option :value="4">4+</option>
          <option :value="5">5+</option><option :value="6">6+</option>
        </select>
      </label>
    </div>
    <div id="mapa" class="card h-[65vh] min-h-[420px] w-full overflow-hidden" />
  </div>
</template>
