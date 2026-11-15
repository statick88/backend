# Backend development baseline

This repository provides the continuous integration NestJS backend baseline. It exposes only `GET /health`, which returns exactly:

```json
{"status":"ok"}
```

Docker Compose is the supported path for development and verification. A fork can be developed without a host Node.js or npm installation; the host needs Git, Docker Engine, and Docker Compose v2. This is a baseline, not a guarantee that every future regression or product integration is covered.

## Quick start from a fork

1. Fork this repository in GitHub, then clone **your fork** and retain its `origin` remote.
2. Add the shared repository as `upstream`, create a worktree and branch, then enter that worktree:

   ```bash
   git clone https://github.com/<your-account>/backend.git
   cd backend
   git remote add upstream https://github.com/statick88/backend.git
   git fetch upstream
   git worktree add ../backend-health -b chore/health upstream/main
   cd ../backend-health
   ```

   Replace `<your-account>` with your GitHub account.

3. Disable implicit `.env` loading and start the development container:

   ```bash
   export COMPOSE_DISABLE_ENV_FILE=1
   docker compose up -d --build
   ```

The default health URL is <http://127.0.0.1:3000/health>. Check readiness and inspect a bounded log tail when it does not become healthy:

```bash
docker compose ps backend
docker compose logs --no-color --tail 80 backend
curl --fail --silent --show-error http://127.0.0.1:3000/health
```

The curl response is exactly `{"status":"ok"}`.

## Development behavior

The `backend` service runs `npm run start:dev`. Only `./src` is mounted into the container, and it is mounted read-only at `/app/src`; source edits trigger Nest's watch reload without mounting the repository root, Git data, local dependencies, credentials, or `.env` files. Dependencies come from the image built from the committed lockfile.

When dependencies or Docker build inputs change, rebuild the image:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose up -d --build backend
```

## Worktrees and port overrides

Compose project names and host ports must differ when two worktrees run simultaneously. Keep the container port at 3000 and assign a unique loopback host port and project name for each worktree:

```bash
COMPOSE_DISABLE_ENV_FILE=1 BACKEND_PORT=13001 docker compose -p backend-feature-a up -d --build
COMPOSE_DISABLE_ENV_FILE=1 BACKEND_PORT=13002 docker compose -p backend-feature-b up -d --build
```

Their health URLs are `http://127.0.0.1:13001/health` and `http://127.0.0.1:13002/health`. Stop only the project you started:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose -p backend-feature-a down --remove-orphans
```

## Verification

Validate the Compose file and run the same immutable container checks used by CI:

```bash
COMPOSE_DISABLE_ENV_FILE=1 docker compose -f compose.yaml config --quiet
python3 -m unittest tests/test_compose_contract.py
COMPOSE_DISABLE_ENV_FILE=1 docker compose -f compose.yaml run --build --rm --no-deps backend-check
```

`backend-check` has no host mounts. It installs from `package-lock.json` inside the image and runs ESLint, TypeScript type checks, Jest's HTTP health test, and the Nest build.

## Pull requests and CI

Open pull requests from branches in your fork to the upstream repository's `main` branch and link the relevant issue. Fork users need permission to read the private upstream repository when it is private, plus the fork and pull-request rights granted by the repository owner.

The workflow is defined for pull requests, pushes to `main`, and manual dispatch. It validates Compose configuration, tests the public Compose contract, runs the full containerized check suite, starts the runtime with `--wait --wait-timeout 180`, probes the exact health response, prints bounded service logs on failure, and always tears down its scoped Compose project. It uses read-only repository permissions and does not use secrets or write tokens.

CI becomes active only after this workflow is published to GitHub. Configuring a CI status check as a required merge check is a separate repository branch-protection or ruleset decision. The current sole maintainer does not need to require another reviewer.

Project tracking: <https://github.com/users/statick88/projects/9>.

No database, authentication, business APIs, migrations, or other product integrations are configured by this baseline.
