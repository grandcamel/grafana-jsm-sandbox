# 07 — Grafana fires the real Alert from synthetic traffic

**What to build:** With the stack up, a rolldice example app receives synthetic traffic and Grafana is quiet. The presenter stops the traffic service; within about a minute Grafana fires the Alert, the Receiver gets the Notification, and an Incident appears in OPS. Repeat Firings arrive every minute and add trend comments. The presenter restarts traffic; the Alert resolves and the Incident Completes. Total lifecycle under five minutes, driven entirely from this repo's provisioning files.

**Blocked by:** 06 — Demo container and compose

**Status:** done

- [x] Provisioning files in this repo, mounted into the LGTM container's alerting provisioning directory, define a webhook contact point aimed at the demo service, a notification policy with one-minute repeat interval and short group wait, and one alert rule
- [x] The rule fires when the rolldice request rate is zero for thirty seconds, evaluated every ten seconds, with labels for severity and service that the field mapping consumes
- [x] rolldice and its traffic generator run as compose services; stopping and starting the traffic service is the only presenter action
- [x] Grafana shows the rule Firing, then Normal, on the laptop
- [x] The Notification Grafana sends passes the Receiver's validation unchanged; any shape difference from the canned fixtures is reconciled in the fixtures, not by loosening validation
- [x] Observed timings for fire, first repeat, and resolve are recorded in the ticket
- [x] The four-hour default repeat interval is overridden and the override is documented in the README

## Observed timings

From the container log of the second rehearsal on 2026-09-15 (the first is under *What the review
changed*), presenter clock in UTC. The only presenter actions were `docker compose stop traffic`
at 03:54:20 and `docker compose start traffic` at 03:57:00.

