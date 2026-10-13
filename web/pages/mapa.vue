<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const rango = ref('30')
const fini = ref(''); const ffin = ref('')
const hora = ref(-1) // -1 = todas
const minmag = ref(4)
const verPlacas = ref(true)
const counts = ref({ total: 0, visibles: 0 })
let map: any = null
let layer: any = null
let placas: any = null
let L: any = null

// Paleta apagada sobre fondo oscuro: el dato manda, no el color.
const magColor = (m: number) => m >= 6 ? '#f87171' : m >= 5 ? '#d19a6b' : m >= 4 ? '#a8a29e' : '#52525b'

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
      radius: 2 + Math.max(0, q.mag - 2) * 1.6,
      color: magColor(q.mag), weight: 1, fillColor: magColor(q.mag), fillOpacity: 0.35
    }).bindTooltip(`<b>M${q.mag.toFixed(1)}</b> · ${Math.round(q.depth)} km · ${q.place}<br>${new Date(q.time).toLocaleString('es-PA', { timeZone: 'UTC' })} UTC`))
  }
}

onMounted(async () => {
  L = (await import('leaflet')).default
  await import('leaflet/dist/leaflet.css')
  map = L.map('mapa', { zoomControl: true }).setView([8.4, -80.5], 7)
  // Fondo oscuro sin ruido: solo costas y fronteras tenues.
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 12, attribution: '© OpenStreetMap · © CARTO · Límites de placa PB2002 (Bird, 2003)'
  }).addTo(map)
  layer = L.layerGroup().addTo(map)
  try {
    const gj = await $fetch('/plates/pb2002.json')
    placas = L.geoJSON(gj, {
      style: (f: any) => f?.properties?.Type === 'subduction'
        ? { color: '#e8b34b', weight: 1.6, opacity: 0.9 }
        : { color: '#7d8aa0', weight: 1, opacity: 0.55, dashArray: '4 3' }
    }).addTo(map)
  } catch { /* sin placas igual hay mapa */ }
  const legend = L.control({ position: 'bottomright' })
  legend.onAdd = () => {
    const d = L.DomUtil.create('div', 'plate-legend')
    d.innerHTML = `<span class="k sub"></span>Subducción (fosa)<br><span class="k otr"></span>Otro límite de placa<br><span class="k sis"></span>Epicentro M4+ (tamaño ∝ M)`
    return d
  }
  legend.addTo(map)
  await draw()
})
onUnmounted(() => map?.remove())
watch([rango, hora, minmag], draw)
watch(verPlacas, (v) => { if (!map || !placas) return; v ? placas.addTo(map) : map.removeLayer(placas) })
</script>
<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">Mapa tectónico y sismicidad</h1>
      <p class="text-sm text-slate-400">Epicentros USGS sobre los límites de placa · lo reciente se dibuja encima · <span class="num">{{ counts.visibles }}/{{ counts.total }}</span> visibles</p>
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
      <label class="flex items-center gap-2"><input v-model="verPlacas" type="checkbox" class="accent-amber-500" /> Placas</label>
    </div>
    <div id="mapa" class="card h-[65vh] min-h-[420px] w-full overflow-hidden" />
  </div>
</template>
<style>
.plate-legend { background: #111826ee; border: 1px solid #ffffff14; border-radius: .5rem; padding: .5rem .65rem; font-size: 11px; line-height: 1.9; color: #c6cfdd; }
.plate-legend .k { display: inline-block; width: 22px; height: 0; vertical-align: middle; margin-right: 6px; }
.plate-legend .sub { border-top: 2px solid #e8b34b; }
.plate-legend .otr { border-top: 2px dashed #7d8aa0; }
.plate-legend .sis { width: 8px; height: 8px; border-radius: 50%; background: #a8a29e; margin: 0 9px 0 7px; }
.leaflet-container { background: #0a0e14; font-family: inherit; }
</style>
