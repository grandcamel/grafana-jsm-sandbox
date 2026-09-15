# 01 — The demo image carries only what a Run needs

**What to build:** `docker compose up -d --build` produces a demo image built from the slim official image for the current Node LTS plus Python, holding exactly Claude Code and `jira-as` at pinned versions, this package and the Skill, run by a non-root user the Dockerfile creates. `sudo`, the `docker` CLI, the `docker` group, `gh`, `git`, `curl` and `jq` are gone; the entrypoint pre-accepts onboarding with Python instead of `jq`; the healthcheck uses Python's standard library. The base image is pinned to a tag and stays overridable through the existing build argument. The whole lifecycle still runs: the replay drives an Incident from created to Completed against the rebuilt container. An ADR records that the container is the boundary, the image carries only what a Run needs, and bubblewrap-based sandboxing is deliberately not layered inside it.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] The Dockerfile starts from the slim official Node LTS image at a pinned tag, overridable by the existing build argument, and Node in the built image is 22.15 or later
- [ ] The image installs only `ca-certificates`, Python 3 with pip, Claude Code and `jira-as` at pinned versions, this package and the Skill; the default-run container check fails if a line installs `sudo`, `docker`, `gh` or `jq`
- [ ] The Dockerfile's last `USER` is a non-root user it created; the opt-in stack check finds `sudo`, `docker` and `gh` absent from the PATH inside the running container and `claude` and `jira-as` present
- [ ] The entrypoint and the healthcheck need nothing the image does not carry; compose reports the container healthy
- [ ] The replay drives one Incident from created to Completed against the rebuilt container, and the outcome and the measured image size are recorded in this ticket
- [ ] An ADR records the decision; the README's container section describes the new image
