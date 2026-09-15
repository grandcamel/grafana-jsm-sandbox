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

The process that actually spawns a Run is injected into the `Receiver` at construction, so it
stays a seam a test can substitute; the real spawner is `RunSpawner`, below.

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

The Receiver pipes every live Run through it, one line at a time, as the Run produces it.

The **skill** a Run follows, and the command line that starts one.

[`skill/incident-sync/SKILL.md`](skill/incident-sync/SKILL.md) is the whole of what a Run knows
about OPS: the Fingerprint label format, the match JQL, the field mapping, the lifecycle rule, and
every operation written as a `jira-as` invocation, because nothing else will execute. It is short
on purpose — it is meant to be read off a screen during the demo.

`build_run_command` is the command line that starts one Run: print mode, `dontAsk`, an allow list
of `Bash(jira-as *)` and `Read`, stream-json with `--verbose`, and the skill directory added so the
Run can read it (ADR 0003). Print it to start a Run by hand:

```bash
python3 -m grafana_jsm_sandbox.run_command skill
```

Two things the permission boundary decides for the skill, both found by running it:

- A `jira-as` command that is split across lines, carries a newline inside an argument, or uses
  `$'...'` does not match the allow list and is denied whole. Every invocation in the skill is one
  line of plain single quotes; the Description gets its paragraphs from one line of ADF instead.
- A Run has no clock of its own — `date` is not on the allow list — so every duration it reports is
  Jira's `serverTime` minus the Incident's `created`. Grafana's clock is never used for a duration,
  which is also what keeps a replayed fixture from reporting a negative one.

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
Receiver owns it, and the spawner below registers each Run's sentinel around that Run.

The **Run spawner** — what the Receiver starts for each Notification, for real.

`RunSpawner` builds the Run's environment from scratch rather than inheriting one: the Anthropic
OAuth token, the Jira email, `JIRA_SITE_URL` pointing at the Forwarder over plain http,
`JIRA_API_TOKEN` set to that Run's sentinel, `JIRA_ALLOW_SITE_OPERATIONS` so the Run can ask Jira
what time it is, and `PATH`. Nothing else — not the real Jira token, not whatever else the
Receiver happened to be started with. The sentinel is registered with the
Forwarder before the process starts and cleared the moment it ends, so a sentinel that turns up in
a Transcript afterwards is worth nothing.

The Run's stdout is its Transcript, rendered into the log by the formatter as it arrives. Its
stderr is captured and logged only if it exits non-zero, redacted like every other line. A Run
that outlives its timeout is killed and logged, and the queue behind it keeps moving.

## Running the demo on the laptop

The Receiver, the Forwarder and real Runs are one process — the container's main process in ticket
06, and this on a laptop:

```bash
python3 -m grafana_jsm_sandbox
```

It refuses to start without a Jira credential and an Anthropic token, naming everything that is
missing at once, so a half-filled env file is fixed in one pass rather than three restarts.

| Variable | What it is |
| --- | --- |
| `JIRA_SITE_URL` | The real Atlassian site. Only the Forwarder ever sees it |
| `JIRA_EMAIL` | The account the Forwarder acts as |
| `JIRA_API_TOKEN` | The real token. It never reaches a Run |
| `CLAUDE_CODE_OAUTH_TOKEN` | What a Run authenticates with. The one real credential it holds |
| `RECEIVER_HOST` / `RECEIVER_PORT` | Where the Receiver listens. `0.0.0.0` and `8080` |
| `RUNS_DIRECTORY` | Where each Run's working directory goes. `runs` |
| `SKILL_DIRECTORY` | The skill a Run reads. This repo's `skill` |
| `RUN_TIMEOUT` | Seconds before a stuck Run is killed. `300` |

Then drive it with the canned Notification sequence — a Firing, a repeat Firing, a Resolved —
which is also the demo's fallback if Grafana is uncooperative:

```bash
python3 -m grafana_jsm_sandbox.replay --receiver http://localhost:8080 --pause 30
```

## Layout

| Path | What it holds |
| --- | --- |
| `grafana_jsm_sandbox/receiver.py` | The Receiver, its Run queue and the `Run` record |
| `grafana_jsm_sandbox/notification.py` | Validation of an incoming Notification |
| `grafana_jsm_sandbox/log_formatter.py` | Rendering a Run's Transcript, and the redaction rules |
| `grafana_jsm_sandbox/forwarder.py` | The Forwarder, the sentinel check and the Jira credential |
| `grafana_jsm_sandbox/run_command.py` | The command line that starts one Run, and its allow list |
| `grafana_jsm_sandbox/run_spawner.py` | Starting one Run for real: its scrubbed environment, its sentinel |
| `grafana_jsm_sandbox/replay.py` | Posting the canned Notification sequence at a Receiver |
| `grafana_jsm_sandbox/__main__.py` | The whole process: configuration, the Forwarder, the Receiver |
| `skill/incident-sync/SKILL.md` | The skill a Run follows to turn a Notification into Incidents |
| `fixtures/notification-*.json` | The canned Notification sequence: firing, repeat, resolved |
| `fixtures/run-transcript.jsonl` | A recorded Run Transcript, including a real denial |
| `fixtures/run-transcript-repeat-firing.jsonl` | A recorded Run that commented a trend on a real Incident |
| `tests/` | pytest, driving a real Receiver and Forwarder over real HTTP on ephemeral ports |

## Running the tests

Python 3.11 or newer; the runtime is standard library only, and pytest is the one dev dependency.

```bash
python3 -m pytest
```

The default run is offline: no Jira, no model, nothing but real HTTP on ephemeral ports and real
child processes. The one test that touches OPS is opt-in, and asserts by JQL that the canned
sequence drove one Incident to `Completed` with its trend comments. It needs a Receiver already
running and a `jira-as` credential in the shell, and it resolves and closes the Incident it
watched on the way out:

```bash
DEMO_END_TO_END=1 python3 -m pytest tests/test_end_to_end.py
```
