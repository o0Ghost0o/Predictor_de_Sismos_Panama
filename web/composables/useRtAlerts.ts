// Alertas en tiempo real en el navegador: se disparan cuando ingresa un sismo
// nuevo por el canal en vivo y supera el umbral de sensibilidad.
// Ajustes en localStorage ('sismos-rt-settings'). Sin backend: el umbral
// Telegram (M4.5) no cambia.
import { ref, watch } from 'vue'
import { useLiveFeed } from './useLiveFeed'

export interface RtAlert { id: string; mag: number; place: string; time: string; depth: number }
export interface RtSettings { enabled: boolean; minMag: number; sound: boolean }

const KEY = 'sismos-rt-settings'
const DEF: RtSettings = { enabled: true, minMag: 5.0, sound: true }

function loadSettings(): RtSettings {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return { ...DEF, ...JSON.parse(raw) }
  } catch { /* almacenamiento no disponible */ }
  return { ...DEF }
}

function beep() {
  try {
    const AC = window.AudioContext || (window as any).webkitAudioContext
    const ctx: AudioContext = new AC()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.connect(g); g.connect(ctx.destination)
    o.frequency.value = 660; o.type = 'sine'
    g.gain.setValueAtTime(0.12, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6)
    o.start(); o.stop(ctx.currentTime + 0.6)
  } catch { /* sin audio */ }
}

export function useRtAlerts() {
  const settings = ref<RtSettings>({ ...DEF })
  const alerts = ref<RtAlert[]>([])
  const seen = new Set<string>()
  if (process.client) {
    settings.value = loadSettings()
    watch(settings, (s) => {
      try { localStorage.setItem(KEY, JSON.stringify(s)) } catch { /* sin persistencia */ }
    }, { deep: true })
  }
  const { connected } = useLiveFeed((q: any) => {
    if (!q?.id || seen.has(q.id)) return
    seen.add(q.id)
    if (!settings.value.enabled) return
    const mag = Number(q.mag ?? 0)
    if (!(mag >= settings.value.minMag)) return
    alerts.value = [{
      id: q.id, mag, place: q.place ?? '', time: q.time ?? '', depth: Number(q.depth ?? 0)
    }, ...alerts.value].slice(0, 10)
    if (settings.value.sound) beep()
  })
  function clear() { alerts.value = [] }
  return { connected, alerts, settings, clear }
}
