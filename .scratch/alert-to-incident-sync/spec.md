# Spec: Grafana Alert to OPS Incident Sync

Status: ready-for-agent
Created: 2026-09-14
Demo date: 2026-09-15, late afternoon

## Problem Statement

When a Grafana alert fires, someone on the ops team has to notice it, decide whether an incident already exists, open or update one in Jira by hand, and remember to resolve it when the alert clears. In a demo setting we want to show peer engineers that an AI agent can do that loop end to end, while being visibly unable to do anything else, and while never holding the Jira credential it is acting with. Today nothing exists: no receiver, no container, no alert rule, no agent prompt.

## Solution

One `docker compose up` starts a local Grafana LGTM stack and one demo container. Grafana sends Notifications to the Receiver in the container. For each Notification the Receiver starts exactly one Run, a headless Claude invocation that can only execute jira-as and read files. The Run finds the Match for each Alert by its Fingerprint label, creates an Incident in OPS if there is none, comments and advances the Incident on repeat Firings, and comments and Completes it on Resolved. All Jira traffic from the Run goes through the Forwarder, which holds the real token; the Run only ever sees a sentinel. The audience watches Grafana, the container log rendered by the log formatter, and the OPS Incidents queue on one screen.

## User Stories

### Presenter and audience

1. As a presenter, I want the whole demo to start with a single compose command, so that setup does not eat into the session.
2. As a presenter, I want a deterministic way to make the Alert fire and resolve, so that the demo does not depend on luck.
3. As a presenter, I want the Alert to fire, repeat and resolve within about five minutes, so that the full lifecycle fits the slot.
4. As a presenter, I want a canned Notification sequence I can replay with a script, so that a broken Grafana does not sink the demo.
5. As a presenter, I want the container log to show each Run's reasoning, every jira-as command, and every denied tool call on its own line, so that the audience can follow what the agent is doing.
6. As an audience member, I want to see the Incident appear in the OPS Incidents queue moments after the Alert fires, so that I believe the loop is real.
7. As an audience member, I want to see that the Run cannot execute anything except jira-as, so that I trust the boundary.
8. As an audience member, I want to see that the Run's environment holds a sentinel and not the Jira token, so that I trust the credential story.
9. As an audience member, I want the presenter to state plainly which credential is not masked, so that the story is honest.
10. As a presenter, I want the purpose-built skill the Run follows to be a short readable file, so that I can show it on screen.

### Receiver

11. As Grafana, I want an HTTP endpoint that accepts my webhook contact point format, so that I can deliver Notifications without adapter code.
12. As the Receiver, I want to reject a body that is not a Grafana Notification with a client error, so that junk does not start Runs.
13. As the Receiver, I want to acknowledge a valid Notification immediately and start the Run afterwards, so that Grafana does not time out or retry.
14. As the Receiver, I want to start exactly one Run per Notification, so that a Notification carrying several Alerts is handled in one place.
15. As the Receiver, I want Runs to execute one at a time in arrival order, so that two Firings of the same Alert can never race to create duplicate Incidents.
16. As the Receiver, I want a health endpoint, so that compose and the presenter can tell it is up.
17. As the Receiver, I want to write the Notification to a per-Run file the Run reads, so that the prompt stays short and the raw payload is inspectable.
18. As the Receiver, I want to log the start, end, exit status and duration of each Run, so that the audience log has structure.
19. As the Receiver, I want a Run that fails or times out to be logged and not to block later Runs, so that one bad Run does not stall the demo.

### Run

