FROM node:24-alpine

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1

RUN mkdir -p /app \
    && chown -R node:node /app

WORKDIR /app

USER node

COPY --chown=node:node package.json package-lock.json ./

RUN npm ci

COPY --chown=node:node . .

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD node -e "fetch('http://127.0.0.1:3000').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]