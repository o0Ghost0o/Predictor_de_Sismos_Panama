<script setup lang="ts">
const props = defineProps<{ nivel: number }>()
const map: Record<number, { t: string; c: string }> = {
  3: { t: 'Nivel 3 · Tranquilo', c: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  4: { t: 'Nivel 4 · Moderado', c: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30' },
  5: { t: 'Nivel 5 · Mod-Alto', c: 'bg-orange-500/15 text-orange-300 border-orange-500/30' },
  6: { t: 'Nivel 6 · Alto', c: 'bg-red-500/15 text-red-300 border-red-500/30' }
}
const s = map[props.nivel] ?? map[3]
</script>
<template>
  <span :class="['inline-block rounded-full border px-3 py-1 text-xs font-medium', s.c]">{{ s.t }}</span>
</template>
