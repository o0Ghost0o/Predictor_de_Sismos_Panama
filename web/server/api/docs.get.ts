import { marked } from 'marked'
import { readFile, readdir } from 'node:fs/promises'
import { join, resolve } from 'node:path'

const DOCS = resolve(process.cwd(), '..', 'docs')
const OK = /^[a-z0-9-]+$/

export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  if (!q.slug) {
    const files = (await readdir(DOCS)).filter((f) => f.endsWith('.md') && f !== 'README.md').sort()
    return { index: files.map((f) => f.replace(/\.md$/, '')) }
  }
  const slug = String(q.slug)
  if (!OK.test(slug)) throw createError({ statusCode: 400 })
  const html = marked.parse(await readFile(join(DOCS, `${slug}.md`), 'utf8'))
  return { slug, html }
})
