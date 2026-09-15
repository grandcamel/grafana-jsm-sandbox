# 04 — Run skill drives one Alert through its Incident lifecycle on OPS

**What to build:** Running Claude headless by hand from the laptop, with the purpose-built skill and a canned Notification, produces the right Incident behaviour in OPS: a Firing Alert with no Match creates an Open Incident carrying the Fingerprint label and the field mapping; a repeat Firing comments with the trend and moves it to Work in progress; a Resolved Alert comments and Completes it. The Run is started in dontAsk mode with only jira-as and file reading allowed, and its Jira traffic goes through the Forwarder. This is where the transition names and the resolution behaviour flagged in the spec get verified against a real issue.

**Blocked by:** 03 — Forwarder holds the Jira token

**Status:** ready-for-human

- [x] Three canned Notification fixtures exist: firing, repeat firing with a different value, resolved, all sharing one Fingerprint
- [x] The skill file states the OPS facts, the label format, the match JQL, the field mapping, the lifecycle rule, and the rule to read transition ids by name from the issue, in terms of jira-as invocations only
- [x] The Run command line uses print mode, dontAsk permission mode, an allow list of jira-as execution and Read, stream-json with verbose, and the skill directory
- [x] Firing with no Match: an Incident is created in Open with Summary, Description including annotations and links, Source Monitoring systems, Severity and Urgency per mapping, Component from the service label, and label fp-<fingerprint>
- [x] Repeat Firing: exactly one comment is added stating current value, change since the previous comment, and time since open; status becomes Work in progress; no second Incident is created
- [x] A further repeat only comments; status stays Work in progress
- [x] Resolved: one closing comment stating duration and firing count; status becomes Completed; the Incident leaves the Incidents queue (resolution is set, or the ticket records how it must be set)
- [x] Resolved with no Match: nothing is created; the Run reports it skipped
- [x] The Run ends with a one-line summary per Alert
- [x] A recorded stream-json transcript from one real Run is saved as a fixture for ticket 02's formatter
- [ ] Leftover test Incidents are taken out of the Incidents queue at the end — **not done**: the criterion says `Canceled`, and `Canceled` turns out to be the one status from which an Incident can never leave the queue. Six are stuck there. See the comment

## Comments

**2026-09-14 — implemented.** 130 tests pass from a clean checkout with `python3 -m pytest`; ruff
and mypy are clean. The lifecycle below was driven five times against the real OPS project on
`jasonkrue.atlassian.net`, with every Jira request going through the Forwarder and the Run holding
only a sentinel.

- `skill/incident-sync/SKILL.md` — the skill a Run follows. Every operation is a `jira-as`
  invocation, because nothing else executes.
- `grafana_jsm_sandbox/run_command.py` — the Run's command line and its allow list, which ticket 05
  hands to `subprocess`. `NOTIFICATION_FILENAME` moved from `receiver.py` to `notification.py` so
  both can name the file without the Receiver importing the command line or the other way round.
- `fixtures/notification-firing-repeat.json`, `fixtures/notification-resolved.json` — the rest of
  the canned sequence, and `tests/test_notification_fixtures.py` asserts the three work as one.
- `fixtures/run-transcript-repeat-firing.jsonl` — a real Run's Transcript, for ticket 02.

### What the five Runs did, in order, to OPS-7

| Run | Notification | Result |
| --- | --- | --- |
| 1 | firing | Created OPS-7 in `Open`: Summary `rolldice request rate is zero on rolldice:8080`, Description with both annotations and the three links on their own lines, Source `Monitoring systems`, Sev-1, Urgency `Critical`, no component, label `fp-a1b2c3d4e5f60718`. Comment `Opened from a firing Alert. value=0.0333.` |
| 2 | repeat firing | One comment, `Still firing. value=0 (previous value=0.0333, down). Open for 32s.`, then `Work in progress` |
| 3 | repeat firing | One comment, `Still firing. value=0 (previous value=0, unchanged). Open for 1m15s.`, no transition |
| 4 | resolved | `Resolved after 1m45s, 3 Firings. value=4.7.`, then `Completed` with resolution `Done` |
| 5 | resolved | Skipped: no open Incident carries the Fingerprint. Nothing created |

Each Run ended with one line per Alert. No Run created a second Incident, set Sev-0, or touched
Major incident. OPS-7 finished `Completed` / `Done` and left the Incidents queue.

### Four things the real Runs settled that the spec had guessed at

