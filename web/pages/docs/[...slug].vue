<script setup lang="ts">
const route = useRoute()
const { data } = await useFetch<any>('/api/docs', { query: { slug: route.params.slug } })
</script>
<template>
  <div class="space-y-4">
    <NuxtLink to="/docs" class="text-sm text-slate-400 hover:text-slate-200">← Documentación</NuxtLink>
    <article v-if="data?.html" class="md card p-6 md:p-8" v-html="data.html" />
    <p v-else class="card p-4 text-sm text-slate-400">Documento no encontrado.</p>
  </div>
</template>