| Moment | Log time | Since the action |
| --- | --- | --- |
| Alert `startsAt` (Grafana's clock) | 03:55:20 | 60s after the stop |
| Firing Notification: Run started | 03:55:30 | **70s after the stop** |
| Incident OPS-13 created, Run finished (19.6s, $0.16) | 03:55:50 | 90s |
| First repeat Firing: Run started | 03:56:40 | **70s after the first Notification** |
| Trend comment, moved to Work in progress, Run finished (20.6s, $0.15) | 03:57:01 | |
| Alert `endsAt` (Grafana's clock) | 03:57:10 | 10s after the start |
| Resolved Notification: Run started | 03:57:20 | **20s after the start** |
| OPS-13 Completed with resolution Done, Run finished (30.2s, $0.16) | 03:57:50 | |

Whole lifecycle, stop to Completed: **3m30s**, three Runs, $0.47. Grafana showed the rule Pending,
then Firing, then Normal on the laptop throughout. The 60s from stop to `startsAt` is the sum of
the rule's parts: the 20s rate window has to empty (plus one 5s export), then the 30s pending
period, then the next 10s evaluation.

## Comments

Done. `docker compose up -d --build` now brings up four services: `lgtm`, `demo`, `rolldice`
and `traffic`. The three provisioning files under `grafana/provisioning/alerting/` are mounted
read-only over the LGTM image's alerting provisioning directory, and the rehearsal above ran the
whole lifecycle from Grafana with no replay involved, twice: OPS-11 and then OPS-13 were created
from the Firing, commented and moved to Work in progress on the repeat, and Completed with
resolution Done on the Resolved. Both are left Completed rather than Closed; the classifier
declined the closing transition in this session, and Completed with a resolution is already out
of the Incidents queue.

**The metric.** The Python auto-instrumentation in this image version (opentelemetry-distro
0.60b0, default semantic conventions) exports `http_server_duration_milliseconds_count`, not
`http_server_request_duration_seconds_count`, and Prometheus promotes `service.name` to a
`service_name` label. The rule's query is
`sum by (instance) (rate(http_server_duration_milliseconds_count{service_name="rolldice"}[20s]))`,
and the opt-in check `test_the_rule_watches_a_metric_rolldice_really_exports` runs the rule's own
query against Prometheus so a change of image version that renames the metric is found by a test
and not by an audience. The `instance` label the field mapping reads comes from the series
itself — `service.instance.id` is pinned to `rolldice:8082` in compose — so the rule declares only
`severity` and `service`.

**The real Notification passed validation unchanged.** All three arrived as 202s and nothing in
`notification.py` moved. The shape differences from the hand-written fixtures were: `orgId` on
each Alert as well as the top level; a `message` field at the top level; `generatorURL` carrying
`?orgId=1`; a real `silenceURL`; `dashboardURL` and `panelURL` present but empty, because the rule
is linked to no dashboard; a `title` that includes the labels; and a two-part `groupKey`. All
reconciled in the fixtures, which are now the three Notifications Grafana actually posted,
pretty-printed and otherwise untouched. Two consequences:

- The fixtures' Fingerprint is the real Alert's, `87e2f184874a3b71`, so the replay fallback
  drives the same Incident the live Alert would. If the live Alert has already opened an Incident
  when the fallback is needed, the replayed Firing comments on it instead of creating a second one
  — the demo working, not a bug. The replay and the live Alert must not run at the same time, and
  the end-to-end check's "no open Match first" precondition now also means "not while Grafana is
  Firing".
- A repeat Firing is byte-identical to the first, values included, so the trend comment on the
  day reads `value=0 (previous value=0, unchanged)`. The fixture test that wanted the repeat to
  carry a different value now asserts what Grafana does instead.

The fallback still works with the reconciled fixtures: `DEMO_END_TO_END=1
DEMO_RECEIVER_URL=http://localhost:8080 python3 -m pytest tests/test_end_to_end.py` passed in
101s against the container after the rehearsal, driving OPS-12 from created to Completed and
closing it on the way out.

**Deviations from the handoff, both deliberate:**

- The rolldice image is based on `python:3.13-slim`, not the example's `python:alpine3.19`. Docker
  Hub pulls on this laptop take minutes (a compose build sat on the alpine image's metadata for ten
  minutes before it was killed), and the slim image was already present. Every dependency has a
  wheel for it, so nothing compiles.
- The three example files are copied into `docker/rolldice/` rather than built from the other
  repo's directory. Story 53 keeps that repo read-only and this one self-contained.

**Policy timings.** `group_wait: 10s`, `group_interval: 10s`, `repeat_interval: 1m`. The group
interval matters as much as the repeat: a Resolved is only sent on a group-interval tick, which
is why the Resolved followed the traffic restart by 16s rather than by the five-minute default.
No-data and query errors are `OK` on the rule, because a rolldice that has not yet served a
request has no series at all, and a DatasourceNoData Notification would start a Run and open an
Incident about nothing.

### For ticket 08

- **`Dashboard:` and `Panel:` in the Incident description are empty.** The rule is linked to no
  dashboard, so Grafana sends both URLs as empty strings and the skill renders them as empty
  bullets. Either provision a small rolldice dashboard and set `dashboardUid`/`panelId` on the
  rule, or accept it; neither is a ticket 07 concern and the skill is not weakened here.
- **Still no `[DENIED]` line.** The three Runs produced none, as ticket 06 predicted.
- **Pre-demo check:** `DEMO_CONTAINER=1 python3 -m pytest tests/test_grafana.py` is the fast
  version of "rule Normal, traffic flowing, contact point aimed at the Receiver".
- **A change to any provisioning file is `docker compose restart lgtm`;** Grafana's reload
  endpoint needs a server admin, which anonymous Admin is not.

## What the review changed

The spec review caught that the rule as first written did not mean "zero for thirty seconds".
Its query was `rate(...[30s])`, and a rate over a thirty-second window only reads zero once the
whole window is past the last request, so the thirty-second pending period started about thirty
seconds late. The first rehearsal showed it: `startsAt` 71s after the stop, the Firing
Notification at 81s. The window is now `[20s]` — four of rolldice's five-second exports, the
shortest that cannot land on a single sample and lose the rate — and the second rehearsal
measured `startsAt` at 60s and the Notification at 70s. The first rehearsal's numbers were: fire
81s, first repeat 69s later, Resolved 16s after the restart, 3m53s end to end; the fixtures are
that rehearsal's Notifications, and nothing in their shape changed.

The same review noted that the end-to-end check's "no open Match first" precondition is
satisfied by a live Firing that has not yet opened its Incident, a window of about ninety
seconds. That stays as documentation rather than a check in the test, because the test also
runs against a laptop process with no Grafana at all.

The standards review found no documented-standard violations and one duplication: the repo
root, the `DEMO_CONTAINER` opt-in and the `docker compose` subprocess call had been written into
both `tests/test_container.py` and `tests/test_grafana.py`. They live in `tests/conftest.py` now.
