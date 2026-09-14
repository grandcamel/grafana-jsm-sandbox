# 05 — Receiver drives real Runs end to end

**What to build:** On the laptop, a replay script posts the firing, repeat and resolved Notifications to the Receiver, and the Incident appears, advances and Completes in OPS without any manual step. Each Run gets a scrubbed environment with a per-Run sentinel, the Forwarder registers and clears that sentinel around the Run, a stuck Run is killed on timeout, and the Run's output flows through the log formatter into the Receiver's log. An opt-in end-to-end test asserts the result by JQL.

**Blocked by:** 01 — Receiver accepts a Notification; 02 — Log formatter; 03 — Forwarder; 04 — Run skill

**Status:** ready-for-agent

- [ ] The real spawner builds the Run's environment from scratch: Anthropic OAuth token, Jira email, site URL pointing at the Forwarder over http, token equal to the Run's sentinel, PATH; nothing inherited
- [ ] The Forwarder runs as a thread inside the Receiver process; the sentinel is registered before spawn and cleared after exit
- [ ] Run stdout is piped through the formatter line by line into the log; stderr is captured and logged on non-zero exit
- [ ] A Run exceeding the timeout is killed, logged, and does not block the queue
- [ ] Receiver fails fast at startup when Jira credentials or the Anthropic token are missing
- [ ] A replay script posts the three canned Notifications in order with a configurable pause
- [ ] An end-to-end test, enabled by an environment flag and skipped otherwise, runs the replay and asserts by JQL: one Incident with the Fingerprint label, at least two comments, final status Completed; then cancels it
- [ ] Default pytest run stays green and fast with the end-to-end test skipped
