<script setup lang="ts">
const levels = [
  { n: 3, c: 'emerald', t: 'Tranquilo', d: 'Baja probabilidad esta semana. Vida normal.' },
  { n: 4, c: 'yellow', t: 'Moderado', d: 'Posible sismo leve (M4+). Actividad habitual de Panamá.' },
  { n: 5, c: 'orange', t: 'Moderado-Alto', d: 'Posible sismo intermedio (M5+). Atento a réplicas.' },
  { n: 6, c: 'red', t: 'Alto', d: 'Posible sismo fuerte (M6+). Revisa tu plan familiar, sin pánico.' }
]
const { data: pro } = await useFetch<any>('/api/prospective')
const resColor = (r: string) => r === 'acierto' ? 'text-emerald-300' : r === 'pendiente' ? 'text-slate-400'
  : r === 'correcto_negativo' ? 'text-slate-500' : 'text-red-300'
</script>
<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Alertas — escala 3–6</h1>
      <p class="text-sm text-slate-400">Niveles 7–10 no se emiten: 5 sismos M7+ en 56 años no alcanzan para entrenar. Investigación, no alerta oficial.</p>
    </div>
    <div class="grid gap-4 sm:grid-cols-2">
      <div v-for="l in levels" :key="l.n" class="card p-4">
        <LevelBadge :nivel="l.n" />
        <p class="mt-2 text-sm text-slate-300">{{ l.d }}</p>
      </div>
    </div>
    <div class="card p-4">
      <h2 class="mb-1 font-semibold">Mini-CSEP: pronósticos prospectivos reales</h2>
      <p class="mb-3 text-xs text-slate-500">Emitidos hacia adelante, calificados al cerrar la ventana de 7 días. {{ pro?.nota }}</p>
      <div v-if="pro?.log?.length" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead><tr class="border-b border-white/10 text-left text-slate-400">
            <th class="p-2">Emitido</th><th class="p-2">Zona</th><th class="p-2">M4+</th>
            <th class="p-2">M5+</th><th class="p-2">M6+</th><th class="p-2">Resultado</th>
          </tr></thead>
          <tbody>
            <tr v-for="(r, i) in pro.log" :key="i" class="border-b border-white/5">
              <td class="p-2 num">{{ r.issued }} → {{ r.target_end }}</td>
              <td class="p-2 font-medium">{{ r.zone }}</td>
              <td class="p-2 num">{{ (r.p4 * 100).toFixed(1) }}%</td>
              <td class="p-2 num">{{ (r.p5 * 100).toFixed(1) }}%</td>
              <td class="p-2 num">{{ (r.p6 * 100).toFixed(2) }}%</td>
              <td class="p-2" :class="resColor(r.resultado ?? 'pendiente')">{{ r.resultado ?? 'pendiente' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
