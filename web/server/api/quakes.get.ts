export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const UP = process.env.API_UPSTREAM || 'http://127.0.0.1:8001'
  return $fetch(`${UP}/quakes`, { params: q }).catch(() => [])
})
