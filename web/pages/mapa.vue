<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const rango = ref('30')
const fini = ref(''); const ffin = ref('')
const hora = ref(-1) // -1 = todas
const minmag = ref(4)
const verPlacas = ref(true)
const sinLlave = ref(false)
const counts = ref({ total: 0, visibles: 0 })
let map: any = null
let circles: any[] = []
let placas: any[] = []
let info: any = null
let G: any = null

// Paleta apagada sobre fondo oscuro: el dato manda, no el color.
const magColor = (m: number) => m >= 6 ? '#f87171' : m >= 5 ? '#d19a6b' : m >= 4 ? '#a8a29e' : '#52525b'

// Mapa oscuro y silencioso: sin etiquetas ni puntos de interés.
const ESTILO = [
  { elementType: 'geometry', stylers: [{ color: '#111826' }] },
  { elementType: 'labels', stylers: [{ visibility: 'off' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0a0e14' }] },
  { featureType: 'administrative.country', elementType: 'geometry.stroke', stylers: [{ color: '#2b3648' }] }
]

function loadGoogle(key: string): Promise<any> {
  const w = window as any
  if (w.google?.maps) return Promise.resolve(w.google)
  return new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&v=weekly`
    s.async = true
    s.onload = () => resolve(w.google)
    s.onerror = reject
    document.head.appendChild(s)
  })
}

async function draw() {
  if (!map || !G) return
  const now = Date.now()
  let desde: string, hasta: string | null = null
  if (rango.value === 'custom') { desde = fini.value; hasta = ffin.value || null }
  else if (rango.value === '24h') desde = new Date(now - 864e5).toISOString()
  else if (rango.value === 'all') desde = new Date(0).toISOString()
  else desde = new Date(now - parseInt(rango.value) * 864e5).toISOString()
  const qs: any[] = await $fetch('/api/quakes', { params: { minmag: minmag.value } })
  for (const c of circles) c.setMap(null)
  circles = []
  const sel = qs
    .filter((q) => q.time >= desde && (!hasta || q.time <= hasta + 'T23:59:59') && (hora.value < 0 || new Date(q.time).getUTCHours() === hora.value))
    .sort((a, b) => a.time.localeCompare(b.time)) // recientes encima (se dibujan últimos)
  counts.value = { total: qs.length, visibles: sel.length }
  for (const q of sel) {
    const col = magColor(q.mag)
    const c = new G.maps.Circle({
      map, center: { lat: q.lat, lng: q.lon },
      radius: 9000 * Math.max(0.6, q.mag - 3),
      strokeColor: col, strokeWeight: 1, strokeOpacity: 0.8,
      fillColor: col, fillOpacity: 0.28
    })
    c.addListener('click', (ev: any) => {
      info.setContent(`<div class="iw-sismo"><b>M${q.mag.toFixed(1)}</b> · ${Math.round(q.depth)} km<br>${q.place}<br>${new Date(q.time).toLocaleString('es-PA', { timeZone: 'UTC' })} UTC</div>`)
      info.setPosition(ev.latLng)
      info.open(map)
    })
    circles.push(c)
  }
}

onMounted(async () => {
  const key = useRuntimeConfig().public.googleMapsKey as string
  if (!key) { sinLlave.value = true; return }
  try {
    G = await loadGoogle(key)
  } catch { sinLlave.value = true; return }
  map = new G.maps.Map(document.getElementById('mapa') as HTMLElement, {
    center: { lat: 8.4, lng: -80.5 }, zoom: 7,
    styles: ESTILO, disableDefaultUI: true, zoomControl: true, fullscreenControl: true,
    backgroundColor: '#0a0e14'
  })
  info = new G.maps.InfoWindow({ maxWidth: 300 })
  try {
    const gj: any = await $fetch('/plates/pb2002.json')
    for (const f of gj.features ?? []) {
      const coords = f.geometry?.type === 'LineString'
        ? f.geometry.coordinates.map(([lng, lat]: number[]) => ({ lat, lng }))
        : []
      if (!coords.length) continue
      const sub = f.properties?.Type === 'subduction'
      const line = new G.maps.Polyline({
        map, path: coords, geodesic: true,
        strokeColor: sub ? '#e8b34b' : '#7d8aa0', strokeWeight: sub ? 2 : 1.2, strokeOpacity: sub ? 0.95 : 0.6,
        ...(sub ? {} : { icons: [{ icon: { path: 'M 0,-1 0,1', strokeOpacity: 1, scale: 2 }, offset: '0', repeat: '9px' }], strokeOpacity: 0 })
      })
      placas.push(line)
    }
  } catch { /* sin placas igual hay mapa */ }
  const legend = document.createElement('div')
  legend.className = 'plate-legend'
  legend.innerHTML = `Límites de placa PB2002 (Bird, 2003)<br><span class="k sub"></span>Subducción (fosa)<br><span class="k otr"></span>Otro límite de placa<br><span class="k sis"></span>Epicentro M4+ (tamaño ∝ M)`
  map.controls[G.maps.ControlPosition.RIGHT_BOTTOM].push(legend)
  await draw()
})
onUnmounted(() => { circles = []; placas = []; map = null })
watch([rango, hora, minmag], draw)
watch(verPlacas, (v) => { for (const l of placas) l.setMap(v ? map : null) })
</script>
<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">Mapa tectónico y sismicidad</h1>
      <p class="text-sm text-slate-400">Epicentros USGS sobre los límites de placa · lo reciente se dibuja encima · <span class="num">{{ counts.visibles }}/{{ counts.total }}</span> visibles</p>
    </div>
    <p v-if="sinLlave" class="card p-4 text-sm text-slate-400">Falta la llave de Google Maps: define <code>NUXT_PUBLIC_GOOGLE_MAPS_KEY</code> en <code>web/.env</code> (local) o en la UI de Coolify.</p>
    <template v-else>
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
    </template>
  </div>
</template>
<style>
.plate-legend { background: #111826ee; border: 1px solid #ffffff14; border-radius: .5rem; padding: .5rem .65rem; font-size: 11px; line-height: 1.9; color: #c6cfdd; margin: 0 10px 24px 0; }
.plate-legend .k { display: inline-block; width: 22px; height: 0; vertical-align: middle; margin-right: 6px; }
.plate-legend .sub { border-top: 2px solid #e8b34b; }
.plate-legend .otr { border-top: 2px dashed #7d8aa0; }
.plate-legend .sis { width: 8px; height: 8px; border-radius: 50%; background: #a8a29e; margin: 0 9px 0 7px; }
/* Chrome propio de Google en tema oscuro (la atribución sigue visible, como exige ToS). */
#mapa .iw-sismo { color: #e8edf5; font-size: 13px; line-height: 1.55; }
#mapa .iw-sismo b { color: #fff; }
#mapa .gm-style .gm-style-iw-c { background: #111826; border: 1px solid #ffffff14; border-radius: .75rem; padding: 14px 18px 14px 14px; box-shadow: 0 8px 24px #000c; }
#mapa .gm-style .gm-style-iw-d { overflow: auto !important; }
#mapa .gm-style .gm-style-iw-tc::after { background: #111826; }
#mapa .gm-style .gm-style-iw-c button.gm-ui-hover-effect span { filter: invert(0.9); }
#mapa .gmnoprint button, #mapa .gm-control-active { background: #111826 !important; }
#mapa .gmnoprint button img, #mapa .gm-control-active img { filter: invert(0.85); }
#mapa .gmnoprint, #mapa .gmnoprint a { color: #93a0b4 !important; }
#mapa .gm-style-cc { background: #0a0e14d9 !important; border-radius: .375rem; padding: 0 4px; }
#mapa .gm-style-cc, #mapa .gm-style-cc a, #mapa .gm-style-cc span { color: #93a0b4 !important; font-size: 10px !important; }
</style>
