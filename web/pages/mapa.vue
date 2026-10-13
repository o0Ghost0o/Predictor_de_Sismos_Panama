<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const rango = ref('7')
const fini = ref(''); const ffin = ref('')
const hora = ref(-1) // -1 = todas
const minmag = ref(4)
const verPlacas = ref(true)
const sinLlave = ref(false)
const counts = ref({ total: 0, visibles: 0 })
const orden = ref<'fecha' | 'mag'>('fecha') // fecha sigue siendo el orden por defecto
const soloSel = ref(false)
const vel = ref(2) // eventos por paso (tick 200 ms)
const cursor = ref(0) // ms: los eventos con time <= cursor están visibles
const rangoMs = ref({ min: 0, max: 0 })
const playing = ref(false)
const loop = ref(false)
const verCalor = ref(false)
let timer: any = null
let times: number[] = []
let ordenT: number[] = [] // tiempos ordenados para avanzar por evento
let heat: any = null
// Microplacas y bloques menores PB2002 relevantes en la región.
const MICRO = new Set(['PM', 'ND', 'CR', 'GP'])
const PLACAS_NOMBRES = [
  { n: 'COCOS', lat: 5.6, lng: -85.4 },
  { n: 'NAZCA', lat: 4.4, lng: -81.6 },
  { n: 'CARIBE', lat: 10.9, lng: -80.1 },
  { n: 'MICROPLACA DE PANAMÁ', lat: 8.75, lng: -80.35 },
  { n: 'BLOQUE N. DE LOS ANDES', lat: 7.6, lng: -77.05 }
]
let nombres: any[] = []
let cancelado = false // true tras unmount: aborta continuaciones async pendientes
const verFallas = ref(true)
let fallas: any[] = []

// Familia de falla GEM por slip_type: inversa (compresiva), rumbo, normal u otra.
const fallaColor = (s: string) => /reverse|thrust/i.test(s ?? '') ? '#e07856'
  : /dextral|sinistral|transform|strike/i.test(s ?? '') ? '#c9a86a' : '#8a8f98'
const base = ref<any[]>([]) // visibles, en orden de dibujo (recientes últimos), alineado con circles
const selCi = ref(-1) // índice en circles del seleccionado
const lista = computed(() => {
  const arr = base.value.map((q, ci) => ({ q, ci }))
  arr.sort((a, b) => orden.value === 'mag'
    ? b.q.mag - a.q.mag || b.q.time.localeCompare(a.q.time)
    : b.q.time.localeCompare(a.q.time))
  return arr
})
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
  base.value = sel
  selCi.value = -1
  times = sel.map((q) => Date.parse(q.time))
  ordenT = [...times].sort((a, b) => a - b)
  rangoMs.value = times.length ? { min: Math.min(...times), max: Math.max(...times) } : { min: 0, max: 0 }
  cursor.value = rangoMs.value.max
  buildHeat()
  aplicarVis()
  for (const q of sel) {
    const col = magColor(q.mag)
    const c = new G.maps.Circle({
      map, center: { lat: q.lat, lng: q.lon },
      radius: 9000 * Math.max(0.6, q.mag - 3),
      strokeColor: col, strokeWeight: 1, strokeOpacity: 0.8,
      fillColor: col, fillOpacity: 0.28
    })
    c.addListener('click', (ev: any) => {
      info.setContent(ficha(q))
      info.setPosition(ev.latLng)
      info.open(map)
    })
    circles.push(c)
  }
}

const ficha = (q: any) => `<div class="iw-sismo"><b>M${q.mag.toFixed(1)}</b> · ${Math.round(q.depth)} km<br>${q.place}<br>${new Date(q.time).toLocaleString('es-PA', { timeZone: 'UTC' })} UTC</div>`
const fmtList = (t: string) => new Date(t).toLocaleString('es-PA', { timeZone: 'UTC', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })

function toggleFallas(v: boolean) {
  for (const l of fallas) l.setMap(v ? map : null)
}

function aplicarVis() {
  if (!map) return
  if (soloSel.value) {
    // Un solo evento: el más reciente <= cursor; la lista lo resalta.
    let idx = -1
    for (let j = 0; j < times.length; j++) if (times[j] <= cursor.value) idx = j
    selCi.value = idx
    circles.forEach((c, j) => c.setMap(j === idx ? map : null))
    return
  }
  circles.forEach((c, j) => c.setMap(
    times[j] <= cursor.value && (selCi.value < 0 || j === selCi.value) ? map : null))
}