20. As a Run, I want the Notification available as a file, so that I can read every Alert's status, labels, annotations, value and Fingerprint.
21. As a Run, I want to handle each Alert in the Notification independently, so that mixed Firing and Resolved Alerts are handled correctly.
22. As a Run, I want to find the Match by searching OPS for an open Incident with the Fingerprint label, so that matching is a lookup and not a guess.
23. As a Run, I want to create an Open Incident when a Firing Alert has no Match, so that the first Firing is captured.
24. As a Run, I want the created Incident to carry the Fingerprint label, so that later Runs and chapter two can find it.
25. As a Run, I want the created Incident to carry Summary, Description, Source, Severity, Urgency and Component from the Alert, so that the Incident is useful without a human editing it.
26. As a Run, I want the Description to include the alert annotations and the generator, dashboard and panel links, so that a responder can jump to Grafana.
27. As a Run, I want to leave Component empty when the Alert's service label matches no seeded component, so that an unknown service does not fail the create.
28. As a Run, I want never to set Sev-0 or Major incident, so that automation cannot page the whole company.
29. As a Run, I want to add a comment on each repeat Firing that states the current value, the change since the previous comment, and time since the Incident opened, so that the Incident shows a trend.
30. As a Run, I want to move an Open Incident to Work in progress on its first repeat Firing, so that the status reflects that the condition is persisting.
31. As a Run, I want to leave a Work in progress Incident in that status on further repeats, so that repeats are idempotent apart from the comment.
32. As a Run, I want to add a closing comment and move the Incident to Completed when its Alert is Resolved, so that the Incident closes itself.
33. As a Run, I want the closing comment to state total duration and number of Firings, so that the record is complete.
34. As a Run, I want a Resolved Alert with no Match to be logged and skipped, so that a stray resolve does not create an Incident.
35. As a Run, I want a Firing Alert whose only prior Incident is Completed to get a new Incident, so that each occurrence is its own record for chapter two.
36. As a Run, I want the transitions I need identified by name rather than hardcoded ids, so that I can read them from the issue and not fail on an id change.
37. As a Run, I want to finish with a one-line summary of what changed for each Alert, so that the log and the audience get a clean ending.

### Permission boundary

38. As an operator, I want the Run started in a mode where any tool call not on the allow list is denied without prompting, so that a headless Run can never hang and never escape.
39. As an operator, I want the allow list to contain only jira-as execution and file reading, so that the Run has no other capability.
40. As an operator, I want denials to show in the log formatter output, so that a misbehaving prompt is visible rather than silent.

### Credential boundary

41. As an operator, I want the real Jira token to exist only in the Receiver's process and the Forwarder, so that the model's environment never contains it.
42. As an operator, I want each Run's environment to point jira-as at the Forwarder with a per-Run sentinel token, so that the sentinel is useless outside that Run.
43. As an operator, I want the Forwarder to reject a request whose sentinel does not match the current Run, so that a stale or guessed sentinel gets nothing.
44. As an operator, I want the Forwarder to forward only to the configured Atlassian site, so that it cannot be used as an open proxy.
45. As an operator, I want the Forwarder to replace the basic-auth header and pass everything else through unchanged, so that jira-as works unmodified.
46. As an operator, I want the Forwarder never to log the real token or the Authorization header, so that the log window is safe to show.
47. As an operator, I want the Receiver to fail fast at startup if the Jira credentials or the Anthropic token are missing, so that a misconfigured container does not silently no-op during the demo.

### Container and compose

48. As an operator, I want the demo container image to include Claude Code, jira-as, and the purpose-built skill, so that a Run needs nothing from the host.
49. As an operator, I want no Docker socket mounted anywhere, so that there is nothing to explain away.
50. As an operator, I want secrets passed to the container by env file, not baked into the image or committed to the repo, so that the image is safe to share.
51. As an operator, I want the container to run as a non-root user, so that the permission-mode flag works and the story is tidy.
52. As an operator, I want compose to run the LGTM stack and the demo container on one network, so that the contact point can name the demo service.
53. As an operator, I want Grafana's contact point, notification policy and alert rule provisioned from files in this repo, so that the other repo is not edited.
54. As an operator, I want the notification policy's repeat interval set to one minute and the rule's evaluation to ten seconds, so that repeats and resolution happen on demo timescales.
55. As an operator, I want a synthetic traffic source whose absence fires the Alert, so that stopping and starting one process drives the lifecycle.

### Chapter hooks

