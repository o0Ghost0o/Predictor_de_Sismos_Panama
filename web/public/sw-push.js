// SW de la PWA: push + shell offline (nunca cachea /api ni el ws en vivo).
const CACHE = 'sismos-pa-v1'
const SHELL = ['/', '/manifest.webmanifest', '/icons/icon-192.png', '/icons/icon-512.png']
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()))
})
self.addEventListener('fetch', (event) => {
  const u = new URL(event.request.url)
  if (u.pathname.startsWith('/api/') || event.request.method !== 'GET') return
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request).then((res) => {
      if (res.ok && u.origin === self.location.origin) {
        const copy = res.clone()
        caches.open(CACHE).then((c) => c.put(event.request, copy))
      }
      return res
    }).catch(() => caches.match('/')))
  )
})
// Push: muestra la notificación y abre el tablero al tocarla.
self.addEventListener('push', (event) => {
  let data = {}
  try { data = event.data ? event.data.json() : {} } catch { data = { body: event.data?.text?.() } }
  const title = data.title || 'Sismos Panamá'
  event.waitUntil(self.registration.showNotification(title, {
    body: data.body || '',
    tag: data.tag || 'sismo',
    data: { url: data.url || '/' },
    renotify: true
  }))
})
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(clients.openWindow(event.notification.data.url || '/'))
})