function play() {
  if (!map || !base.value.length) return
  let pos = ordenT.filter((t) => t <= cursor.value).length
  if (pos >= ordenT.length) pos = 0
  playing.value = true
  clearInterval(timer)
  timer = setInterval(() => {
    pos = Math.min(pos + (soloSel.value ? 1 : vel.value), ordenT.length)
    cursor.value = ordenT[pos - 1] ?? rangoMs.value.min
    if (pos >= ordenT.length) {
      if (loop.value) pos = 0
      else { pausar(); return }
    }
    aplicarVis()
  }, 200)
}

function pausar() {
  playing.value = false
  clearInterval(timer)
  aplicarVis()
}

// Calor sin depender de la capa de mapas de Google eliminada en Maps JS v3.65.
// OverlayView + canvas 2D con la misma pinta: radio 22 px, opacidad 0.55 y
// peso 2^(M-4) por evento, sin librerias externas.
const CALOR_RADIO = 22
const CALOR_OPACIDAD = 0.55
// Paradas visibles del degradado original (se omite la primera, transparente).
const CALOR_PARADAS: Array<[number, number, number, number]> = [
  [232, 179, 75, 0.55], [209, 154, 107, 0.75], [248, 113, 113, 0.9]
]

function calorColor(t: number): [number, number, number, number] {
  const x = Math.min(1, Math.max(0, t)) * (CALOR_PARADAS.length - 1)
  const i = Math.min(CALOR_PARADAS.length - 2, Math.floor(x))
  const f = x - i
  const a = CALOR_PARADAS[i], b = CALOR_PARADAS[i + 1]
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f]
}

function crearCalor(google: any, mapa: any, pts: Array<{ lat: number; lng: number; w: number }>) {
  const overlay = new google.maps.OverlayView()
  let div: HTMLDivElement | null = null
  let canvas: HTMLCanvasElement | null = null
  const maxW = Math.max(1, ...pts.map((p) => p.w))
  overlay.onAdd = function (this: any) {
    div = document.createElement('div')
    div.style.position = 'absolute'
    div.style.top = '0'
    div.style.left = '0'
    div.style.pointerEvents = 'none'
    div.style.opacity = String(CALOR_OPACIDAD)
    canvas = document.createElement('canvas')
    div.appendChild(canvas)
    // overlayMouseTarget: por encima de los circulos de epicentro (overlayLayer),
    // con pointerEvents none para no bloquear clics. Debajo quedaba oculto.
    this.getPanes().overlayMouseTarget.appendChild(div)
  }
  overlay.draw = function (this: any) {
    const proj = this.getProjection()
    const cont = mapa.getDiv() as HTMLElement
    if (!proj || !div || !canvas || !cont) return
    const W = cont.offsetWidth, H = cont.offsetHeight
    if (!W || !H) return
    const dpr = Math.min(2, window.devicePixelRatio || 1)
    canvas.width = Math.round(W * dpr)
    canvas.height = Math.round(H * dpr)
    canvas.style.width = `${W}px`
    canvas.style.height = `${H}px`
    div.style.width = `${W}px`
    div.style.height = `${H}px`
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.globalCompositeOperation = 'lighter'
    for (const p of pts) {
      const px = proj.fromLatLngToDivPixel(new google.maps.LatLng(p.lat, p.lng))
      if (!px) continue
      const x = px.x * dpr, y = px.y * dpr
      const R = CALOR_RADIO * dpr
      if (x < -R || y < -R || x > canvas.width + R || y > canvas.height + R) continue
      // Escala logarítmica: un M7 pesa ~9x más que un M4 y en lineal
      // satura el enjambre a un bloque blanco. Picos más bajos y anillo
      // intermedio para que se lean varios lóbulos en vez de uno solo.
      const t = Math.max(0.1, Math.log(1 + p.w) / Math.log(1 + maxW))
      const [r, g, b, a] = calorColor(t)
      const rgb = `${Math.round(r)},${Math.round(g)},${Math.round(b)}`
      const grad = ctx.createRadialGradient(x, y, 0, x, y, R)
      grad.addColorStop(0, `rgba(${rgb},${(a * 0.5).toFixed(3)})`)
      grad.addColorStop(0.55, `rgba(${rgb},${(a * 0.16).toFixed(3)})`)
      grad.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = grad
      ctx.beginPath()
      ctx.arc(x, y, R, 0, Math.PI * 2)
      ctx.fill()
    }
  }
  overlay.onRemove = function (this: any) {
    div?.remove()
    div = null
    canvas = null
  }
  overlay.setMap(mapa)
  return overlay
}

