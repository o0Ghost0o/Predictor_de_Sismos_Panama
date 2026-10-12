<script setup lang="ts">
defineProps<{ zone: string; nivel: number; p4: number; p5: number; p6: number; mensaje?: string; observed?: number | null; curva?: number[]; curva5?: number[]; curva6?: number[]; bandas?: Record<string, number>; fecha?: string }>()
const dia = (i: number, fecha?: string) => {
  if (!fecha) return `+${i + 1}`
  const d = new Date(fecha + 'T12:00:00'); d.setDate(d.getDate() + i + 1)
  return `${d.getDate()}/${d.getMonth() + 1}`
}
</script>
<template>
  <div class="card p-4">
    <div class="mb-2 flex items-center justify-between">
      <h3 class="font-semibold">{{ zone }}</h3>
      <LevelBadge :nivel="nivel" />
    </div>
    <div class="space-y-2 text-xs text-slate-400">
      <div v-if="p4 >= 0.01"><div class="mb-1 flex justify-between"><span>M4+ 7d</span><span class="num text-slate-200">{{ (p4 * 100).toFixed(1) }}%</span></div><RiskBar :value="p4" /></div>
      <div v-if="p5 >= 0.01"><div class="mb-1 flex justify-between"><span>M5+ 7d</span><span class="num text-slate-200">{{ (p5 * 100).toFixed(1) }}%</span></div><RiskBar :value="p5" color="bg-orange-500" /></div>
      <div v-if="p6 >= 0.01"><div class="mb-1 flex justify-between"><span>M6+ 7d</span><span class="num text-slate-200">{{ (p6 * 100).toFixed(2) }}%</span></div><RiskBar :value="p6" color="bg-red-500" /></div>
      <div v-for="(v, m) in (bandas ?? {})" :key="m"><div class="mb-1 flex justify-between"><span>M{{ m }}+ 7d <em class="not-italic text-slate-500">(GR)</em></span><span class="num text-slate-200">{{ (v * 100).toFixed(4) }}%</span></div><RiskBar :value="v" color="bg-purple-500" /></div>
    </div>
    <div v-if="curva?.length && (p4 >= 0.01 || Math.max(...curva) >= 0.01)" class="mt-3">
      <p class="mb-1 text-[11px] uppercase tracking-wide text-slate-500">Curva 7 días — M4+ por día</p>
      <div class="flex h-10 items-end gap-1">
        <div v-for="(c, i) in curva" :key="i" class="flex-1 rounded-sm bg-amber-500/80" :style="{ height: `${Math.max(4, Math.min(100, c * 400))}%` }" :title="`D+${i + 1}: ${(c * 100).toFixed(1)}%`" />
      </div>
      <div class="mt-0.5 flex gap-1 text-[10px] text-slate-500">
        <span v-for="(_, i) in curva" :key="i" class="flex-1 text-center" :title="`D+${i + 1}`">{{ dia(i, fecha) }}</span>
      </div>
      <div class="flex gap-1 text-[10px] font-medium text-slate-300">
        <span v-for="(c, i) in curva" :key="i" class="num flex-1 text-center">{{ (c * 100).toFixed(1) }}%</span>
      </div>
    </div>
    <div v-if="curva5?.length && (p5 >= 0.01 || Math.max(...curva5) >= 0.01)" class="mt-2">
      <p class="mb-1 text-[11px] uppercase tracking-wide text-slate-500">Curva 7 días — M5+ por día</p>
      <div class="flex h-10 items-end gap-1">
        <div v-for="(c, i) in curva5" :key="i" class="flex-1 rounded-sm bg-orange-500/80" :style="{ height: `${Math.max(4, Math.min(100, c * 1500))}%` }" :title="`D+${i + 1}: ${(c * 100).toFixed(2)}%`" />
      </div>
      <div class="mt-0.5 flex gap-1 text-[10px] text-slate-500">
        <span v-for="(_, i) in curva5" :key="i" class="flex-1 text-center" :title="`D+${i + 1}`">{{ dia(i, fecha) }}</span>
      </div>
      <div class="flex gap-1 text-[10px] font-medium text-slate-300">
        <span v-for="(c, i) in curva5" :key="i" class="num flex-1 text-center">{{ (c * 100).toFixed(2) }}%</span>
      </div>
    </div>
    <div v-if="curva6?.length && (p6 >= 0.01 || Math.max(...curva6) >= 0.01)" class="mt-2">
      <p class="mb-1 text-[11px] uppercase tracking-wide text-slate-500">Curva 7 días — M6+ por día (ETAS)</p>
      <div class="flex h-10 items-end gap-1">
        <div v-for="(c, i) in curva6" :key="i" class="flex-1 rounded-sm bg-red-500/80" :style="{ height: `${Math.max(4, Math.min(100, c * 3000))}%` }" :title="`D+${i + 1}: ${(c * 100).toFixed(2)}%`" />
      </div>
      <div class="mt-0.5 flex gap-1 text-[10px] text-slate-500">
        <span v-for="(_, i) in curva6" :key="i" class="flex-1 text-center" :title="`D+${i + 1}`">{{ dia(i, fecha) }}</span>
      </div>
      <div class="flex gap-1 text-[10px] font-medium text-slate-300">
        <span v-for="(c, i) in curva6" :key="i" class="num flex-1 text-center">{{ (c * 100).toFixed(2) }}%</span>
      </div>
    </div>
    <p v-if="mensaje" class="mt-3 text-xs text-slate-400">{{ mensaje }}</p>
    <p v-if="observed !== null && observed !== undefined" class="mt-1 text-xs" :class="observed ? 'text-red-300' : 'text-slate-500'">
      Real: {{ observed ? 'hubo M4+ en 7d' : 'sin M4+ en 7d' }}
    </p>
  </div>
</template>
