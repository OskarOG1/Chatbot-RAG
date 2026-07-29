FROM node:22-slim AS deps
WORKDIR /app
COPY frontend-next/package.json frontend-next/package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend-next/ ./
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

COPY --from=builder /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.status<500?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
