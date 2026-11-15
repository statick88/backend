FROM node:22.23.5-bookworm-slim AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM deps AS check

COPY eslint.config.mjs jest.config.ts nest-cli.json tsconfig.json tsconfig.build.json ./
COPY src ./src
COPY test ./test

CMD ["sh", "-c", "npm run lint && npm run typecheck && npm run test:ci && npm run build"]

FROM deps AS development

# Nest\'s watch-mode restart uses `ps` to terminate the previous child process.
RUN apt-get update && apt-get install -y --no-install-recommends procps && rm -rf /var/lib/apt/lists/*

COPY nest-cli.json tsconfig.json tsconfig.build.json ./
COPY src ./src

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["node", "-e", "require('http').get('http://127.0.0.1:3000/health', (response) => process.exit(response.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"]

CMD ["npm", "run", "start:dev"]
