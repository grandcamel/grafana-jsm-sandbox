# 01 — Receiver accepts a Notification and starts a fake Run

**What to build:** A presenter can POST a canned Grafana Notification at the Receiver and see, in the log, that exactly one Run was started for it with the Notification saved to a per-Run directory. Junk bodies are refused. Two Notifications posted back to back are handled one at a time in order. A Run that blows up is logged and the next one still starts. This ticket also scaffolds the repo: Python package, pytest, a canned firing Notification fixture, and a README stub.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [x] POST of a valid Notification returns 202 before the Run starts, and the injected spawner is called once with a working directory containing the Notification as JSON
- [x] A body that is not JSON, or lacks an alerts array, or has an alert without fingerprint and status, returns 400 and no spawn occurs
- [x] GET health returns 200
- [x] Two Notifications posted back to back produce two spawns in arrival order; the second spawn does not begin until the first fake completes
- [x] A spawner that raises is logged with the Run id and the next Notification still spawns
- [x] Receiver logs Run start, end, exit status and duration
- [x] Tests start a real local server on an ephemeral port; no HTTP layer mocking; pytest passes from a clean checkout
- [x] Uses the vocabulary from CONTEXT.md in module and test names (Receiver, Run, Notification, Alert)

## Comments

**2026-09-14 — implemented.** Every acceptance criterion is covered by a test in
`tests/test_receiver.py`; 14 tests pass from a clean checkout with `python3 -m pytest`.

- `grafana_jsm_sandbox/receiver.py` — the Receiver, its single-worker FIFO Run queue, and the
  `Run` record. `spawn_run` is injected at construction.
- `grafana_jsm_sandbox/notification.py` — Notification validation.
- `fixtures/notification-firing.json` — the canned firing Notification.

Two additions beyond the checklist, both from the code review:

- A Notification the Receiver cannot record (e.g. the runs directory cannot be created) now gets a
  `500` instead of dropping the connection with no status. Under `protocol_version = "HTTP/1.1"` an
  escaping exception left Grafana with nothing to read, which works against story 13 ("so that
  Grafana does not time out or retry").
- `pyproject.toml` pins `line-length = 100` so ruff format is a tooled standard rather than taste.

Known and deliberate: a Notification whose `alerts` array is empty is accepted and starts a Run
with nothing to do. This matches the letter of the spec's validation rule ("a top-level alerts
array where every element has a fingerprint and a status") and Grafana does not send one.

The Receiver has no `__main__` entry point yet — the real Run command, the Forwarder and the
container entrypoint are tickets 04, 03 and 06.
