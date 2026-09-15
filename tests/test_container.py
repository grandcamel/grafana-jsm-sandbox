"""The committed container and compose, checked against the process they must start.

Nothing here builds an image. These drive the three committed files — the
Dockerfile, `docker-compose.yml` and `.env.example` — against the code and the
rules they exist to satisfy: the configuration reader that refuses to start
without a credential, git's own ignore rules, and the redaction the log
formatter applies to anything credential-shaped.

The checks that need a container actually running are opt-in, like the
end-to-end check, because they cost a build and a demo:

    DEMO_CONTAINER=1 python3 -m pytest tests/test_container.py
"""

from __future__ import annotations

import os
import subprocess
import urllib.request
from pathlib import Path

import pytest
import yaml

from grafana_jsm_sandbox.__main__ import (
    HOST_VARIABLE,
    PORT_VARIABLE,
    RUN_TIMEOUT_VARIABLE,
    RUNS_DIRECTORY_VARIABLE,
    SKILL_DIRECTORY_VARIABLE,
    Settings,
)
from grafana_jsm_sandbox.forwarder import ENVIRONMENT_VARIABLES
from grafana_jsm_sandbox.log_formatter import redact
from grafana_jsm_sandbox.run_spawner import ANTHROPIC_TOKEN_VARIABLE

REPOSITORY = Path(__file__).resolve().parent.parent
"""The build context, the git working tree, and where every file read here lives."""

COMPOSE_FILE = REPOSITORY / "docker-compose.yml"
DOCKERFILE = REPOSITORY / "Dockerfile"
DOCKER_IGNORE = REPOSITORY / ".dockerignore"
ENV_EXAMPLE = REPOSITORY / ".env.example"
"""The four committed files that describe the container, all read as text."""

ENV_FILE = ".env"
"""What compose reads the demo's credentials from, and what git must never take."""

RUNS_PATTERN = "runs/"
"""What must stay ignored: each Run's working directory, and the Notification in it."""

DEMO_SERVICE = "demo"
"""The container the Run happens in. Grafana's contact point will name it."""

LGTM_SERVICE = "lgtm"
"""The published Grafana stack the Alert fires from."""

GRAFANA_PORT = 3000
"""Where the presenter watches the Alert fire, on the laptop."""

RECEIVER_PORT = 8080
"""What the contact point names and what the replay script posts at by default."""

CONTAINER_VARIABLE = "DEMO_CONTAINER"
"""Set it to anything and the checks that need the stack up run too."""

CREDENTIALS = (*ENVIRONMENT_VARIABLES.values(), ANTHROPIC_TOKEN_VARIABLE)
"""Every variable the process refuses to start without."""

SETTINGS_VARIABLES = (
    *CREDENTIALS,
    HOST_VARIABLE,
    PORT_VARIABLE,
    RUNS_DIRECTORY_VARIABLE,
    SKILL_DIRECTORY_VARIABLE,
    RUN_TIMEOUT_VARIABLE,
)
"""Every variable the process reads at all, which is what the example must list."""


def env_example() -> dict[str, str]:
    """The committed example read the way compose reads an env file."""
    variables = {}
    for line in ENV_EXAMPLE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, value = line.partition("=")
        variables[name.strip()] = value.strip()
    return variables


COMPOSE = yaml.safe_load(COMPOSE_FILE.read_text())
"""The committed compose file, read once."""


def service(name: str) -> dict:
    return COMPOSE["services"][name]


def published_ports(name: str) -> set[int]:
    """The laptop-side ports a service publishes.

    Compose's short form is `"host:container"`, optionally with an address in
    front. A bare `"container"` publishes nothing to the laptop and so counts for
    nothing here.
    """
    mappings = (str(mapping).split(":") for mapping in service(name).get("ports", []))
    return {int(parts[-2]) for parts in mappings if len(parts) > 1}


def git_ignores(path: str) -> bool:
    return (
        subprocess.run(["git", "check-ignore", "-q", path], cwd=REPOSITORY, check=False).returncode
        == 0
    )


def test_the_committed_example_describes_a_process_that_would_start():
    """Every variable filled with its placeholder, and the Receiver still starts."""
    settings = Settings.from_environment(env_example())

    assert settings.credential.site_url.startswith("https://")
    assert settings.credential.email
    assert settings.credential.api_token
    assert settings.anthropic_token


@pytest.mark.parametrize("variable", CREDENTIALS)
def test_the_example_names_every_credential_the_demo_needs(variable):
    assert variable in env_example()


@pytest.mark.parametrize("variable", SETTINGS_VARIABLES)
def test_the_example_names_every_variable_the_process_reads(variable):
    """Named, not necessarily set: the ones with a working default are commented out."""
    assert variable in ENV_EXAMPLE.read_text()


