"""Public Docker Compose configuration contract for local development."""

import json
import os
from pathlib import Path
import subprocess
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
COMPOSE_FILE = REPOSITORY / "compose.yaml"


def compose_config(project_name: str, *, backend_port: str | None = None) -> dict:
    environment = os.environ | {"COMPOSE_DISABLE_ENV_FILE": "1"}
    if backend_port is None:
        environment.pop("BACKEND_PORT", None)
    else:
        environment["BACKEND_PORT"] = backend_port

    result = subprocess.run(
        [
            "docker",
            "compose",
            "--profile",
            "ci",
            "-p",
            project_name,
            "-f",
            str(COMPOSE_FILE),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        cwd=REPOSITORY,
        env=environment,
        text=True,
    )
    return json.loads(result.stdout)


class ComposeContractTests(unittest.TestCase):
    def test_development_mounts_only_source_read_only(self) -> None:
        config = compose_config("backend-contract-default")

        mounts = config["services"]["backend"].get("volumes", [])
        self.assertEqual(
            mounts,
            [
                {
                    "type": "bind",
                    "source": str(REPOSITORY / "src"),
                    "target": "/app/src",
                    "read_only": True,
                }
            ],
        )

    def test_check_service_has_no_host_mounts(self) -> None:
        config = compose_config("backend-contract-check")

        self.assertEqual(config["services"]["backend-check"].get("volumes", []), [])

    def test_loopback_default_port_and_override_are_preserved(self) -> None:
        default = compose_config("backend-contract-default")
        override = compose_config("backend-contract-override", backend_port="43101")

        self.assertEqual(default["services"]["backend"]["ports"][0], {
            "mode": "ingress",
            "host_ip": "127.0.0.1",
            "target": 3000,
            "published": "3000",
            "protocol": "tcp",
        })
        self.assertEqual(override["services"]["backend"]["ports"][0]["published"], "43101")
        self.assertEqual(override["services"]["backend"]["ports"][0]["host_ip"], "127.0.0.1")

    def test_explicit_project_names_are_retained(self) -> None:
        config = compose_config("backend-contract-worktree")

        self.assertEqual(config["name"], "backend-contract-worktree")
        self.assertEqual(
            config["networks"]["default"]["name"],
            "backend-contract-worktree_default",
        )


if __name__ == "__main__":
    unittest.main()
