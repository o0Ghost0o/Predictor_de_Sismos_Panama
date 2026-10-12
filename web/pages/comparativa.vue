<script setup lang="ts">
const models = [
  { n: 'ETAS físico (2 params/zona)', pr: 0.240, roc: 0.774, nota: 'Mejor ROC. Re-corrido con gap cerrado.' },
  { n: 'Stack LGBM+LSTM+Trans', pr: 0.245, roc: 0.756, nota: 'Previo; profundos no re-entrenados.' },
  { n: 'Híbrido ETAS×LGBM', pr: 0.220, roc: 0.754, nota: 'etas_rate feature #1, sin ganancia de ranking.' },
  { n: 'LGBM+clima+RSI', pr: 0.224, roc: 0.747, nota: 'RSI usado pero resta en datos ralos.' },
  { n: 'LGBM+clima', pr: 0.227, roc: 0.725, nota: 'Re-corrido: +0.003 con gap cerrado + IGC.' },
  { n: 'Dial ETAS-24h (réplicas, días secuencia)', pr: 0.232, roc: 0.773, nota: 'El 2º evaluador brilla cuando importa.' },
  { n: 'Dial ETAS-24h (global re-corrido)', pr: 0.029, roc: 0.704, nota: 'Base 1.6%; Azuero post-7.7 anti-skill (tasa saturada).' },
  { n: 'Dial ETAS-24h (días calmos)', pr: 0.044, roc: 0.773, nota: 'Base 1.4%: predecir el día exacto en calma es casi azar.' },
  { n: 'LGBM+GNSS (red 88% muerta)', pr: 0.224, roc: 0.747, nota: 'Sin cobertura no hay señal.' },
  { n: 'Transformer / LSTM', pr: 0.154, roc: 0.655, nota: 'Necesitan >10⁴ eventos (tenemos 1.6k).' }
]
const { data: bt } = await useFetch<any>('/api/backtest')
const max = Math.max(...models.map((m) => m.pr))
</script>
<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Comparativa de modelos</h1>
      <p class="text-sm text-slate-400">Test temporal 2018–2026 · azar PR-AUC ≈ 0.086</p>
    </div>
    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead><tr class="border-b border-white/10 text-left text-slate-400">
          <th class="p-3">Modelo</th><th class="p-3">PR-AUC</th><th class="p-3">ROC</th><th class="p-3">Lectura</th>
        </tr></thead>
        <tbody>
          <tr v-for="m in models" :key="m.n" class="border-b border-white/5">
            <td class="p-3 font-medium">{{ m.n }}</td>
            <td class="p-3 num">{{ m.pr.toFixed(3) }}
              <div class="mt-1 h-1.5 w-24 overflow-hidden rounded bg-white/10">
                <div class="h-full bg-amber-500" :style="{ width: `${(m.pr / max) * 100}%` }" />
              </div>
            </td>
            <td class="p-3 num">{{ m.roc.toFixed(3) }}</td>
            <td class="p-3 text-slate-400">{{ m.nota }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card p-4">
      <h2 class="mb-1 font-semibold">Backtest en vivo ({{ bt?.periodo ?? '…' }})</h2>
      <p class="mb-3 text-xs text-slate-500">Umbral: {{ bt?.umbral_alerta }}</p>
      <div v-if="bt?.por_zona?.length" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead><tr class="border-b border-white/10 text-left text-slate-400">
            <th class="p-2">Zona</th><th class="p-2">Reales</th><th class="p-2">Aciertos</th>
            <th class="p-2">Falsas</th><th class="p-2">Omitidos</th>
          </tr></thead>
          <tbody>
            <tr v-for="z in bt.por_zona" :key="z.zone" class="border-b border-white/5">
              <td class="p-2 font-medium">{{ z.zone }}</td>
              <td class="p-2 num">{{ z.positivos }}</td>
              <td class="p-2 num text-emerald-300">{{ z.aciertos }}</td>
              <td class="p-2 num text-red-300">{{ z.falsas_alarmas }}</td>
              <td class="p-2 num text-yellow-300">{{ z.omitidos }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