def test_the_example_carries_placeholders_rather_than_anyone_s_credential():
    """Nothing in it is credential-shaped, by the same rule that keeps the log clean."""
    for name, value in env_example().items():
        assert redact(value) == value, f"{name} looks like a real credential"


def test_git_never_takes_the_env_file_compose_reads():
    assert git_ignores(ENV_FILE)


def test_git_never_takes_a_run_s_working_directory():
    assert git_ignores(RUNS_PATTERN)


def test_the_build_context_carries_neither_the_env_file_nor_a_past_run():
    ignored = DOCKER_IGNORE.read_text().split()

    assert ENV_FILE in ignored
    assert RUNS_PATTERN in ignored


def test_the_demo_takes_its_credentials_from_the_ignored_env_file():
    demo = service(DEMO_SERVICE)

    assert ENV_FILE in _as_list(demo["env_file"])
    assert not set(demo.get("environment", {})) & set(CREDENTIALS)


def test_a_misconfigured_demo_is_not_restarted_into_a_crash_loop():
    """The Receiver refuses to start and names the missing variable. Once (story 47)."""
    assert "restart" not in service(DEMO_SERVICE)


def test_no_service_is_handed_the_docker_socket():
    for name, definition in COMPOSE["services"].items():
        for volume in definition.get("volumes", []):
            assert "docker.sock" not in str(volume), f"{name} mounts the docker socket"
        assert not definition.get("privileged"), f"{name} is privileged"


def test_grafana_and_the_receiver_answer_the_laptop():
    assert GRAFANA_PORT in published_ports(LGTM_SERVICE)
    assert RECEIVER_PORT in published_ports(DEMO_SERVICE)


def test_the_receiver_listens_where_the_published_port_leads():
    """The port compose publishes is the port the process is told to bind."""
    settings = Settings.from_environment(env_example())

    assert settings.port == RECEIVER_PORT
    assert PORT_VARIABLE not in service(DEMO_SERVICE).get("environment", {})


def test_the_lgtm_stack_and_the_demo_share_one_network():
    """The contact point in ticket 07 names the demo service, so both must be on it."""
    networks = COMPOSE["networks"]
    assert len(networks) == 1

    only = next(iter(networks))
    assert _as_list(service(LGTM_SERVICE)["networks"]) == [only]
    assert _as_list(service(DEMO_SERVICE)["networks"]) == [only]


def test_the_container_ends_as_a_user_who_is_not_root():
    """Read off the Dockerfile, so the default run says it even with no stack up.

    `TestAStackThatIsUp` asks the running container the same question properly.
    """
    users = [
        line.split(maxsplit=1)[1].strip()
        for line in DOCKERFILE.read_text().splitlines()
        if line.startswith("USER ")
    ]

    assert users and users[-1] != "root"


def test_the_image_is_built_holding_no_credential():
    """No credential variable is so much as named in the build, let alone given a value."""
    for line in DOCKERFILE.read_text().splitlines():
        for variable in CREDENTIALS:
            assert variable not in line, f"{variable} is named in the Dockerfile"


@pytest.mark.skipif(not os.environ.get(CONTAINER_VARIABLE), reason=f"set {CONTAINER_VARIABLE}")
class TestAStackThatIsUp:
    """With `docker compose up -d` already done, the two things the demo depends on."""

    def test_the_health_endpoint_answers_the_laptop(self):
        assert _get(f"http://localhost:{RECEIVER_PORT}/health") == 200

    def test_the_health_endpoint_answers_from_inside_the_network(self):
        """What Grafana's contact point will do, from the container that will do it."""
        answered = _compose_exec(
            LGTM_SERVICE, "curl", "-fsS", f"http://{DEMO_SERVICE}:{RECEIVER_PORT}/health"
        )

        assert answered.returncode == 0, answered.stderr

    def test_the_receiver_runs_as_a_user_who_is_not_root(self):
        who = _compose_exec(DEMO_SERVICE, "id", "-u")

        assert who.stdout.strip() != "0"

    def test_a_run_would_find_the_tools_it_is_allowed_to_use(self):
        for tool in ("claude", "jira-as"):
            found = _compose_exec(DEMO_SERVICE, "sh", "-c", f"command -v {tool}")
            assert found.returncode == 0, f"{tool} is not on the Run's PATH"


def _as_list(value) -> list[str]:
    return [value] if isinstance(value, str) else list(value)


def _get(url: str) -> int:
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status


def _compose_exec(service_name: str, *command: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "exec", "-T", service_name, *command],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    )
