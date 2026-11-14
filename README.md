# Backend

Minimal NestJS technical baseline for Continius Integration. It exposes `GET /health`, which returns exactly:

```json
{"status":"ok"}
```

## Run with Docker Compose

Docker Compose is the primary development and verification path. It uses the pinned `node:22.23.5-bookworm-slim` image and does not read a local `.env` file.

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose up --build backend
```

The service listens on `http://127.0.0.1:3000`; `GET /health` returns the status shown above. The runtime image is a development image and runs `npm run start:dev`.

Run the full check suite in a clean container:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose run --build --rm --no-deps backend-check
```

The check container installs dependencies from the committed lockfile and runs linting, type-checking, tests, and the Nest build. It has no bind mounts or persistent volumes.

## Optional local development

For local Node.js development, use Node.js 22 LTS (see `.nvmrc`) and npm:

```bash
npm ci
npm run start:dev
npm run lint
npm run typecheck
npm run test:ci
npm run build
```

`npm run start:dev` starts the service on port 3000 by default. Set `PORT` to choose another port.

## Continuous integration

`.github/workflows/ci.yml` runs the Docker Compose check for every pull request, pushes to `main`, and manual dispatches. The workflow has read-only repository contents permission, a 15-minute timeout, and cancels superseded runs for the same workflow/ref.

CI starts only after this workflow is published to GitHub. Blocking merges also requires repository administrators to configure the CI status check as a required branch-protection/ruleset check separately; this repository configuration is not changed here.

No database or business-feature configuration is included in this technical baseline.
