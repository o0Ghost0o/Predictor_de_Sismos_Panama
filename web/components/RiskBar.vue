<script setup lang="ts">
defineProps<{ value: number; color?: string }>()
</script>
<template>
  <div class="h-2 w-full overflow-hidden rounded-full bg-white/10">
    <div class="h-full rounded-full" :class="color ?? 'bg-amber-500'" :style="{ width: `${Math.min(100, Math.max(0, value * 100))}%` }" />
  </div>
</template>
