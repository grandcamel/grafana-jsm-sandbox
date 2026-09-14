"""Shared fixtures for Receiver tests.

Every test here drives a real Receiver over real HTTP on an ephemeral port.
Nothing in the HTTP layer is mocked; the only substitution is the Run spawner,
which is injected into the Receiver at construction.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from grafana_jsm_sandbox.receiver import Receiver, Run

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def firing_notification() -> dict:
    """The canned firing Notification, as Grafana's webhook contact point sends it."""
    return json.loads((FIXTURES / "notification-firing.json").read_text())


@dataclass
class SpawnedRun:
    """One recorded invocation of the injected spawner.

    The Notification is read when the spawn happens, not later, so a test that
    asserts on it is asserting the file was already there when the Run started.
    """

    run_id: str
    working_directory: Path
    notification: dict

    @classmethod
    def record(cls, run: Run) -> SpawnedRun:
        return cls(
            run.run_id,
            run.working_directory,
            json.loads(run.notification_path.read_text()),
        )


@dataclass
class RecordingSpawner:
    """A fake Run spawner that records what the Receiver asked it to start."""

    exit_status: int = 0
    spawned: list[SpawnedRun] = field(default_factory=list)
    _progress: threading.Condition = field(default_factory=threading.Condition)
    _release: threading.Event | None = None
    _fail_next: BaseException | None = None

    def block_until_released(self) -> threading.Event:
        """Make the next spawn hang until the returned event is set."""
        self._release = threading.Event()
        return self._release

    def fail_next(self, error: BaseException) -> None:
        """Make the next spawn — and only the next — blow up."""
        self._fail_next = error

    def wait_for_spawns(self, count: int, timeout: float = 5.0) -> None:
        with self._progress:
            reached = self._progress.wait_for(lambda: len(self.spawned) >= count, timeout)
        assert reached, f"expected {count} spawns, saw {len(self.spawned)}"

    def __call__(self, run) -> int:
        with self._progress:
            self.spawned.append(SpawnedRun.record(run))
            error, self._fail_next = self._fail_next, None
            self._progress.notify_all()
        if self._release is not None:
            release, self._release = self._release, None
            assert release.wait(5.0), "blocked spawn was never released"
        if error is not None:
            raise error
        return self.exit_status


@dataclass
class Response:
    status: int
    body: bytes


def post_notification(receiver: Receiver, body) -> Response:
    """POST a Notification body. `body` may be bytes, str or a JSON-serialisable object."""
    if isinstance(body, (bytes, bytearray)):
        data = bytes(body)
    elif isinstance(body, str):
        data = body.encode()
    else:
        data = json.dumps(body).encode()
    return _request(receiver.url + "/notification", data=data, content_type="application/json")


def get_health(receiver: Receiver) -> Response:
    return _request(receiver.url + "/health")


def _request(url: str, data: bytes | None = None, content_type: str | None = None) -> Response:
    headers = {"Content-Type": content_type} if content_type else {}
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return Response(response.status, response.read())
    except urllib.error.HTTPError as error:
        return Response(error.code, error.read())


@pytest.fixture
def spawner() -> RecordingSpawner:
    return RecordingSpawner()


@pytest.fixture
def receiver(spawner, tmp_path):
    receiver = Receiver(spawn_run=spawner, runs_directory=tmp_path / "runs")
    receiver.start()
    try:
        yield receiver
    finally:
        receiver.stop()


def wait_for_log(caplog, substring: str, timeout: float = 5.0) -> str:
    """Wait until a log line containing `substring` has been emitted; return the log text."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = caplog.text
        if substring in text:
            return text
        time.sleep(0.01)
    raise AssertionError(f"no log line containing {substring!r}; log was:\n{caplog.text}")