56. As a future developer, I want every Incident to carry its Fingerprint label from day one, so that grouping under a Problem is a lookup.
57. As a future developer, I want Completed rather than Closed to be the automated terminal status, so that a post-incident review has a clean trigger on close.

## Implementation Decisions

### Process layout

- One container. The Receiver is the container's main process. Each Run is a child process of the Receiver. Runs are serialized through an in-memory FIFO with a single worker. See ADR 0001.
- The Forwarder is a thread inside the Receiver process listening on the container loopback interface, so the token never leaves one process.
- Compose in this repo defines two services: the LGTM stack from the published otel-lgtm image, and the demo container built from a Dockerfile in this repo. Both share one network. The Grafana contact point URL names the demo service.

### Receiver

- Python standard library only: the HTTP server module for the endpoint, threading for the queue worker and the Forwarder, subprocess for Runs. No third-party dependency at runtime.
- Endpoints: one POST for Notifications and one GET for health.
- Validation: the body must parse as JSON and contain a top-level alerts array where every element has a fingerprint and a status. Anything else gets a 400. Valid bodies get a 202 before the Run starts.
- Per Run the Receiver creates a working directory containing the Notification as a JSON file and starts the Run with the working directory as its cwd.
- The Run spawner is a callable injected into the Receiver at construction, so tests substitute a fake that records invocations.
- The Run command is the Claude CLI in print mode with: permission mode dontAsk; allowed tools limited to jira-as execution and reading; output format stream-json with verbose; a system prompt appendix that names the Notification file and the purpose-built skill; the mounted skill directory. A per-Run timeout of a few minutes kills a stuck Run and logs it.
- The Run's environment is constructed from scratch, not inherited: the Anthropic OAuth token, the Jira email, a Jira site URL pointing at the Forwarder over plain http, a Jira token equal to the Run's sentinel, and PATH. Nothing else.
- Sentinel: a random token generated per Run and registered with the Forwarder before the Run starts, unregistered when it ends.

### Forwarder

- Accepts any HTTP method and path, checks the incoming basic-auth password equals the active sentinel, replaces the Authorization header with the real email and token, and forwards to the configured Atlassian site over https. Response status, headers and body pass back unchanged apart from hop-by-hop headers.
- A request with a missing or non-matching sentinel gets a 401 and is logged without the credential.
- Bound to loopback only. The upstream host is fixed from configuration, never from the request.
- The real Jira token and the Authorization header are never written to any log line. See ADR 0002.

### Log formatter

- A pure function from one stream-json event to zero or more human lines. Renders assistant text, each tool call with its command, each tool result trimmed to a few lines, permission-denied events prominently, and the final result with cost and duration. The Receiver pipes the Run's stdout through it into the container log.

### The Run's skill

- One skill file in this repo, mounted into the container, that describes the five operations in terms of jira-as invocations and the OPS facts: project key, issue type, the Fingerprint label format `fp-<fingerprint>`, the match JQL, the field mapping, the status names, and the rule for reading transition ids from the issue.
- Field mapping: Summary is alert name plus instance label; Description is annotations plus generator, dashboard and panel URLs; Source is Monitoring systems; Severity maps critical to Sev-1, warning to Sev-2, anything else to Sev-3; Urgency follows Severity as Critical, High, Medium; Component is the service label when it equals a seeded component name, else empty. Sev-0 and Major incident are never set.
- Lifecycle: create in Open; first repeat moves to Work in progress and comments; further repeats only comment; Resolved comments and moves to Completed. Pending, Closed and Canceled are never used by automation.
- Match JQL: project OPS, issue type Incident, label equals the Fingerprint label, status category not Done. See ADR 0004.
- Body for create and edit goes through jira-as's body-from-file mechanism; the Run writes those JSON files in its working directory.

### Grafana provisioning

