<script setup lang="ts">
import { ref, onMounted } from 'vue'

const estado = ref<'idle' | 'listo' | 'activado' | 'error' | 'no-soportado'>('idle')
const detalle = ref('')
const paso = ref('')

function keyToBytes(key: string) {
  const pad = '='.repeat((4 - (key.length % 4)) % 4)
  const bin = atob((key + pad).replace(/-/g, '+').replace(/_/g, '/'))
  return Uint8Array.from(bin, (c) => c.charCodeAt(0))
}

onMounted(async () => {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) { estado.value = 'no-soportado'; return }
  try {
    const reg = await navigator.serviceWorker.register('/sw-push.js')
    const sub = await reg.pushManager.getSubscription()
    estado.value = sub ? 'activado' : 'listo'
  } catch (e: any) { estado.value = 'error'; detalle.value = String(e?.message ?? e) }
})

async function activar() {
  estado.value = 'idle'; detalle.value = ''; paso.value = ''
  try {
    paso.value = 'permiso del navegador'
    if (Notification.permission === 'denied') throw new Error('permiso denegado en el navegador')
    if (Notification.permission !== 'granted') {
      if (await Notification.requestPermission() !== 'granted') throw new Error('permiso no concedido')
    }
    paso.value = 'registro del worker'
    const reg = await navigator.serviceWorker.register('/sw-push.js')
    paso.value = 'llave del servidor'
    const { publicKey } = await $fetch<{ publicKey: string }>('/api/push/vapid')
    paso.value = 'suscripción push'
    const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyToBytes(publicKey) })
    paso.value = 'envío al gateway'
    await $fetch('/api/push/subscribe', { method: 'POST', body: { subscription: sub.toJSON() } })
    estado.value = 'activado'
  } catch (e: any) {
    estado.value = 'error'
    detalle.value = `${paso.value}: ${e?.name ?? ''} ${String(e?.message ?? e)}`.trim()
    console.error('[push] falló en', paso.value, e)
  }
}
</script>
<template>
  <div class="flex flex-wrap items-center gap-3">
    <button v-if="estado !== 'activado'" class="btn text-xs" :disabled="estado === 'idle' || estado === 'no-soportado'" @click="activar()">
      {{ estado === 'error' ? 'Reintentar push' : 'Activar push del servidor' }}
    </button>
    <p class="text-xs" :class="estado === 'activado' ? 'text-green-400' : 'text-slate-500'">
      <template v-if="estado === 'activado'">Push activo en este navegador</template>
      <template v-else-if="estado === 'no-soportado'">Este navegador no soporta push</template>
      <template v-else-if="estado === 'error'">No se pudo activar{{ detalle ? ': ' + detalle : '' }}. Abre la consola (F12) para el detalle. Pista: en Brave activa "Usar servicios de Google para push" en ajustes; en Safari de escritorio el push solo funciona en apps web instaladas.</template>
      <template v-else>Push del servidor apagado en este navegador</template>
    </p>
  </div>
</template>
