# 06 — Demo container and compose bring up Receiver and LGTM together

**What to build:** One docker compose command starts the LGTM stack and the demo container on a shared network. The demo container runs the Receiver as its main process, as a non-root user, with Claude Code, jira-as and the skill baked in and secrets supplied by an ignored env file. The replay script posted from the laptop into the container produces an Incident in OPS, and the container log shows the formatted Run.

**Blocked by:** 05 — Receiver drives real Runs

**Status:** ready-for-agent

- [ ] Dockerfile extends the existing claude-devcontainer image, pip-installs jira-as, copies the package and skill, and sets its own entrypoint that runs the Receiver
- [ ] Container runs as the existing non-root user; onboarding is pre-accepted the way the existing entrypoints do it; no bubblewrap or sandbox packages required
- [ ] No Docker socket is mounted; no secret is baked into the image or committed
- [ ] A committed env example lists every variable name with placeholder values; compose references an ignored env file
- [ ] Compose defines the LGTM service from the published otel-lgtm image and the demo service, on one network, with Grafana reachable on the laptop
- [ ] Health endpoint answers from inside the network and, via a published port, from the laptop
- [ ] Replay script posted from the laptop creates, advances and Completes an Incident; container log shows formatted Run output including jira-as commands
- [ ] README documents build, up, replay, and log tailing commands
