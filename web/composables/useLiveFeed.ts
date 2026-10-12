// Canal live: ws://API/ws/live — snapshot + {tipo:'sismo'} en cada ingesta nueva.
// Reconexión automática. Sin dependencias.
import { ref, onMounted, onUnmounted } from 'vue'

export function useLiveFeed(onQuake?: (q: any) => void) {
  const connected = ref(false)
  const last = ref<any>(null)
  let ws: WebSocket | null = null
  let timer: any = null
  let dead = false

  function connect() {
    if (dead) return
    try {
      ws = new WebSocket('ws://localhost:8001/ws/live')
    } catch { retry(); return }
    ws.onopen = () => { connected.value = true }
    ws.onmessage = (ev) => {
      try {
        const m = JSON.parse(ev.data)
        if (m.tipo === 'sismo') { last.value = m; onQuake?.(m) }
      } catch {}
    }
    ws.onclose = () => { connected.value = false; retry() }
    ws.onerror = () => ws?.close()
  }
  function retry() { clearTimeout(timer); timer = setTimeout(connect, 5000) }
  onMounted(connect)
  onUnmounted(() => { dead = true; clearTimeout(timer); ws?.close() })
  return { connected, last }
}