- Files in this repo mounted into the LGTM container's provisioning alerting directory: a webhook contact point pointing at the Receiver, a notification policy with a one-minute repeat interval and short group wait, and one alert rule evaluated every ten seconds.
- The rule: request rate for the rolldice service is zero for thirty seconds. The synthetic source is the rolldice example app plus its traffic script, run as a compose service that the presenter stops to fire and starts to resolve. Rule labels carry severity and service so the field mapping has inputs.
- A canned Notification sequence, firing then repeat then resolved, is committed as JSON fixtures. A small script posts them in order with a pause, used both as the demo fallback and by the end-to-end check.

### Container image

- Built from the existing claude-devcontainer image, with jira-as pip-installed, bubblewrap deliberately not required, and the skill copied in. Runs as the existing non-root user. Onboarding pre-accepted the way the existing entrypoints do it.
- Secrets arrive by an env file referenced from compose and ignored by git. A committed example file lists the variable names with placeholder values.

### Project settings

- The repo's Claude settings allow the OPS project and site operations for jira-as, already in place. The Run's permission rules are passed on the command line, not from repo settings, because dontAsk and allow rules are honored there regardless of settings-file scope.

## Testing Decisions

- A good test drives a seam from the outside and asserts observable behaviour: an HTTP response, a recorded spawn invocation, a forwarded request as seen by a fake upstream, formatted text lines. No test inspects internal state or patches private functions.
- Framework: pytest. Tests start real local HTTP servers on ephemeral ports for the Receiver and the Forwarder; no mocking of the HTTP layer.
- Receiver tests: valid Notification gets 202 and one spawn call with the Notification file present; invalid bodies get 400 and no spawn; two Notifications posted back to back produce two spawns in order and the second does not start until the first's fake completes; health returns 200; a spawn that raises is logged and the next Notification still spawns.
- Forwarder tests, against a fake upstream server: correct sentinel yields a forwarded request carrying the real credential and none of the sentinel; wrong or missing sentinel yields 401 and no upstream call; upstream status and body pass back; log output contains neither the real token nor an Authorization header.
- Formatter tests: table-driven over recorded stream-json events, including a permission-denied event and a final result event.
- End-to-end check, opt-in by an environment flag: posts the canned sequence to a running container and asserts by jira-as JQL that one Incident exists with the Fingerprint label, has at least two comments, and ends in Completed. Cleans up by transitioning the Incident to Canceled. Not part of the default run.
- Prior art: none in this repo. The as-demo repo's skill tests are subprocess-driven and not reused.

## Out of Scope

- Chapter two, grouping repeated Incidents under a Problem with the is-caused-by link. Only the Fingerprint label hook is built.
- Chapter three, drafting a post-incident review on close.
- Claude Code native sandbox credential masking. Stretch goal, mentioned in the demo as the built-in equivalent.
- An iptables egress allowlist inside the container.
- Any servicedeskapi call, request type assignment, or customer-portal behaviour.
- Reopening a Completed Incident on a re-fire, fuzzy matching, or any match window.
- Parallel Runs, persistence of the queue across restarts, retries of failed Runs.
- Authentication on the Receiver endpoint. It is reachable only on the compose network.
- Grafana authentication. The LGTM image runs anonymous admin, which is acceptable on a laptop.

## Further Notes

- Grafana's repeat interval defaults to four hours. Without the one-minute policy in this repo, repeat Firings never happen during a demo. This is the most likely thing to be lost if someone reuses the stack from the other repo.
- The Incidents queue filters on unresolved resolution and issue type. Completed must set a resolution or the Incident stays in the queue. Confirm against a real issue's transitions during implementation, and if the transition does not set one, set resolution in the transition body.
- jira-as sends basic auth through the requests library and mounts both http and https adapters, so the plain-http Forwarder URL works without patching.
- In print mode with dontAsk, denials are reported as permission-denied events in the stream and in the result's denial list. That is the audience-visible proof for story 7.
- The Anthropic OAuth token cannot be masked by any documented mechanism. Say it out loud.
- The as-demo entrypoint ignores its command argument. The demo container in this repo has its own entrypoint and does not reuse that one.
- Domain vocabulary is in CONTEXT.md; decisions in docs/adr. Use those terms in ticket titles and test names.
