# 03 — The demo container runs the way Anthropic's deployment guide describes

**What to build:** The demo service runs with every Linux capability dropped, `no-new-privileges`, a read-only root filesystem with tmpfs for the temp directory, the runs directory and the Run user's home, a process limit, and memory and CPU limits sized for three Runs in a row on a laptop. The lifecycle still runs end to end under those limits. The default test run reads each control off the committed compose file; the opt-in stack run proves the root filesystem refuses a write and the tmpfs paths accept one. The runbook's spoken points name which controls are Anthropic's recommendations.

**Blocked by:** 01 — The demo image carries only what a Run needs

**Status:** ready-for-agent

- [ ] The demo service declares `cap_drop: [ALL]`, `no-new-privileges`, `read_only: true`, tmpfs mounts for the temp directory, the runs directory and the Run user's home, `pids_limit`, and memory and CPU limits; each is read off the compose file by a default-run check
- [ ] The opt-in stack check shows a write to the root filesystem refused and a write to each tmpfs path accepted, from inside the running container
- [ ] The Receiver starts, the onboarding flag is written, and the replay drives an Incident from created to Completed under the limits; the outcome is recorded in this ticket
- [ ] The runbook's spoken points say which controls come from Anthropic's secure-deployment guide and which are this repo's, and the README's container section lists the hardening
