// Proxy de suscripción: la site_key nunca sale del servidor.
const UP = process.env.NOTIFICATIONS_URL || 'https://notifications.vertexdc.com'
const KEY = process.env.NOTIFICATIONS_SITE_KEY || ''
export default defineEventHandler(async (event) => {
  if (!KEY) throw createError({ statusCode: 500, message: 'push no configurado en el servidor' })
  const { subscription } = await readBody(event)
  if (!subscription?.endpoint) throw createError({ statusCode: 400, message: 'subscription incompleta' })
  return $fetch(`${UP}/subscribe`, {
    method: 'POST',
    body: { site_key: KEY, subscription }
  }).catch((e: any) => { throw createError({ statusCode: 502, message: 'gateway push rechazó' }) })
})
