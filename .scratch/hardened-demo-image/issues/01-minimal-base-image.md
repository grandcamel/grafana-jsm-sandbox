# 01 — The demo image carries only what a Run needs

**What to build:** `docker compose up -d --build` produces a demo image built from the slim official image for the current Node LTS plus Python, holding exactly Claude Code and `jira-as` at pinned versions, this package and the Skill, run by a non-root user the Dockerfile creates. `sudo`, the `docker` CLI, the `docker` group, `gh`, `git`, `curl` and `jq` are gone; the entrypoint pre-accepts onboarding with Python instead of `jq`; the healthcheck uses Python's standard library. The base image is pinned to a tag and stays overridable through the existing build argument. The whole lifecycle still runs: the replay drives an Incident from created to Completed against the rebuilt container. An ADR records that the container is the boundary, the image carries only what a Run needs, and bubblewrap-based sandboxing is deliberately not layered inside it.

**Blocked by:** None — can start immediately

**Status:** done

- [x] The Dockerfile starts from the slim official Node LTS image at a pinned tag, overridable by the existing build argument, and Node in the built image is 22.15 or later
- [x] The image installs only `ca-certificates`, Python 3 with pip, Claude Code and `jira-as` at pinned versions, this package and the Skill; the default-run container check fails if a line installs `sudo`, `docker`, `gh` or `jq`
- [x] The Dockerfile's last `USER` is a non-root user it created; the opt-in stack check finds `sudo`, `docker` and `gh` absent from the PATH inside the running container and `claude` and `jira-as` present
- [x] The entrypoint and the healthcheck need nothing the image does not carry; compose reports the container healthy
- [x] The replay drives one Incident from created to Completed against the rebuilt container, and the outcome and the measured image size are recorded in this ticket
- [x] An ADR records the decision; the README's container section describes the new image

## Comments

Done. The demo image is `node:24.21.0-trixie-slim` (Node 24 is the current LTS; trixie's Python
is 3.13, the same as the laptop's) plus `ca-certificates`, `python3` and `python3-venv` from the
distribution, Claude Code 2.1.272 through npm, `jira-as` 2.0.0 in its own venv under `/opt` with
a symlink on the PATH, this package and the Skill. One user, `demo` (uid 1000), created by the
Dockerfile; the base's `node` account, yarn, corepack and the base's entrypoint are removed. The
last `USER` is `demo`.

Measured: **539 MB**, against 4.35 GB for the image it replaces. A cached rebuild is seconds; the
uncached build on this laptop was about a minute after the base pull. `ls /usr/local/bin` in the
running container is `claude jira-as node nodejs npm npx`; there is no `sudo`, `docker`, `gh`,
`git`, `curl` or `jq`, no `docker` group, and `/etc/passwd` has one account above uid 1000.

Verified on this laptop against the real OPS project, driving the rebuilt container:

    docker compose up -d --build
    python3 -m grafana_jsm_sandbox.reset
    DEMO_END_TO_END=1 DEMO_RECEIVER_URL=http://localhost:8080 \
        python3 -m pytest tests/test_end_to_end.py

It passed in 73s. The three replayed Notifications became three Runs inside the container, each
exiting 0 in 20.7s, 21.2s and 21.5s, and OPS-16 is what they did: opened from the firing Alert,
commented `Still firing ... Open for 15s`, then `Resolved after 35s, 2 Firings ... Completed
automatically from the Grafana Alert`. Cleanup left it Closed with resolution Done. Compose
reports the container healthy on the new standard-library healthcheck.

`DEMO_CONTAINER=1 python3 -m pytest tests/test_container.py` passed all 50: the six escalation
tools absent from a Run's PATH, no `docker` group, Node 24.21.0 (the trust-store threshold is
22.15), the Receiver as uid 1000, `claude` and `jira-as` present, health answered from the laptop
and from inside `lgtm`.

Three things worth recording:

- **npm 11 skips Claude Code's install script unless told otherwise.** The first build printed
  `npm warn install-scripts` and left `claude` as the package's Node stub, which spawns the native
  binary through a wrapper. `claude --version` worked either way, but the rehearsed shape is the
  native binary as PID of the Run, so the Dockerfile passes
  `--allow-scripts=@anthropic-ai/claude-code`; `bin/claude.exe` is now an ELF file and a Run
  is that binary, not a Node process around it.
- **The old entrypoint ignored a failing `jq`.** Running the real script under `sh` on a PATH
  holding only what the slim image carries showed the merge case leaving the onboarding flag
  untouched with exit 0: `jq ... > tmp && mv` inside `set -e` does not stop on the first
  command's failure. The Python replacement writes to a temporary file and `os.replace`s it, and
  the two entrypoint tests would catch a regression.
- **`jira-as` is in a venv, not the system site-packages.** Debian's Python refuses a bare
  `pip install` into the distribution's site-packages (PEP 668); the alternatives were
  `--break-system-packages` or a venv, and a venv also keeps `requests` and the rest out of the
  interpreter the Receiver runs on. `python3-venv` is the one extra distribution package that
  buys.

Not done here, by design: the compose hardening (ticket 03) and the certificate mechanism
(ticket 02). ADR 0005 names the compose controls as the place the runtime boundary lives so that
ticket 03 lands under a decision already recorded.

## What the review changed

Both the standards and the spec review caught the README and ADR 0005 listing four executables in
`/usr/local/bin` where the verified container shows six: `nodejs` (a symlink to `node`) and `npx`
were left out of an audience-facing claim that the same diff's own record contradicted. Both now
list all six. The standards review also caught "event shapes" in a Dockerfile comment, where
CONTEXT.md says a Run event is never shortened to "event" on its own. Neither review found a
missing requirement for this ticket, and both judged removing the base's `node` account, yarn and
corepack, and allowing Claude Code's install script, reasonable and recorded.
