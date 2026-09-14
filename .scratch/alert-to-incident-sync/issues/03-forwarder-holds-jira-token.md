# 03 — Forwarder holds the Jira token and serves a sentinel-authenticated caller

**What to build:** A caller that knows only a sentinel can run jira-as against the real OPS project by pointing its site URL at the Forwarder on loopback. The Forwarder swaps the sentinel for the real credential and forwards to the configured Atlassian site; a wrong sentinel gets nothing; the real token never appears in any log line. Demoable by running a JQL search from the laptop with the sentinel and forwarder URL in the environment.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [x] Forwarder binds to loopback only and takes its upstream host, email and token from configuration, never from the request
- [x] A request whose basic-auth password equals the active sentinel is forwarded with the real email and token in the Authorization header; the sentinel does not reach upstream
- [x] A request with a missing or non-matching sentinel gets 401 and no upstream call is made
- [x] Upstream status, headers (minus hop-by-hop) and body pass back unchanged, for GET, POST with JSON body, and PUT
- [x] The active sentinel can be set and cleared by the owning process, so a stale sentinel from a previous Run is rejected
- [x] Startup fails fast with a clear message if site URL, email or token are missing
- [x] Tests run against a fake upstream server on an ephemeral port and assert the log output contains neither the real token nor any Authorization header
- [x] Manual check recorded in the ticket: jira-as JQL search on OPS succeeds through the Forwarder with a sentinel token

## Comments

**2026-09-14 — implemented.** Every acceptance criterion is covered by a test in
`tests/test_forwarder.py`; 108 tests pass from a clean checkout with `python3 -m pytest`, and
ruff and mypy are clean.

- `grafana_jsm_sandbox/forwarder.py` — the Forwarder, the sentinel check, the header swap and the
  `JiraCredential` the owning process reads from its environment.
- `tests/upstream.py` — the fake Atlassian site the Forwarder tests run against.
- `CONTEXT.md` — Sentinel now has a glossary entry; it was load-bearing vocabulary without one.

**Manual check, run twice against the real site (`jasonkrue.atlassian.net`).** With
`python3 -m grafana_jsm_sandbox.forwarder` holding the token and jira-as holding only a
32-character sentinel:

- `jira-as search jql "project = OPS ORDER BY created DESC" --max-results 3` → `Found 0 issue(s)`,
  and the Forwarder logged `forwarded GET /rest/api/3/search/jql?jql=project+%3D+OPS... upstream
  said 200`. OPS has no Incidents yet, so zero results is the right answer; the 200 is the proof
  the real credential was attached, since that endpoint answers 401 without one.
- `jira-as api call getCurrentUser` through the same sentinel returned
  `"emailAddress": "jasonkrue@gmail.com"`, so the forwarded request was authenticated as the real
  account rather than merely reaching the site.
- The same search with `JIRA_API_TOKEN=not-the-sentinel` was refused and never reached upstream.
- The Forwarder's whole log for both runs contains no token and no Authorization header.

Three things beyond the checklist, two of them from the code review:

- An upstream that cannot be reached returns `502` rather than letting the exception drop the
  connection, which is the same fix ticket 01 made for the Receiver's `500`.
- A basic-auth password that is not ASCII used to crash the handler inside
  `secrets.compare_digest` instead of being refused. It is now refused like any other wrong
  sentinel, with a test for it.
- A redirect from upstream is handed back rather than followed, so the Forwarder cannot be walked
  off the configured site.

Known and deliberate: the Forwarder answers GET, POST, PUT, DELETE and PATCH, not literally every
method — HEAD and OPTIONS get the `BaseHTTPRequestHandler` 501 before the sentinel is checked.
jira-as sends none of them, and HEAD would need its own no-body handling to be correct rather than
merely present. The standalone `python3 -m grafana_jsm_sandbox.forwarder` entry point is the
vehicle for the manual check above; the Receiver owns the Forwarder and registers each Run's
sentinel in ticket 05.
