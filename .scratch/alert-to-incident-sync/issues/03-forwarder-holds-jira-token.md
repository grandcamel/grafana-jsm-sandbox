# 03 — Forwarder holds the Jira token and serves a sentinel-authenticated caller

**What to build:** A caller that knows only a sentinel can run jira-as against the real OPS project by pointing its site URL at the Forwarder on loopback. The Forwarder swaps the sentinel for the real credential and forwards to the configured Atlassian site; a wrong sentinel gets nothing; the real token never appears in any log line. Demoable by running a JQL search from the laptop with the sentinel and forwarder URL in the environment.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] Forwarder binds to loopback only and takes its upstream host, email and token from configuration, never from the request
- [ ] A request whose basic-auth password equals the active sentinel is forwarded with the real email and token in the Authorization header; the sentinel does not reach upstream
- [ ] A request with a missing or non-matching sentinel gets 401 and no upstream call is made
- [ ] Upstream status, headers (minus hop-by-hop) and body pass back unchanged, for GET, POST with JSON body, and PUT
- [ ] The active sentinel can be set and cleared by the owning process, so a stale sentinel from a previous Run is rejected
- [ ] Startup fails fast with a clear message if site URL, email or token are missing
- [ ] Tests run against a fake upstream server on an ephemeral port and assert the log output contains neither the real token nor any Authorization header
- [ ] Manual check recorded in the ticket: jira-as JQL search on OPS succeeds through the Forwarder with a sentinel token
