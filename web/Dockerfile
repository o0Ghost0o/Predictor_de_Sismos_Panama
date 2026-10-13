# Sismos Panama web (Nuxt 4). Contexto de build = raiz del repo (ver docker-compose.yaml),
# porque server/api/docs.get.ts lee ../docs en tiempo de ejecucion.
FROM oven/bun:1 AS build

WORKDIR /app/web
COPY web/package.json web/bun.lock ./
RUN bun install --frozen-lockfile
COPY web/ ./
COPY docs/ /app/docs/
RUN bun run build

FROM node:22-slim

ENV NODE_ENV=production \
    NUXT_HOST=0.0.0.0 \
    NUXT_PORT=3000

WORKDIR /app/web
COPY --from=build /app/web/.output ./.output/
COPY --from=build /app/docs /app/docs/

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
