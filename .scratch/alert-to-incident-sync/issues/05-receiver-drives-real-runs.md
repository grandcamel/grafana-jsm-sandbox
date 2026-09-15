# 05 — Receiver drives real Runs end to end

**What to build:** On the laptop, a replay script posts the firing, repeat and resolved Notifications to the Receiver, and the Incident appears, advances and Completes in OPS without any manual step. Each Run gets a scrubbed environment with a per-Run sentinel, the Forwarder registers and clears that sentinel around the Run, a stuck Run is killed on timeout, and the Run's output flows through the log formatter into the Receiver's log. An opt-in end-to-end test asserts the result by JQL.

**Blocked by:** 01 — Receiver accepts a Notification; 02 — Log formatter; 03 — Forwarder; 04 — Run skill

**Status:** done

- [x] The real spawner builds the Run's environment from scratch: Anthropic OAuth token, Jira email, site URL pointing at the Forwarder over http, token equal to the Run's sentinel, PATH; nothing inherited
- [x] The Forwarder runs as a thread inside the Receiver process; the sentinel is registered before spawn and cleared after exit
- [x] Run stdout is piped through the formatter line by line into the log; stderr is captured and logged on non-zero exit
- [x] A Run exceeding the timeout is killed, logged, and does not block the queue
- [x] Receiver fails fast at startup when Jira credentials or the Anthropic token are missing
- [x] A replay script posts the three canned Notifications in order with a configurable pause
- [x] An end-to-end test, enabled by an environment flag and skipped otherwise, runs the replay and asserts by JQL: one Incident with the Fingerprint label, at least two comments, final status Completed; then cancels it — **resolves and closes it instead**, see the comment
- [x] Default pytest run stays green and fast with the end-to-end test skipped

## Comments

Done. `RunSpawner` is the real spawner, `python3 -m grafana_jsm_sandbox` is the whole process
(Forwarder thread, Receiver, spawner), and `python3 -m grafana_jsm_sandbox.replay` posts the
canned sequence. Verified on the laptop: three replayed Notifications became three serialized
Runs, each a real `claude` child process with a scrubbed environment, each Transcript rendered
into the log.

Three deviations worth recording:

- The end-to-end check **resolves and closes** the Incident it watched instead of cancelling it.
  ADR 0004 found after this ticket was written that `Canceled` sets no resolution and has no way
  out but `Close`, so a cancelled Incident sits in the Incidents queue for good — the opposite of
  cleaning up. It leaves the rehearsal's Incident `Closed` with a resolution instead.
- The Run's environment is the five variables the ticket names and nothing else. macOS adds
  `LC_CTYPE` and `__CF_USER_TEXT_ENCODING` to every child process below the spawner, which the
  test excludes rather than allows for; the container is Linux and adds neither.
- The end-to-end check identifies its own Incident rather than assuming OPS is empty. Four
  Incidents already carry this Fingerprint from ticket 04's rehearsals, and this check leaves a
  fifth, so "the one Incident with the label" would have been a check that passed once and never
  again. It records the keys that exist before the replay and watches for one that does not.

## What the review changed

The spec review found one bug that would have shown up in front of the audience: `_kill` ended
only the Run itself, and a Run is the Claude CLI with a shell and a `jira-as` under it. Those
grandchildren hold the Transcript pipe, so a timed-out Run left the Receiver reading a pipe that
never closed and the single worker stalled for as long as the orphan lived — the exact thing the
timeout exists to prevent. A Run is now started in its own session and the timeout ends the whole
session. `test_the_timeout_also_ends_what_the_run_started` is the test; without the fix it hangs
for thirty seconds and then fails, which is how it was verified.

Also from the review: the replay is inside the end-to-end check's `try`, so a Notification that
fails to post cannot leave an Incident behind uncleaned; cleanup never closes an Incident that has
no resolution, because `Closed` without one is the same trap as `Canceled`; a failed Run's stderr
is logged as a bounded tail rather than one unbounded line; and the kill timer no longer reports a
timeout it lost the race to.

## Verified against OPS

`DEMO_END_TO_END=1 python3 -m pytest tests/test_end_to_end.py` passed in 97s against a Receiver
started with a real Anthropic token: the replayed sequence created **OPS-9**, commented the trend
on the repeat, and Completed it with a resolution, all without a manual step. Its three comments
are what the skill asks for, and both durations came off the Jira clock rather than Grafana's:

    Opened from a firing Alert. value=0.0333.
    Still firing. value=0 (previous value=0.0333, down). Open for 22s.
    Resolved after 50s, 2 Firings. value=4.7. Completed automatically from the Grafana Alert.

Cleanup left OPS-9 `Closed` with resolution `Done`, so the check added nothing to the Incidents
queue and can be run again. The six `Canceled` Incidents from ticket 04 are still stuck there; see
that ticket's own open item.
