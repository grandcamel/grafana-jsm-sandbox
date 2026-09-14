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
