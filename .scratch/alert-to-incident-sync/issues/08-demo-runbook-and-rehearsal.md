# 08 — Demo runbook and rehearsal

**What to build:** A runbook the presenter can follow cold on 2026-09-15: window layout for Grafana, the container log and the OPS Incidents queue on one screen; the spoken points, including that the Run can only execute jira-as, that the Jira token lives in the Forwarder and the Run holds a sentinel, and that the Anthropic OAuth token is the one credential that is not masked; the fallback path using the replay script if Grafana misbehaves; and a reset procedure that cancels leftover Incidents so the queue starts empty. One timed rehearsal is run and its timings and hiccups are recorded.

**Blocked by:** 07 — Grafana fires the real Alert

**Status:** ready-for-agent

- [ ] Runbook lists pre-demo checks: stack up, health green, queue empty, traffic flowing, Grafana rule Normal
- [ ] Runbook gives the exact presenter actions in order with expected on-screen results and expected wait times
- [ ] Spoken points cover the permission boundary, the credential boundary, the unmasked OAuth token, and the chapter two and three roadmap
- [ ] Fallback section switches to the replay script without restarting anything
- [ ] Reset procedure cancels every open OPS Incident carrying an fp- label and restarts traffic
- [ ] One full rehearsal completed; timings and any hiccups recorded in this ticket