function buildHeat() {
  if (heat) { heat.setMap(null); heat = null }
  if (map && G && verCalor.value && base.value.length) {
    heat = crearCalor(G, map, base.value.map((q) => ({ lat: q.lat, lng: q.lon, w: Math.pow(2, q.mag - 4) })))
  }
}

function select(item: { q: any; ci: number }) {
  if (!map || !G) return
  const q = item.q
  if (soloSel.value) cursor.value = times[item.ci] ?? cursor.value
  else selCi.value = item.ci
  aplicarVis()
  map.panTo({ lat: q.lat, lng: q.lon })
  info.setContent(ficha(q))
  info.setPosition({ lat: q.lat, lng: q.lon })
  info.open(map)
}

onMounted(async () => {
  const key = useRuntimeConfig().public.googleMapsKey as string
  if (!key) { sinLlave.value = true; return }
  try {
    G = await loadGoogle(key)
  } catch { sinLlave.value = true; return }
  if (cancelado) return
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
      const micro = !sub && (MICRO.has(f.properties?.PlateA) || MICRO.has(f.properties?.PlateB))
      const line = new G.maps.Polyline({
        map, path: coords, geodesic: true,
        strokeColor: sub ? '#e8b34b' : micro ? '#9fb4d8' : '#7d8aa0',
        strokeWeight: sub ? 2 : micro ? 1.5 : 1.2,
        strokeOpacity: sub ? 0.95 : micro ? 0.85 : 0.6,
        ...(!sub && !micro ? { icons: [{ icon: { path: 'M 0,-1 0,1', strokeOpacity: 1, scale: 2 }, offset: '0', repeat: '9px' }], strokeOpacity: 0 } : {})
      })
      placas.push(line)
    }
    for (const p of PLACAS_NOMBRES) {
      nombres.push(new G.maps.Marker({
        position: { lat: p.lat, lng: p.lng }, map, clickable: false,
        icon: { path: G.maps.SymbolPath.CIRCLE, scale: 0.1, fillOpacity: 0, strokeOpacity: 0 },
        label: { text: p.n, color: '#8fa0b8', fontSize: '10px', fontWeight: '600', className: 'plate-name' }
      }))
    }
  } catch { /* sin placas igual hay mapa */ }
  try {
    const fj: any = await $fetch('/plates/faults.json')
    for (const f of fj.features ?? []) {
      const g = f.geometry
      const lines = g?.type === 'LineString' ? [g.coordinates]
        : g?.type === 'MultiLineString' ? g.coordinates : []
      for (const coords of lines) {
        const path = coords.map(([lng, lat]: number[]) => ({ lat, lng }))
        if (!path.length) continue
        const p = f.properties ?? {}
        const line = new G.maps.Polyline({
          map, path, geodesic: true,
          strokeColor: fallaColor(p.slip_type), strokeWeight: 1.1, strokeOpacity: 0.8
        })
        const titulo = [p.name, p.slip_type, p.net_slip_rate ? `${p.net_slip_rate} mm/año` : null].filter(Boolean).join(' · ')
        if (titulo) line.addListener('click', (ev: any) => {
          info.setContent(`<div class="iw-sismo"><b>Falla activa</b><br>${titulo}</div>`)
          info.setPosition(ev.latLng)
          info.open(map)
        })
        fallas.push(line)
      }
    }
    if (!verFallas.value) for (const l of fallas) l.setMap(null)
  } catch { /* sin fallas igual hay mapa */ }
  const legend = document.createElement('div')
  legend.className = 'plate-legend'
  legend.innerHTML = `Límites de placa PB2002 (Bird, 2003) · Fallas GEM<br><span class="k sub"></span>Subducción (fosa)<br><span class="k mic"></span>Microplaca (PM · ND · GP)<br><span class="k fal"></span>Falla activa (clic: nombre)<br><span class="k otr"></span>Otro límite de placa<br><span class="k sis"></span>Epicentro M4+ (tamaño ∝ M)`
  if (cancelado || !map) return
  map.controls[G.maps.ControlPosition.RIGHT_BOTTOM].push(legend)
  await draw()
})
onUnmounted(() => { cancelado = true; clearInterval(timer); circles = []; placas = []; nombres = []; times = []; if (heat) { heat.setMap(null); heat = null } map = null })
watch([rango, hora, minmag], draw)
watch(verPlacas, (v) => { for (const l of [...placas, ...nombres]) l.setMap(v ? map : null) })
watch(cursor, aplicarVis)
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
      <label class="flex items-center gap-2"><input v-model="verFallas" type="checkbox" class="accent-amber-500" @change="toggleFallas(($event.target as HTMLInputElement).checked)" /> Fallas</label>
      <label class="flex items-center gap-2"><input v-model="soloSel" type="checkbox" class="accent-amber-500" @change="aplicarVis()" /> Solo seleccionado</label>
      <label class="flex items-center gap-2"><input v-model="verCalor" type="checkbox" class="accent-amber-500" @change="buildHeat()" /> Calor</label>
      </div>
      <div class="card flex flex-col gap-3 p-3 sm:flex-row sm:items-center">
        <button class="btn shrink-0 px-4 text-sm" :disabled="!base.length" @click="playing ? pausar() : play()">{{ playing ? 'Pausar' : 'Reproducir' }}</button>
        <input v-model.number="cursor" type="range" :min="rangoMs.min" :max="rangoMs.max" :disabled="!base.length" step="3600000" class="w-full accent-amber-500" @input="pausar()" title="Arrastrar para reproducir manualmente" />
        <span class="num shrink-0 text-xs text-slate-300">{{ base.length ? fmtList(new Date(cursor).toISOString()) + ' UTC' : '—' }}</span>
        <select v-model.number="vel" class="input shrink-0 !rounded-md !px-2 !py-1 text-xs" title="Eventos por paso">
          <option :value="1">1 ev</option><option :value="2">2 ev</option>
          <option :value="5">5 ev</option><option :value="10">10 ev</option>
        </select>
        <label class="flex shrink-0 items-center gap-2 text-xs text-slate-400"><input v-model="loop" type="checkbox" class="accent-amber-500" /> Repetir</label>
      </div>
      <div class="flex flex-col gap-4 lg:flex-row">
        <div id="mapa" class="card h-[65vh] min-h-[420px] w-full overflow-hidden lg:flex-1" />
        <aside class="card flex max-h-[40vh] flex-col overflow-hidden lg:max-h-[65vh] lg:min-h-[420px] lg:w-[340px] lg:shrink-0">
          <div class="flex items-center justify-between border-b border-white/10 px-4 py-2">
            <p class="text-[11px] uppercase tracking-wide text-slate-500">Eventos · <span class="num">{{ lista.length }}</span></p>
            <select v-model="orden" class="input ml-2 !rounded-md !px-2 !py-1 text-[11px]" title="Orden">
              <option value="fecha">Fecha</option>
              <option value="mag">Magnitud</option>
            </select>
          </div>
          <ul class="divide-y divide-white/5 overflow-y-auto">
            <li v-for="item in lista" :key="item.q.id ?? item.q.time + item.q.place">
              <button class="flex w-full items-center gap-3 px-4 py-2 text-left hover:bg-white/5" :class="item.ci === selCi ? 'bg-white/5' : ''" @click="select(item)">
                <span class="num w-12 shrink-0 text-sm font-semibold" :style="{ color: magColor(item.q.mag) }">M{{ item.q.mag.toFixed(1) }}</span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-[13px] text-slate-200">{{ item.q.place }}</span>
                  <span class="num block text-[11px] text-slate-500">{{ fmtList(item.q.time) }} UTC · {{ Math.round(item.q.depth) }} km</span>
                </span>
              </button>
            </li>
          </ul>
          <p v-if="!lista.length" class="px-4 py-6 text-sm text-slate-500">Sin eventos en esta ventana.</p>
        </aside>
      </div>
    </template>
  </div>
</template>
<style>
.plate-legend { background: #111826ee; border: 1px solid #ffffff14; border-radius: .5rem; padding: .5rem .65rem; font-size: 11px; line-height: 1.9; color: #c6cfdd; margin: 0 10px 24px 0; }
.plate-legend .k { display: inline-block; width: 22px; height: 0; vertical-align: middle; margin-right: 6px; }
.plate-legend .sub { border-top: 2px solid #e8b34b; }
.plate-legend .otr { border-top: 2px dashed #7d8aa0; }
.plate-legend .mic { border-top: 2px solid #9fb4d8; }
.plate-legend .fal { border-top: 2px solid #e07856; }
.plate-name { letter-spacing: .18em; text-shadow: 0 1px 3px #000, 0 0 8px #000; font-family: inherit; white-space: nowrap; }
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
