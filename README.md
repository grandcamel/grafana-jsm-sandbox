# grafana-jsm-sandbox

A Grafana alert Notification triggers a headless Claude Run inside a container, and that Run
creates, updates and resolves Incidents in the Jira OPS project.

Domain vocabulary is in [CONTEXT.md](CONTEXT.md); decisions are in [docs/adr](docs/adr);
the spec and tickets are under [.scratch/alert-to-incident-sync](.scratch/alert-to-incident-sync).

## What exists today

The **Receiver** — the HTTP endpoint that accepts Notifications and starts Runs, one at a time.

- `POST /notification` — a Grafana webhook contact point body. A valid Notification is
  acknowledged with `202` and queued; the Run starts afterwards, so Grafana never waits on it.
  A body that is not JSON, has no `alerts` array, or has an Alert without a `fingerprint` and a
  `status`, gets a `400` and starts nothing.
- `GET /health` — `200` while the Receiver is up.

Each Notification becomes one Run with its own working directory under the Receiver's runs
directory, containing the Notification exactly as Grafana sent it as `notification.json`. Runs
execute one at a time in arrival order, so two Firings of the same Alert cannot race into
duplicate Incidents. The Receiver logs each Run's start, end, exit status and duration; a Run that
blows up is logged and the next one still starts.

The process that actually spawns a Run is injected into the `Receiver` at construction, so it is
still a seam — the real Claude CLI invocation, the Forwarder, the log formatter, the container and
the Grafana provisioning are later tickets.

## Layout

| Path | What it holds |
| --- | --- |
| `grafana_jsm_sandbox/receiver.py` | The Receiver, its Run queue and the `Run` record |
| `grafana_jsm_sandbox/notification.py` | Validation of an incoming Notification |
| `fixtures/notification-firing.json` | A canned firing Notification for tests and demo fallback |
| `tests/` | pytest, driving a real Receiver over real HTTP on an ephemeral port |

## Running the tests

Python 3.11 or newer; the runtime is standard library only, and pytest is the one dev dependency.

```bash
python3 -m pytest
```
