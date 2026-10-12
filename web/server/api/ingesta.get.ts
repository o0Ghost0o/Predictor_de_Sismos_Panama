export default defineEventHandler(() =>
  $fetch('http://127.0.0.1:8001/ingesta').catch(() => ({}))
)
