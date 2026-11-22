"""Public contract for the versioned three-sibling Compose entrypoint."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
STACK_FILE = REPOSITORY / "compose.stack.yaml"


class StackComposeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name) / "relocated-workspace"
        self.backend = self.workspace / "backend"
        self.frontend = self.workspace / "frontend"
        self.ai_service = self.workspace / "ai-service"
        for repository in (self.backend, self.frontend, self.ai_service):
            repository.mkdir(parents=True)

        shutil.copy2(STACK_FILE, self.backend / "compose.stack.yaml")
        self._write_compose_files()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_compose_files(self) -> None:
        (self.backend / "compose.yaml").write_text(
            """services:
  backend:
    image: example/backend
    build:
      context: .
    ports:
      - \"127.0.0.1:${BACKEND_PORT:-3000}:3000\"
    volumes:
      - type: bind
        source: ./src
        target: /app/src
        read_only: true
  backend-check:
    profiles: [ci]
    image: example/backend-check
"""
        )
        (self.frontend / "compose.yaml").write_text(
            """services:
  frontend:
    image: example/frontend
    build:
      context: .
    ports:
      - \"127.0.0.1:${FRONTEND_PORT:-4200}:4200\"
    volumes:
      - type: bind
        source: ./src
        target: /app/src
        read_only: true
  frontend-check:
    profiles: [ci]
    image: example/frontend-check
"""
        )
        (self.ai_service / "compose.yaml").write_text(
            """services:
  ai-service:
    image: example/ai-service
    build:
      context: .
    ports:
      - \"127.0.0.1:${AI_SERVICE_PORT:-8000}:8000\"
    volumes:
      - type: bind
        source: ./app
        target: /app/app
        read_only: true
  ai-check:
    profiles: [ci]
    image: example/ai-check
"""
        )

    def compose_config(self, project_name: str, **ports: str) -> dict:
        environment = os.environ | {"COMPOSE_DISABLE_ENV_FILE": "1"}
        for name in ("BACKEND_PORT", "FRONTEND_PORT", "AI_SERVICE_PORT"):
            environment.pop(name, None)
        environment.update(ports)
        result = subprocess.run(
            [
                "docker",
                "compose",
                "--profile",
                "ci",
                "-p",
                project_name,
                "-f",
                "compose.stack.yaml",
                "config",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            cwd=self.backend,
            env=environment,
            text=True,
        )
        return json.loads(result.stdout)

    def test_includes_all_sibling_services_with_their_own_paths(self) -> None:
        config = self.compose_config("stack-contract-relocated")

        self.assertEqual(
            set(config["services"]),
            {
                "backend",
                "backend-check",
                "frontend",
                "frontend-check",
                "ai-service",
                "ai-check",
            },
        )
        self.assertEqual(config["services"]["backend"]["build"]["context"], str(self.backend))
        self.assertEqual(config["services"]["frontend"]["build"]["context"], str(self.frontend))
        self.assertEqual(config["services"]["ai-service"]["build"]["context"], str(self.ai_service))
        self.assertEqual(
            config["services"]["frontend"]["volumes"][0]["source"],
            str(self.frontend / "src"),
        )
        self.assertEqual(
            config["services"]["ai-service"]["volumes"][0]["source"],
            str(self.ai_service / "app"),
        )

    def test_project_name_and_all_port_overrides_are_preserved(self) -> None:
        config = self.compose_config(
            "stack-contract-ports",
            BACKEND_PORT="43101",
            FRONTEND_PORT="43102",
            AI_SERVICE_PORT="43103",
        )

        self.assertEqual(config["name"], "stack-contract-ports")
        self.assertEqual(config["networks"]["default"]["name"], "stack-contract-ports_default")
        self.assertEqual(config["services"]["backend"]["ports"][0]["published"], "43101")
        self.assertEqual(config["services"]["frontend"]["ports"][0]["published"], "43102")
        self.assertEqual(config["services"]["ai-service"]["ports"][0]["published"], "43103")

    def test_missing_sibling_fails_before_starting_any_service(self) -> None:
        for missing in ("frontend", "ai-service"):
            with self.subTest(missing=missing):
                workspace = self.workspace / f"missing-{missing}"
                backend = workspace / "backend"
                for source in (self.backend, self.frontend, self.ai_service):
                    target = workspace / source.name
                    target.mkdir(parents=True)
                    if source.name != missing:
                        shutil.copy2(source / "compose.yaml", target / "compose.yaml")
                shutil.copy2(STACK_FILE, backend / "compose.stack.yaml")

                project_name = f"stack-contract-missing-{missing}"
                result = subprocess.run(
                    ["docker", "compose", "-p", project_name, "-f", "compose.stack.yaml", "up", "-d", "--no-build"],
                    capture_output=True,
                    cwd=backend,
                    env=os.environ | {"COMPOSE_DISABLE_ENV_FILE": "1"},
                    text=True,
                )
                containers = subprocess.run(
                    ["docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={project_name}"],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(missing, result.stderr)
                self.assertIn("compose.yaml", result.stderr)
                self.assertEqual(containers.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
