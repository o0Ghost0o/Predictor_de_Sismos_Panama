<script setup lang="ts">
const { data: latest } = await useFetch<any[]>('/api/risk')
const hoy = new Date().toISOString().slice(0, 10)
const fecha = ref(latest.value?.[0]?.date ?? hoy)
const { data: zones, refresh, pending } = await useFetch<any[]>('/api/risk', { query: { date: fecha } })
watch(fecha, () => refresh())
</script>
<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Pronóstico por fecha</h1>
      <p class="text-sm text-slate-400">Hindcast: elige cualquier fecha 1970–hoy y compara contra lo que realmente pasó (dato USGS).</p>
    </div>
    <div class="flex items-center gap-3">
      <input v-model="fecha" type="date" min="1970-01-01" :max="hoy" class="input" />
      <button class="btn text-sm" :disabled="pending" @click="refresh()">{{ pending ? '…' : 'Consultar' }}</button>
    </div>
    <div v-if="zones?.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <ZoneCard v-for="z in [...zones].sort((a, b) => b.nivel - a.nivel)" :key="z.zone"
        :zone="z.zone" :nivel="z.nivel" :p4="z.p_M4_7d" :p5="z.p_M5_7d" :p6="z.p_M6_7d"
        :mensaje="z.mensaje" :observed="z.observed_M4_next7d" :curva="z.curva_diaria" :curva5="z.curva_m5" :curva6="z.curva_m6" :bandas="z.bandas_gr" :fecha="z.date" />
    </div>
    <p class="text-xs text-slate-500">Fechas sugeridas: 2025-06-15 · 2021-07-14 (pre-M6.7) · 2026-10-05 (pre-M7.7, el modelo falló ahí).</p>
  </div>
</template>
