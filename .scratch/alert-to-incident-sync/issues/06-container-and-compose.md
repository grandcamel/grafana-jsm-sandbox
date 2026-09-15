# 06 — Demo container and compose bring up Receiver and LGTM together

**What to build:** One docker compose command starts the LGTM stack and the demo container on a shared network. The demo container runs the Receiver as its main process, as a non-root user, with Claude Code, jira-as and the skill baked in and secrets supplied by an ignored env file. The replay script posted from the laptop into the container produces an Incident in OPS, and the container log shows the formatted Run.

**Blocked by:** 05 — Receiver drives real Runs

**Status:** done

- [x] Dockerfile extends the existing claude-devcontainer image, pip-installs jira-as, copies the package and skill, and sets its own entrypoint that runs the Receiver
- [x] Container runs as the existing non-root user; onboarding is pre-accepted the way the existing entrypoints do it; no bubblewrap or sandbox packages required — **only** `hasCompletedOnboarding`, see the comment
- [x] No Docker socket is mounted; no secret is baked into the image or committed
- [x] A committed env example lists every variable name with placeholder values; compose references an ignored env file
- [x] Compose defines the LGTM service from the published otel-lgtm image and the demo service, on one network, with Grafana reachable on the laptop
- [x] Health endpoint answers from inside the network and, via a published port, from the laptop
- [x] Replay script posted from the laptop creates, advances and Completes an Incident; container log shows formatted Run output including jira-as commands
- [x] README documents build, up, replay, and log tailing commands

## Comments

Done. `docker compose up -d --build` is the whole demo: `lgtm` from the published
`grafana/otel-lgtm` image and `demo` built from this repo's Dockerfile, on one network called
`demo`. The demo container's main process is the Receiver, so a Run is a child of PID 1 and
nothing else runs in there.

Verified on this laptop against the real OPS project, driving the container and not the laptop
process:

    docker compose up -d --build
    DEMO_END_TO_END=1 DEMO_RECEIVER_URL=http://localhost:8080 \
        python3 -m pytest tests/test_end_to_end.py

It passed in 93s. The three replayed Notifications became three Runs inside the container, each
exiting 0, and OPS-10 is what they did:

    Opened from a firing Alert. value=0.0333.
    Still firing. value=0 (previous value=0.0333, down). Open for 24s.
    Resolved after 48s, 2 Firings. value=4.7. Completed automatically from the Grafana Alert.

Run timings from the container log, which is the pace the demo will actually run at: create 35.4s,
repeat 20.4s, resolve 29.5s, $0.46 for the three. Every `jira-as` command appeared in the log in
full, each one paired with the Forwarder's own line saying what it forwarded upstream — the create
is `POST /rest/api/3/issue, upstream said 201` — so the credential boundary is visible on the same
screen as the thing it protects. Cleanup left OPS-10 `Closed` with resolution `Done`.

`DEMO_CONTAINER=1 python3 -m pytest tests/test_container.py` covers the rest with the stack up:
health answered the laptop on the published port and answered `http://demo:8080/health` from
inside the `lgtm` container, the Receiver runs as uid 1000, and both `claude` and `jira-as` are on
the PATH a Run inherits. Checked by hand as well: no `/var/run/docker.sock` in the container, and
no credential variable in the built image's environment.

Four deviations worth recording:

- **The entrypoint does not pre-accept bypass permissions mode.** The ticket says onboarding is
  pre-accepted "the way the existing entrypoints do it", and the earlier demo's entrypoint writes
  `hasCompletedOnboarding` and `bypassPermissionsModeAccepted` together. Writing the second is
  precisely what ADR 0003 refuses — it is the skip-permissions route every other wrapper on this
  machine takes. This entrypoint writes only `hasCompletedOnboarding`, and a Run starts fine
  without the other: `~/.claude/.claude.json` in the running container is one key long.
- **The demo service has no restart policy.** `unless-stopped` would have turned story 47's
  fail-fast into a crash loop: a half-filled `.env` makes the Receiver print which variable is
  missing and exit, and restarting it scrolls that one readable message away. `lgtm` keeps its
  restart policy; `demo` is meant to stay dead and be read.
- **Claude Code is pinned, not upgraded to latest.** The base image's CLI is eight months old
  (2.0.76) and the formatter renders the event shapes of a current one, so the image installs
  `@anthropic-ai/claude-code@2.1.272` — the version these Runs were rehearsed on. `latest` in a
  Dockerfile means a rebuild on demo day can ship a Transcript shape nothing has ever seen.
- **`runs/` is no longer committed.** Three Run working directories from ticket 05's rehearsal
  were in the repository. They are untracked now and the directory is ignored.

### Two things ticket 08 should know

- **The first log line lists every tool, not the allow list.** In the container the Run's opening
  event reports `tools=Task,Bash,CronCreate,DesignSync,...` where the recorded fixture reports
  `tools=Bash,Read`. The boundary is unaffected — `dontAsk` denies everything not on the allow
  list, and the allow list is still `Bash(jira-as *)` and `Read` — but the line an audience reads
  first now says the opposite of what the demo is about. The formatter truncates it, which helps.
  Worth attributing before the demo, and worth not pointing at.
- **These three Runs produced no denials.** The skill never reaches for a tool it cannot have, so
  no `[DENIED]` line appeared in the whole rehearsal. Story 7's audience-visible proof needs
  something that provokes one; `fixtures/run-transcript.jsonl` has a real denial in it and can be
  rendered on screen, or the presenter can ask a Run to do something it cannot.

## What the review changed

The spec review caught the restart policy defeating story 47, which would have shown up as a
container looping silently on a bad `.env` rather than saying what was wrong — the exact failure
the fail-fast exists to prevent. It also caught `.env.example` naming only the four credentials
where the ticket asks for every variable name, and `published_ports` counting a container-only
port spelling as published, which would have let a future "the Receiver is no longer reachable
from the laptop" regression pass.

The standards review caught the entrypoint pre-accepting bypass permissions mode against ADR 0003,
`payload` used for a Notification against CONTEXT.md, and a handful of test-file smells: the
compose file re-parsed on every assertion, a constant named `RUNS_DIRECTORY` colliding with the
environment variable of that name, and a `published_ports` helper handling three compose spellings
where the committed file uses one.

Both reviews flagged the unpinned `CLAUDE_CODE_VERSION=latest` sitting next to a pinned `jira-as`,
and both flagged the tests that read file text rather than driving behaviour. The text-reading
tests that only duplicated a `DEMO_CONTAINER` check are gone; the two that remain —
the last `USER` in the Dockerfile, and no credential named anywhere in it — are kept deliberately,
because they are the only form of those two claims that runs when no stack is up, and both guard a
one-line mistake that would otherwise be found by an audience.
