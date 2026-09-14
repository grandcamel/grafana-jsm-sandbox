# 01 — Receiver accepts a Notification and starts a fake Run

**What to build:** A presenter can POST a canned Grafana Notification at the Receiver and see, in the log, that exactly one Run was started for it with the Notification saved to a per-Run directory. Junk bodies are refused. Two Notifications posted back to back are handled one at a time in order. A Run that blows up is logged and the next one still starts. This ticket also scaffolds the repo: Python package, pytest, a canned firing Notification fixture, and a README stub.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] POST of a valid Notification returns 202 before the Run starts, and the injected spawner is called once with a working directory containing the Notification as JSON
- [ ] A body that is not JSON, or lacks an alerts array, or has an alert without fingerprint and status, returns 400 and no spawn occurs
- [ ] GET health returns 200
- [ ] Two Notifications posted back to back produce two spawns in arrival order; the second spawn does not begin until the first fake completes
- [ ] A spawner that raises is logged with the Run id and the next Notification still spawns
- [ ] Receiver logs Run start, end, exit status and duration
- [ ] Tests start a real local server on an ephemeral port; no HTTP layer mocking; pytest passes from a clean checkout
- [ ] Uses the vocabulary from CONTEXT.md in module and test names (Receiver, Run, Notification, Alert)
