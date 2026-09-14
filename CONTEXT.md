# Grafana to OPS Incident Sync

A demo in which a Grafana alert notification triggers a headless Claude run inside a container, and that run creates, updates and resolves Incidents in the Jira OPS project.

## Language

### Alerting side

**Alert**:
One Grafana alert rule instance, identified by its Fingerprint. It is either Firing or Resolved.
_Avoid_: alarm, event, rule

**Fingerprint**:
Grafana's stable hash of an Alert's label set. The identity of an Alert across every Notification.
_Avoid_: alert id, hash, key

**Notification**:
One webhook POST from Grafana, carrying one or more Alerts.
_Avoid_: webhook, payload, message, event

**Firing**:
The Alert state meaning the condition currently holds. A Notification may report the same Firing Alert repeatedly.
_Avoid_: active, triggered, alerting

**Resolved**:
The Alert state meaning the condition no longer holds.
_Avoid_: cleared, ok, recovered

### Sync side

**Receiver**:
The HTTP endpoint inside the container that accepts Notifications and starts Runs, one at a time.
_Avoid_: harness, server, listener, webhook handler

**Run**:
One headless Claude invocation, started by the Receiver for exactly one Notification.
_Avoid_: harness, agent, session, job

**Forwarder**:
The localhost process, owned by the Receiver, that holds the real Jira credential and forwards a Run's Jira requests with that credential attached. A Run only ever holds a sentinel.
_Avoid_: proxy, sidecar, hand, vault

**Sentinel**:
The random token generated for one Run and registered with the Forwarder for that Run's lifetime. It stands where the Jira API token would be in a Run's environment, and is worth nothing anywhere else or once the Run has ended.
_Avoid_: fake token, dummy credential, placeholder, api key

**Transcript**:
The stream-json output of one Run, one Run event per line. The Receiver renders it into the container log as it arrives, and a recorded Transcript is committed as a fixture.
_Avoid_: log, output, stream, session log

**Run event**:
One line of a Transcript: one thing the Run did — assistant text, a tool call, a tool result, a denial, or the final result. Never shortened to "event" on its own, because an Alert and a Notification are not events here either.
_Avoid_: event, message, chunk

### Jira side

**Incident**:
An OPS issue of type Incident that represents one Alert's lifetime, from first Firing to Resolved.
_Avoid_: ticket, issue, case, request

**Match**:
The open Incident that carries an Alert's Fingerprint label. An Alert has at most one Match.
_Avoid_: duplicate, existing incident, correlation

**Problem**:
An OPS issue of type Problem that groups repeated Incidents sharing a Fingerprint. Chapter two; not built on day one.
_Avoid_: parent, root cause ticket
