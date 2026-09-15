"""The container's main process: the Receiver, the Forwarder it owns, and real Runs.

Everything the demo needs in one process (ADR 0001). The Forwarder is a thread
inside it holding the real Jira credential; the Receiver listens for Grafana's
Notifications; each Notification becomes a child process started by the spawner
with a sentinel where that credential would be.

    python3 -m grafana_jsm_sandbox

It reads its whole configuration from the environment and refuses to start
without a Jira credential and an Anthropic token, naming everything that is
missing at once, because a container that starts and quietly does nothing is
only found out when an Alert fires in front of an audience.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from grafana_jsm_sandbox.forwarder import Forwarder, IncompleteJiraCredential, JiraCredential
from grafana_jsm_sandbox.receiver import Receiver
from grafana_jsm_sandbox.run_command import build_run_command
from grafana_jsm_sandbox.run_spawner import (
    RUN_TIMEOUT,
    MissingAnthropicToken,
    RunSpawner,
    anthropic_token_from_environment,
)

logger = logging.getLogger(__name__)

Number = TypeVar("Number", int, float)

HOST_VARIABLE = "RECEIVER_HOST"
PORT_VARIABLE = "RECEIVER_PORT"
RUNS_DIRECTORY_VARIABLE = "RUNS_DIRECTORY"
SKILL_DIRECTORY_VARIABLE = "SKILL_DIRECTORY"
RUN_TIMEOUT_VARIABLE = "RUN_TIMEOUT"
"""What the container sets to place the demo; the credential variables are the Forwarder's
and the spawner's. Every one of these has a default that works on a laptop."""

DEFAULT_HOST = "0.0.0.0"
"""Grafana reaches the Receiver from another container; the Forwarder is the loopback one."""

DEFAULT_PORT = 8080
"""What the contact point URL names, so compose publishes one well-known port."""

DEFAULT_RUNS_DIRECTORY = Path("runs")
"""Where each Run's working directory goes, relative to wherever this was started."""

DEFAULT_SKILL_DIRECTORY = Path(__file__).resolve().parent.parent / "skill"
"""The skill in this repo, which is what the container mounts and what a Run reads."""


class IncompleteConfiguration(ValueError):
    """The environment does not describe a demo that could work, and says how."""


@dataclass(frozen=True)
class Settings:
    """Everything the process needs, read from the environment in one place."""

    credential: JiraCredential
    anthropic_token: str
    host: str
    port: int
    runs_directory: Path
    skill_directory: Path
    run_timeout: float

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> Settings:
        """Read the whole configuration, or raise naming every part of it that is wrong.

        Every failure is collected rather than raised at the first one, so a
        half-filled env file is fixed in one pass instead of three restarts.
        """
        environment = os.environ if environment is None else environment
        failures: list[str] = []
        credential = None
        anthropic_token = ""
        try:
            credential = JiraCredential.from_environment(environment)
        except IncompleteJiraCredential as failure:
            failures.append(str(failure))
        try:
            anthropic_token = anthropic_token_from_environment(environment)
        except MissingAnthropicToken as failure:
            failures.append(str(failure))
        port = _number(environment, PORT_VARIABLE, DEFAULT_PORT, int, failures)
        run_timeout = _number(environment, RUN_TIMEOUT_VARIABLE, RUN_TIMEOUT, float, failures)
        if failures or credential is None:
            raise IncompleteConfiguration("\n".join(failures))
        return cls(
            credential=credential,
            anthropic_token=anthropic_token,
            host=environment.get(HOST_VARIABLE, "").strip() or DEFAULT_HOST,
            port=port,
            runs_directory=_directory(environment, RUNS_DIRECTORY_VARIABLE, DEFAULT_RUNS_DIRECTORY),
            skill_directory=_directory(
                environment, SKILL_DIRECTORY_VARIABLE, DEFAULT_SKILL_DIRECTORY
            ),
            run_timeout=run_timeout,
        )


def serve(settings: Settings) -> int:
    """Start the Forwarder and the Receiver, and serve Notifications until interrupted."""
    forwarder = Forwarder(settings.credential)
    forwarder.start()
    receiver = Receiver(
        spawn_run=RunSpawner(
            command=build_run_command(settings.skill_directory),
            forwarder=forwarder,
            anthropic_token=settings.anthropic_token,
            # The email, and only the email. The spawner is handed the one part of
            # the credential a Run is allowed to hold, rather than the credential
            # it would then have to be trusted not to pass on (ADR 0002).
            jira_email=settings.credential.email,
            timeout=settings.run_timeout,
        ),
        runs_directory=settings.runs_directory,
        host=settings.host,
        port=settings.port,
    )
    receiver.start()
    logger.info("receiver listening on %s", receiver.url)
    logger.info(
        "runs reach %s as %s through the Forwarder, holding a sentinel",
        settings.credential.site_url,
        settings.credential.email,
    )
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        receiver.stop()
        forwarder.stop()
    return 0


def main(argv: list[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print("usage: python3 -m grafana_jsm_sandbox", file=sys.stderr)
        return 2
    try:
        settings = Settings.from_environment(environment)
    except IncompleteConfiguration as failure:
        print(failure, file=sys.stderr)
        return 1
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return serve(settings)


def _number(
    environment: Mapping[str, str],
    variable: str,
    default: Number,
    read: Callable[[str], Number],
    failures: list[str],
) -> Number:
    """A number read from the environment, or the default, or one more failure to report."""
    value = environment.get(variable, "").strip()
    if not value:
        return default
    try:
        return read(value)
    except ValueError:
        failures.append(f"{variable} is not a number: {value!r}")
        return default


def _directory(environment: Mapping[str, str], variable: str, default: Path) -> Path:
    return Path(environment.get(variable, "").strip() or default)


if __name__ == "__main__":
    raise SystemExit(main())
