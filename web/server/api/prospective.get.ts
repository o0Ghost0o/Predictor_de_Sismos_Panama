const UP = 'http://127.0.0.1:8001'
export default defineEventHandler(() =>
  $fetch(`${UP}/prospective`).catch(() => ({ n: 0, log: [] }))
)
