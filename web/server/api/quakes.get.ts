export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  return $fetch('http://127.0.0.1:8001/quakes', { params: q }).catch(() => [])
})
