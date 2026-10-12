const UP = process.env.API_UPSTREAM || 'http://127.0.0.1:8001'
export default defineEventHandler(() =>
  $fetch(`${UP}/ingesta`).catch(() => ({}))
)
