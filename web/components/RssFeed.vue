<script setup lang="ts">
const { data } = await useFetch<any>('/api/rss')
</script>
<template>
  <div v-if="data?.items?.length" class="divide-y divide-white/5 text-sm">
    <a v-for="(it, i) in data.items" :key="i" :href="it.link" target="_blank" class="block py-2 hover:underline">
      <span class="font-medium">{{ it.title }}</span>
      <span class="ml-2 text-xs text-slate-500">{{ it.date ? new Date(it.date).toLocaleString('es-PA') : '' }}</span>
    </a>
  </div>
  <p v-else class="text-sm text-slate-500">RSS no disponible.</p>
</template>
