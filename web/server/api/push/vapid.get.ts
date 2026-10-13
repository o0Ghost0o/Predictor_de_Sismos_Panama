const UP = process.env.NOTIFICATIONS_URL || 'https://notifications.vertexdc.com'
let cached: string | null = null
export default defineEventHandler(async () => {
  if (cached) return { publicKey: cached }
  const r: any = await $fetch(`${UP}/vapid-public-key`).catch(() => null)
  if (!r?.publicKey) throw createError({ statusCode: 502, message: 'push gateway sin VAPID' })
  cached = r.publicKey
  return { publicKey: cached }
})