**A `jira-as` command that is not one plain line is denied whole.** Split across lines with `\`,
or carrying a newline inside a quoted argument, or using `$'...'` — all three fail to match
`Bash(jira-as *)` and are denied without a prompt. The first Run lost its Description's line breaks
to this before the skill said so. The skill now says so twice, and gets paragraphs from a single
line of ADF passed through `--custom-fields` instead. (`issue create` has no `--format`; only
`issue update` does.)

**A Run has no clock.** `date` is not on the allow list, so the only time a Run can read is Jira's,
via `api call getServerInfo`. Durations are `serverTime` minus the Incident's `created` — both
Jira's clock. An earlier skill measured from the Alert's `startsAt` and a replayed fixture dated
tomorrow produced `Open for -15h55m3s`. `getServerInfo` is site-scoped, so the Run's environment
needs `JIRA_ALLOW_SITE_OPERATIONS=true`: **ticket 05 must put it in the scrubbed environment and
ticket 06 in the container's settings**, or every duration breaks.

**The create records its own value.** Without it the first repeat has nothing to compare against
and writes `previous value=none`. One extra comment at create time gives the first repeat a real
trend and makes the closing Firing count exact — it is the number of `value=` comments.

**`Canceled` is a trap, so the cleanup criterion changed.** Only the `Resolve` transition accepts
`--resolution` on this workflow; `Cancel` and `Close` have it rejected by their screens and
`editIssue` cannot set it. The Incidents queue is `resolution = Unresolved`, and `Canceled` leads
nowhere but `Closed`, so an Incident parked in `Canceled` sits in the audience's queue permanently.
Leftovers now leave by `Resolve --resolution Done`. Recorded in ADR 0004.

### A seventh Run, for the half of the Component rule the lifecycle never reaches

`rolldice` is not a seeded OPS component, so the five Runs above only ever proved the empty
fallback (story 27). A sixth Notification — same shape, `service: Jira`, `severity: warning` —
created **OPS-8** with component `Jira`, Sev-2 and Urgency `High`, which is the other end of both
mappings. It was then taken to `Completed` / `Done`, so it is out of the queue.

Nothing in tickets 06 or 07 seeds a `rolldice` component, so on the day the demo will show an
Incident with no component. That is correct behaviour, but worth saying out loud before someone
reads a blank field as a bug.

### Deviations from the spec, deliberate

- **No body-from-file.** The spec says "Body for create and edit goes through jira-as's
  body-from-file mechanism; the Run writes those JSON files in its working directory." A Run has no
  `Write` — ADR 0003's allow list is `Bash(jira-as *)` and `Read` — so it cannot write one. Every
  body is inline instead, and the Description is one line of ADF under `--custom-fields`.
- **No `edit`.** ADR 0004 lists edit among the platform operations a Run uses. This lifecycle never
  needs one: everything after the create is a comment or a transition.
- **One comment the spec did not ask for.** Story 29 asks for a comment per repeat Firing. The
  create adds one too, recording the value it opened at, because without it the first repeat has
  nothing to compare against.

### Still open

Everything this ticket asked to be built is built and committed; the status is `ready-for-human`
rather than `done` for the one criterion below that no agent can finish — deleting an issue is the
user's call, and `Canceled` leaves no other way out (ADR 0004).

- **Six test Incidents are stuck in the Incidents queue**: OPS-1 through OPS-6, from before the
  `Canceled` trap was understood. They are `Canceled` or `Closed` with no resolution and no
  transition left that could set one, so they cannot be cleaned up — only deleted, which is the
  user's call: `jira-as api call deleteIssue --issueIdOrKey OPS-1` and so on. OPS-7 and OPS-8 are
  `Completed` / `Done` and are not in the queue.
- **The fixtures assume the rule fires on a threshold, not on exact equality.** The first Firing
  reports `values.A = 0.0333` and the repeat `0`, which is what a 30-second rate does as the last
  requests fall out of the window. Ticket 07 provisions the real rule and owns reconciling any
  difference *in the fixtures*; if the rule it writes can only fire at exactly zero, these two
  values become equal and the trend comment reads `unchanged` rather than `down`.
- **The `resolved` Alert whose Match is still in `Open` was never run.** The Runs above closed an
  Incident from `Work in progress`. The skill treats both the same and the transition is read off
  the issue either way, so the risk is low, but it is untested.
- **Two things the recorded Transcript does not show, and why.** Its `init` Run event lists every
  tool the host offers, because `--allowedTools` restricts what may be *used*, not what is offered;
  `permission_denials` is empty because that particular Run made no denied call. The denial a demo
  audience needs to see is in `fixtures/run-transcript.jsonl` from ticket 02. Both Runs were
  started by `build_run_command`.
- **`python3 -m grafana_jsm_sandbox.log_formatter ... | head` ends in a `BrokenPipeError`
  traceback.** Ticket 02's entry point, harmless, but ugly if a presenter pipes it on stage.
- The by-hand Run inherited its environment apart from the Jira variables, which were overridden
  with the Forwarder's URL and the sentinel. Building the environment from scratch with the
  Anthropic token in it is ticket 05's first criterion.
