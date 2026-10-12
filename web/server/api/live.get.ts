// Sismicidad en vivo: feeds USGS filtrados al bbox de Panamá (sin dependencias RSS).
const FEEDS = [
  'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson',
  'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson'
]
const BBOX = { latMin: 6.5, latMax: 10.0, lonMin: -83.5, lonMax: -77.0 }

export default defineEventHandler(async () => {
  const items: any[] = []
  for (const url of FEEDS) {
    try {
      const j: any = await $fetch(url, { timeout: 15000 })
      for (const f of j.features ?? []) {
        const [lon, lat, dep] = f.geometry.coordinates
        const p = f.properties
        if (lat < BBOX.latMin || lat > BBOX.latMax || lon < BBOX.lonMin || lon > BBOX.lonMax) continue
        items.push({ mag: p.mag, place: p.place, time: new Date(p.time).toISOString(), depth: dep, url: p.url })
      }
    } catch { /* feed caído: se omite */ }
  }
  const seen = new Set()
  return items
    .filter((i) => (seen.has(i.time + i.place) ? false : (seen.add(i.time + i.place), true)))
    .sort((a, b) => b.time.localeCompare(a.time))
    .slice(0, 30)
})
