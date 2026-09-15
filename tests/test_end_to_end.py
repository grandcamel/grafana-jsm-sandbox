"""The whole loop, against a running demo and the real OPS project.

This is the only test that touches Jira, so it is opt-in: set `DEMO_END_TO_END`
and it runs, otherwise it is skipped and the default suite stays offline and
fast. It replays the canned Notification sequence at a Receiver that is already
running — `python3 -m grafana_jsm_sandbox`, or the container from ticket 06 —
and then watches OPS until the Incident those Runs created is Completed:

    DEMO_END_TO_END=1 python3 -m pytest tests/test_end_to_end.py

It asserts through `jira-as`, which reads the real credential from this shell's
environment, the same credential the Forwarder holds inside the demo.

Rehearsals accumulate, so the check identifies its own Incident rather than
assuming OPS is empty: it records which Incidents already carry the Fingerprint
label, and watches for one that was not there before. What it demands up front
is only that no *open* Match exists — a leftover open Incident would be
commented on instead of a new one being created, which is the demo working
correctly and the check being asked the wrong question.

Whatever it finds, it leaves nothing open behind: every Incident that appeared
during the run is resolved and then closed (ADR 0004 — `Canceled` sets no
resolution and has no way out, so a cancelled Incident sits in the Incidents
queue for good).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass

import pytest

from grafana_jsm_sandbox.replay import DEFAULT_RECEIVER, replay
from tests.conftest import firing_notification

END_TO_END_VARIABLE = "DEMO_END_TO_END"
"""Set it to anything and this check runs against a live demo and the real OPS project."""

RECEIVER_VARIABLE = "DEMO_RECEIVER_URL"
"""Where the demo is listening, when it is not on this laptop's default port."""

DEADLINE_VARIABLE = "DEMO_END_TO_END_TIMEOUT"
"""How long to give three Runs, when a demo machine is slower than this one."""

DEFAULT_DEADLINE = 900.0
"""Seconds to wait for three Runs. A Run is a live model call, not a function call."""

PAUSE = 10.0
"""Seconds between the replayed Notifications. The Receiver queues them anyway."""

POLL = 5.0
"""Seconds between looks at OPS, which is a real site and not to be hammered."""

JIRA_AS = "jira-as"
"""The CLI a Run uses, used here to ask OPS what the Runs actually did."""

LABELLED = 'project = OPS AND issuetype = Incident AND labels = "{label}"'
"""Every Incident ever created for this Fingerprint, in any status."""

MATCH = LABELLED + " AND statusCategory != Done"
"""The Match as a Run defines it (ADR 0004): the one *open* Incident for a Fingerprint."""

COMPLETED = "Completed"
CLOSED = "Closed"
RESOLUTION = "Done"

pytestmark = pytest.mark.skipif(
    not os.environ.get(END_TO_END_VARIABLE),
    reason=f"drives a running demo and the real OPS project; set {END_TO_END_VARIABLE}=1 to run",
)


@dataclass(frozen=True)
class Incident:
    """An OPS Incident as this check reads it: where it got to, and how much it said."""

    key: str
    status: str
    resolution: str | None
    comments: int


def test_the_canned_sequence_drives_one_incident_from_firing_to_completed():
    label = fingerprint_label()
    assert open_match(label) is None, (
        f"an open Incident already carries {label}; the Runs would comment on it "
        "instead of creating one. Close it first"
    )
    before = keys_labelled(label)

    try:
        assert replay(receiver_url(), pause=PAUSE) == [202, 202, 202]
        completed = wait_for_a_completed_incident(label, before)
        assert completed.comments >= 2, (
            f"{completed.key} should carry the opening comment and at least one trend comment"
        )
    finally:
        clean_up(label, before)


def wait_for_a_completed_incident(label: str, before: set[str]) -> Incident:
    """Watch OPS until an Incident that was not there before this replay is Completed."""
    deadline = time.monotonic() + setting(DEADLINE_VARIABLE, DEFAULT_DEADLINE)
    seen = None
    while time.monotonic() < deadline:
        for key in sorted(keys_labelled(label) - before):
            seen = incident(key)
            if seen.status == COMPLETED:
                return seen
        time.sleep(POLL)
    raise AssertionError(f"no new Completed Incident for {label}; the last look saw {seen}")


def clean_up(label: str, before: set[str]) -> None:
    """Leave every Incident this run created resolved and closed, out of the open queues."""
    for key in sorted(keys_labelled(label) - before):
        if incident(key).resolution is None:
            move_to(key, COMPLETED, resolution=RESOLUTION)
        if incident(key).resolution is None:
            # Closing it now would park it in the Incidents queue for good, which is
            # worse than leaving it visible for a human to finish.
            continue
        move_to(key, CLOSED)


def fingerprint_label() -> str:
    """The label the Runs key their Incident by, taken from the Notification they are sent."""
    return "fp-" + firing_notification()["alerts"][0]["fingerprint"]


def receiver_url() -> str:
    return os.environ.get(RECEIVER_VARIABLE, "").strip() or DEFAULT_RECEIVER


def setting(variable: str, default: float) -> float:
    return float(os.environ.get(variable, "").strip() or default)


def keys_labelled(label: str) -> set[str]:
    """Every Incident carrying `label`, however it ended."""
    return {issue["key"] for issue in search(LABELLED.format(label=label))}


def open_match(label: str) -> str | None:
    """The one open Incident carrying `label`, which is what a Run would act on."""
    found = search(MATCH.format(label=label))
    assert len(found) <= 1, f"{label} matched more than one open Incident: {found}"
    return found[0]["key"] if found else None


def incident(key: str) -> Incident:
    fields = jira_as_json("issue", "get", key)["fields"]
    return Incident(
        key=key,
        status=fields["status"]["name"],
        resolution=(fields.get("resolution") or {}).get("name"),
        comments=jira_as_json("collaborate", "comment", "list", key)["total"],
    )


def move_to(key: str, status: str, resolution: str | None = None) -> None:
    """Take the transition that lands on `status`, if there is one from where it is."""
    wanted = [
        transition
        for transition in jira_as_json("lifecycle", "transitions", key)
        if transition.get("to", {}).get("name") == status
    ]
    if not wanted:
        return
    arguments = ["lifecycle", "transition", key, "--id", wanted[0]["id"]]
    if resolution is not None:
        arguments += ["--resolution", resolution]
    jira_as(*arguments)


def search(jql: str) -> list[dict]:
    return jira_as_json("search", "jql", jql).get("issues", [])


def jira_as_json(*arguments: str):
    return json.loads(jira_as(*arguments, "-o", "json"))


def jira_as(*arguments: str) -> str:
    answer = subprocess.run(
        [JIRA_AS, *arguments], capture_output=True, text=True, timeout=120, check=False
    )
    assert answer.returncode == 0, f"{' '.join(arguments)} failed: {answer.stderr.strip()}"
    return answer.stdout
