<script setup lang="ts">
const { data } = await useFetch<any>('/api/docs')
</script>
<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Documentación</h1>
      <p class="text-sm text-slate-400">Fuente única: se renderiza desde <code>docs/*.md</code> del repo.</p>
    </div>
    <div class="grid gap-3 sm:grid-cols-2">
      <NuxtLink v-for="s in data?.index ?? []" :key="s" :to="`/docs/${s}`" class="card p-4 hover:border-amber-500/50">
        <span class="font-mono text-sm">{{ s }}</span>
      </NuxtLink>
    </div>
  </div>
</template>
