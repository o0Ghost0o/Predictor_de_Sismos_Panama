// RSS sismico real: RSN Costa Rica (Joomla feed). Sin dependencias: regex sobre XML.
export default defineEventHandler(async () => {
  try {
    const xml: string = await $fetch('https://rsn.ucr.ac.cr/actividad-sismica/ultimos-sismos', {
      timeout: 20000, query: { format: 'feed', type: 'rss' }, responseType: 'text',
      headers: { 'User-Agent': 'SismosPanama-PoC/1.0 (investigacion; contacto comunitario)' }
    })
    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].slice(0, 15).map((m) => {
      const g = (t: string) => (m[1].match(new RegExp(`<${t}>([\\s\\S]*?)<\/${t}>`))?.[1] ?? '').replace(/<!\[CDATA\[|\]\]>/g, '').trim()
      return { title: g('title'), link: g('link'), date: g('pubDate'), desc: g('description').slice(0, 140) }
    })
    return { fuente: 'RSN-UCR', items }
  } catch (e: any) {
    console.error('RSS-DBG:', e?.message ?? e, '| cause:', (e?.cause as any)?.message ?? '')
    return { fuente: 'RSN-UCR', items: [], error: 'feed no disponible' }
  }
})
