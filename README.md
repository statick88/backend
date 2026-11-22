# Backend development baseline

This repository provides the NestJS backend baseline. It exposes only `GET /health`, which returns exactly:

```json
{"status":"ok"}
```

It has no API wiring between applications, database, authentication, business APIs, migrations, or other product integrations.

## Team stack: three sibling repositories

The coordinated stack needs three published repositories checked out as siblings: `frontend`, `backend`, and `ai-service`. The versioned entrypoint is `backend/compose.stack.yaml`; it includes each repository's own `compose.yaml`, so every build context and read-only source mount remains in that repository even when the parent directory is relocated.

> **Publication prerequisite:** all three repositories and their Compose files must be published and clone-reachable before this team path is usable. This local preparation does not claim that the upstream repositories or `main` are ready.

Fork or clone each canonical repository, then place the three clones under one parent directory (replace `statick88` with your fork owner when applicable):

```bash
git clone https://github.com/statick88/frontend.git frontend
git clone https://github.com/statick88/backend.git backend
git clone https://github.com/statick88/ai-service.git ai-service
cd backend
export COMPOSE_DISABLE_ENV_FILE=1
export COMPOSE_FILE=compose.stack.yaml
docker compose up -d --build
```

PowerShell uses environment variables with `$env`:

```powershell
cd backend
$env:COMPOSE_DISABLE_ENV_FILE = "1"
$env:COMPOSE_FILE = "compose.stack.yaml"
docker compose up -d --build
```

This path requires Docker Engine and Docker Compose v2.20+ on the host. It does not make WSL or macOS execution claims.

### Operate the stack

With `COMPOSE_FILE=compose.stack.yaml` still exported, use literal Compose commands:

```bash
docker compose ps
docker compose logs --no-color --tail 80
docker compose up --wait --wait-timeout 180
docker compose down --remove-orphans
```

The initial baselines are independently healthy at their own ports: frontend on 4200, backend on 3000 (`/health` returns `{"status":"ok"}`), and ai-service on 8000 (`/health`). This is not application-to-application API integration.

Alternatively, do not export `COMPOSE_FILE` and name the entrypoint explicitly:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose -f compose.stack.yaml up -d --build
```

For simultaneous coordinated worktree groups, select a unique Compose project name and all three loopback host ports:

Keep the same port variables for every command, including the second `up --wait`, so Compose does not recreate the stack using default ports:

```bash
export COMPOSE_DISABLE_ENV_FILE=1
export BACKEND_PORT=13001
export FRONTEND_PORT=14201
export AI_SERVICE_PORT=18001
docker compose -p workspace-task-stack -f compose.stack.yaml up -d --build
docker compose -p workspace-task-stack -f compose.stack.yaml ps
docker compose -p workspace-task-stack -f compose.stack.yaml up --wait --wait-timeout 180
docker compose -p workspace-task-stack -f compose.stack.yaml logs --no-color --tail 80
docker compose -p workspace-task-stack -f compose.stack.yaml down --remove-orphans
```

In PowerShell, set `$env:BACKEND_PORT = "13001"`, `$env:FRONTEND_PORT = "14201"`, and `$env:AI_SERVICE_PORT = "18001"` before the same `docker compose -p ... -f ...` commands. Clear these variables when returning to default ports.

Create each group as three separate Git worktrees and branches under one parent, for example `workspace-task/frontend`, `workspace-task/backend`, and `workspace-task/ai-service`. Do not move Git worktrees manually and do not share one branch checkout between repositories.

Before returning to the standalone backend workflow, unset `COMPOSE_FILE`; otherwise plain `docker compose` would merge the stack entrypoint unexpectedly:

```bash
unset COMPOSE_FILE
COMPOSE_DISABLE_ENV_FILE=1 docker compose -f compose.yaml up -d --build
```

PowerShell equivalent:

```powershell
Remove-Item Env:COMPOSE_FILE
$env:COMPOSE_DISABLE_ENV_FILE = "1"
docker compose -f compose.yaml up -d --build
```

## Standalone backend development

The standalone backend Compose file remains the primary pull-request coverage and can be used without private sibling checkouts. It mounts only `./src` read-only at `/app/src`; dependencies come from the image built from the committed lockfile.

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose -f compose.yaml config --quiet
python3 -m unittest tests/test_compose_contract.py
COMPOSE_DISABLE_ENV_FILE=1 docker compose -f compose.yaml run --build --rm --no-deps backend-check
```

`backend-check` has no host mounts and runs ESLint, TypeScript type checks, Jest's HTTP health test, and the Nest build. The stack contract test uses temporary minimal public Compose fixtures, so CI neither checks out private siblings nor uses secrets or write tokens. A full private-sibling integration run is not automatically available to same-repository GitHub Actions.

For one standalone runtime, use a unique project and port when needed:

```bash
COMPOSE_DISABLE_ENV_FILE=1 BACKEND_PORT=13001 docker compose -p backend-feature-a -f compose.yaml up -d --build
curl --fail --silent --show-error http://127.0.0.1:13001/health
COMPOSE_DISABLE_ENV_FILE=1 docker compose -p backend-feature-a -f compose.yaml down --remove-orphans
```

## CI and project tracking

The workflow validates standalone Compose configuration, both public Compose contracts, the immutable container checks, and the standalone runtime health endpoint. CI becomes active only after this workflow is published to GitHub; required checks remain a repository ruleset decision.

Project tracking: <https://github.com/users/statick88/projects/9>.
