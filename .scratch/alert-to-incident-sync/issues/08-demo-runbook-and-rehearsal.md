# 08 — Demo runbook and rehearsal

**What to build:** A runbook the presenter can follow cold on 2026-09-15: window layout for Grafana, the container log and the OPS Incidents queue on one screen; the spoken points, including that the Run can only execute jira-as, that the Jira token lives in the Forwarder and the Run holds a sentinel, and that the Anthropic OAuth token is the one credential that is not masked; the fallback path using the replay script if Grafana misbehaves; and a reset procedure that cancels leftover Incidents so the queue starts empty. One timed rehearsal is run and its timings and hiccups are recorded.

**Blocked by:** 07 — Grafana fires the real Alert

**Status:** done

- [x] Runbook lists pre-demo checks: stack up, health green, queue empty, traffic flowing, Grafana rule Normal
- [x] Runbook gives the exact presenter actions in order with expected on-screen results and expected wait times
- [x] Spoken points cover the permission boundary, the credential boundary, the unmasked OAuth token, and the chapter two and three roadmap
- [x] Fallback section switches to the replay script without restarting anything
- [x] Reset procedure cancels every open OPS Incident carrying an fp- label and restarts traffic
- [x] One full rehearsal completed; timings and any hiccups recorded in this ticket

## Rehearsal record

One full take on 2026-09-15, presenter clock in UTC, driven exactly as the runbook says: the reset
first, then `docker compose stop traffic`, then `docker compose start traffic` once the Incident
was in Work in progress. Grafana's rule state was polled every five seconds, so the "seen" times
are up to five seconds late; the Run times are from the container log.

| Moment | Clock | Since the action |
| --- | --- | --- |
| `docker compose stop traffic` issued | 13:04:43 | T+0 |
| ... returned | 13:04:54 | **11s** (see hiccups) |
| Grafana: Pending (seen) | 13:05:13 | 30s |
| Grafana: Firing (seen) | 13:05:42 | 59s |
| Firing Notification: Run started | 13:05:50 | **67s** |
| OPS-14 created | 13:06:15 | 92s |
| Run finished (29.7s, $0.16) | 13:06:19 | 96s |
| First repeat: Run started | 13:07:00 | **70s after the first Run** |
| Trend comment, Work in progress, Run finished (29.3s, $0.15) | 13:07:29 | 2m46s |
| `docker compose start traffic` issued | 13:07:30 | T+2m47s |
| Grafana: Normal (seen) | 13:07:45 | 15s after the start |
| Resolved Notification: Run started | 13:07:49 | **19s after the start** |
| OPS-14 Completed with resolution Done, Run finished (26.8s, $0.15) | 13:08:16 | 3m33s |

Whole lifecycle, stop to Completed: **3m33s**, three Runs, $0.46. Within a few seconds of the
second rehearsal in ticket 07 at every step, so the runbook's table uses these numbers rounded to
the nearest five seconds. Still no `[DENIED]` line from a live Run; the runbook points the
presenter at the recorded Transcript for that picture.

### Hiccups

1. **`docker compose stop traffic` took 11 seconds to return.** The traffic service is a shell
   loop, which ignores SIGTERM, so Docker waited out its ten-second grace period before killing
   it. The traffic kept flowing for those ten seconds too. Fixed in `docker-compose.yml` with
   `stop_grace_period: 1s` on the service; measured afterwards, a stop returns in 1.5s and a
   start in 1.7s. The timings above were taken before the fix and are measured from the moment
   the command was issued, which is also how ticket 07 measured, so they are comparable.
2. **The Incidents queue does not start empty, and the reset cannot make it.** Queue 608 is
   `resolution = Unresolved AND issuetype = Incident`, and the six probe Incidents from ticket 04,
   OPS-1 to OPS-6, are `Canceled` or `Closed` with no resolution and no transition left that
   could set one (ADR 0004). The reset as first written said `queue is empty` while the queue
   showed six. It now searches for exactly that shape, reports each as stuck with the one-line
   delete command, and exits 1, because whether to delete them is the presenter's call and the
   reset never deletes. The runbook gives the alternative of projecting a `statusCategory != Done`
   filter instead of the queue, which needs no deletion. **This is the one open decision before
   the demo.**
3. **Jira's search index lags the resolution.** Ten seconds after OPS-14 was Completed, the
   unresolved JQL still listed it; a minute later it did not. The runbook says to count to twenty
   before reloading the queue on the last step.
4. The reset ran clean at the start of the take with nothing open (exit 0 at the time, traffic
   started), and correctly did not touch OPS-14 afterwards, since a Completed Incident with a
   resolution is already out of the queue.

## Comments

Done. The runbook is `docs/demo-runbook.md`: the three-window screen with URLs, five pre-demo
checks with their commands and what passing looks like, a step table of presenter actions with
what the audience sees and what to say through each wait, the four spoken points each with one
thing on screen to point at, the replay fallback, and the reset. The README links it and
documents the reset.

**Reset semantics differ from the ticket's verb, deliberately.** The ticket says "cancels every
open OPS Incident carrying an fp- label". `Canceled` carries no resolution on this workflow and
has no way out but `Close`, which also refuses one, so a cancelled Incident sits in the Incidents
queue for good — ADR 0004, verified in ticket 04 and again by the six probes above. The reset
therefore takes the only clean exit: `Resolve` with resolution Done, a comment saying the reset did
it, then `Close`. The acceptance criterion's intent, the queue starting empty, is what it serves.
`grafana_jsm_sandbox/reset.py` takes `jira-as` and `docker compose` as injected callables, like
the Receiver's spawner, and `tests/test_reset.py` drives it against a fake OPS that has the real
workflow's transitions; eight tests, offline.

**Accepted from ticket 07's notes:** the empty `Dashboard:` and `Panel:` lines in the Description
stay. Provisioning a dashboard for one link is not a runbook concern; the runbook's small print
says why they are empty.

**Not done, on purpose:** nothing was deleted in OPS. The rehearsal Incident OPS-14 is left
Completed with resolution Done, out of the queue, like OPS-11 and OPS-13 before it.

## What the review changed

The standards review found no documented-standard violations and one duplication: the reset had
its own copies of the "read the transitions off the issue and take the one landing on a status",
"search and return the issues" and "run jira-as and fail loudly" helpers that
`tests/test_end_to_end.py` already had. They live in `grafana_jsm_sandbox/reset.py` now and the
end-to-end check imports them, so the two encodings of ADR 0004's exit rule cannot drift apart.

The spec review found the runbook's pre-demo step 3 contradicting itself: it promised `queue is
empty` and exit 0, and the next paragraph said the reset ends `queue is NOT empty` today because
of the six probes. Step 3 now states the exit the presenter will actually see until the probes
are decided, and the probe paragraph is headed as the decision it is.

After the refactor, `DEMO_END_TO_END=1 DEMO_RECEIVER_URL=http://localhost:8080 python3 -m pytest
tests/test_end_to_end.py` passed in 84s against the container, driving OPS-15 from created to
Completed with resolution Done and closing it through the shared helpers on the way out. The
rehearsal's OPS-14 stays Completed.
