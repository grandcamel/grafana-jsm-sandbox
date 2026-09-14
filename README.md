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
still a seam — the real Claude CLI invocation, the container and the Grafana provisioning are
later tickets.

The **log formatter** — what turns a Run's Transcript into the log window the audience watches.

`format_event` is a pure function: one Run event in, zero or more display lines out. It renders
the Run's own text, every tool call with its command in full, tool results trimmed to a few lines,
and permission denials on a `[DENIED]` line — the audience-visible proof that a Run cannot do
anything except talk to Jira (ADR 0003). An event it does not understand costs one diagnostic
line, never a crash. Every line is redacted on the way out, so no Authorization header and nothing
token-shaped can reach a screen.

Render a saved Transcript to see what the log window will look like:

```bash
python3 -m grafana_jsm_sandbox.log_formatter fixtures/run-transcript.jsonl
```

```
[run]    model=claude-fable-5-1 permission-mode=dontAsk tools=Bash,Read
[claude] I'll run the two bash commands in order and report which worked.
[tool]   Bash: seq 1 40
[out]    1
[out]    2
[out]    3
[out]    4
[out]    5
[out]    + 35 more lines
[tool]   Bash: ls /etc
[DENIED] Bash: Permission to use Bash has been denied because Claude Code is running in don't ask mode.
[claude] The first command (`seq 1 40`) worked and printed 1 through 40; the second (`ls /etc`) was denied by the permission mode and did not run.
[DENIED] Bash: ls /etc
[result] success in 10.0s, 3 turns, $0.4527
```

Nothing pipes a live Run through it yet; the Receiver wires it up in ticket 05.

The **Forwarder** — the localhost process that holds the real Jira credential so a Run never does.

A Run's environment points jira-as at the Forwarder over plain http, with a per-Run **sentinel**
in place of the API token. The Forwarder swaps that sentinel for the real email and token and
forwards the request to the configured Atlassian site (ADR 0002). It binds to loopback only, takes
its upstream from configuration and never from the request, hands a redirect back rather than
following it somewhere else, and refuses a request whose sentinel is missing, wrong, or left over
from a Run that has ended. Neither the token nor an Authorization header reaches any log line.

Run it on its own to point a jira-as on this machine at the real site through a sentinel:

```bash
python3 -m grafana_jsm_sandbox.forwarder
```

```
forwarding to https://example.atlassian.net as ops@example.com
point jira-as at the Forwarder with a sentinel in place of the token:

    export JIRA_SITE_URL=http://127.0.0.1:61545
    export JIRA_API_TOKEN=<a fresh 32-character sentinel>

forwarded GET /rest/api/3/search/jql?jql=project+%3D+OPS, upstream said 200
refused a GET /rest/api/3/myself with no valid sentinel
```

It reads `JIRA_SITE_URL`, `JIRA_EMAIL` and `JIRA_API_TOKEN` from its own environment and fails at
startup, naming every variable that is missing, rather than no-opping during the demo. The
Receiver owns the Forwarder and registers each Run's sentinel in ticket 05.

## Layout

| Path | What it holds |
| --- | --- |
| `grafana_jsm_sandbox/receiver.py` | The Receiver, its Run queue and the `Run` record |
| `grafana_jsm_sandbox/notification.py` | Validation of an incoming Notification |
| `grafana_jsm_sandbox/log_formatter.py` | Rendering a Run's Transcript, and the redaction rules |
| `grafana_jsm_sandbox/forwarder.py` | The Forwarder, the sentinel check and the Jira credential |
| `fixtures/notification-firing.json` | A canned firing Notification for tests and demo fallback |
| `fixtures/run-transcript.jsonl` | A recorded Run Transcript, including a real denial |
| `tests/` | pytest, driving a real Receiver and Forwarder over real HTTP on ephemeral ports |

## Running the tests

Python 3.11 or newer; the runtime is standard library only, and pytest is the one dev dependency.

```bash
python3 -m pytest
```
