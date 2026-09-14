# Handoff: Grafana alert -> sandboxed Claude harness -> JSM incident demo

Written 2026-09-14 from a session in `~/projects/grand-camel-platform`.
Next session works in **`~/projects/grafana-jsm-sandbox`** (does not exist yet; create it and `git init`).

## Goal

An evolving demo, shown to T-Mobile peer engineers on **2026-09-15, late afternoon**.
A container receives a Grafana alert webhook and spawns a sandboxed Claude harness that:

1. reads the alert webhook content
2. searches the JSM project for an existing matching incident
3. creates a new incident if none matches well enough
4. if one exists, updates it with current status and trend
5. if the webhook clears the alert, comments and resolves the incident

Chapter two (after day one works): repeated incidents with the same alert fingerprint
get grouped under one Problem via the "is caused by" link. Chapter three: draft the
post-incident review from the comment history on resolve.

## Decisions already made

- **Route:** main flow. `/grill-with-docs` -> `/to-spec` -> `/to-tickets` -> `/implement` per ticket.
  No `/wayfinder` (idea fits one session), no `/prototype` (nothing needs a runnable answer).
- **Jira target:** a new project **OPS** "Ops Incidents" was created from the ITSM template
  (option 2 over adding issue types to the old DEMOSD desk). DEMOSD is untouched; ignore it.
- **API surface:** the harness should use *platform* operations on OPS (JQL search, create issue,
  edit, comment, transition). These are project-keyed and work under the project allowlist alone.
  JSM servicedeskapi calls (queues, request types, service desk list) are site-scoped and need
  the site flag (below). Decide in the grill whether the demo needs any of them.
- **Fingerprint:** every incident the harness creates should carry the Grafana alert
  `fingerprint` (a label is the cheapest place) from day one, so step 2 and chapter two are lookups,
  not fuzzy matching.

## OPS project facts (verified live 2026-09-14)

| Item | Value |
|---|---|
| Site | jasonkrue.atlassian.net |
| Project | OPS, id 10775, company-managed, ITIL v2 ITSM template |
| Service desk id | 289 |
| Issue types | Incident 10425, Problem 10432, Change 10428, Service Request 10426, Task 10005 |
| Incident statuses | Open, Work in progress, Pending, Completed, Closed, Canceled |
| Problem statuses | Open, Under investigation, Under review, Pending, Completed, Closed, Canceled |
| Request type for alerts | 1254 "Report a system problem" (maps to Incident) |
| Queues | 605 All open, 608 Incidents, 611 Problem |
| Link type | 10006 Problem/Incident, outward "causes", inward "is caused by" |

Incident custom fields: Severity `customfield_10085` (Sev-0..Sev-3), Urgency `customfield_10079`
(Critical/High/Medium/Low), Impact `customfield_10004`, Source `customfield_10096` (has a
"Monitoring systems" value), Affected services `customfield_10080`, Major incident
`customfield_10083`. Components are seeded with service names (Billing Services, Cloud Storage
Services, Active Directory, ...). Labels and Description are free-form.

Transition ids for Incident were not fetched; read them from a created issue with
`jira-as api call getTransitions --issueIdOrKey OPS-n`.

## jira-as 2.0.0 gotchas (all verified)

- Credentials come from **shell environment variables** (`JIRA_SITE_URL`, `JIRA_EMAIL`,
  `JIRA_API_TOKEN`), not from any `.claude/settings*.json`. A new directory inherits them.
  Never print them; never copy them into the repo. The container will need its own injection
  path (see security research below).
- The `jira-as jsm ...` verb group is **retired stubs** (JAS-49). They print
  `Use api call <operationId>` and exit 2 regardless of flags. The live surface is
  `jira-as api call <operationId>`; `jira-as api describe <operationId>` shows body shape;
  `jira-as api search <word>` finds operations. Body goes in via `--body @file.json`.
- Site-scoped operations (52 of 75 JSM ops, plus `getIssueAllTypes`, `searchProjects`,
  `createProject`, `getIssueLinkTypes`) fail closed with "site access is disabled" unless
  `JIRA_ALLOW_SITE_OPERATIONS=true` or `jira.allow_site_operations: true` in `.claude/settings.json`.
  Recommended settings for the new repo:
  `{ "jira": { "allowed_projects": ["OPS"], "allow_site_operations": true } }`
- `jira-as search jql '<jql>' -o json` works on OPS without the site flag. It has no `--limit`.
- Do not create OPS again: `createProject` with the enum's `simplified-it-service-management`
  key fails "template does not exist"; the working key was
  `com.atlassian.servicedesk:itil-v2-service-desk-project`.

## Reusable assets on this machine

- `~/projects/claude-devcontainer` — hardened docker-run wrapper, egress allowlist, headless
  OAuth onboarding trick for Claude Code in a container.
- `~/projects/as-demo` — Claude Code in a container with the Jira plugin preinstalled, Grafana
  dashboards, a queue-manager "hand" that holds secrets; its Incident Response scenario is close
  to this demo. Layout: `demo-container/`, `queue-manager/`, `observability/`, `docker-compose.yml`.
- `~/projects/docker-otel-lgtm` — local Grafana LGTM stack with alerting, so the webhook can fire
  from the laptop.
- `~/projects/grand-camel-platform/docs/research/containerized-agent-secret-isolation.md` —
  keeping the Jira token out of the model's environment (Claude Code sandbox `mask` +
  `injectHosts`, vault-proxy pattern). This is the part a T-Mobile audience will probe.
- Memory note with the same OPS facts:
  `~/.claude/projects/-Users-jasonkrueger-projects-grand-camel-platform/memory/ops-itsm-demo-project.md`
  (not auto-loaded in the new directory).

## Open questions for the grill

1. Match rule for step 2: fingerprint label equality, or alert name + labels, and over what
   window (open incidents only, or also recently resolved).
2. What "status, trend" means on repeat fires: a comment per firing, an edited field, or both.
   Which statuses the harness moves through (Open -> Work in progress -> Completed?).
3. Sandbox shape: plain docker run from claude-devcontainer, the as-demo compose stack, or the
   Claude Code native sandbox with credential masking.
4. How Claude runs headless in the container: `claude -p` with a prompt file, or the Agent SDK.
   Permission mode for the demo.
5. What the audience sees live: the OPS Incidents queue, the container log, Grafana, or all three.
6. Whether Grafana is the real LGTM stack firing on a synthetic metric, or a curl of a canned
   payload. Real is better for the story; canned is the fallback.
7. Whether any servicedeskapi call is needed at all (queues, request type) or platform ops suffice.

## Suggested skills

- `/setup-matt-pocock-skills` first in the new directory (issue tracker, labels, doc layout).
  Tracker choice: local files under `.scratch/` is fastest for a one-day build; the GC Jira
  project is the alternative.
- `/grill-with-docs` — run it on the goal above; it should leave `CONTEXT.md` and ADRs.
- `/to-spec` then `/to-tickets` in the same context window as the grill.
- `/implement` per ticket, `/clear` between tickets. It drives `/tdd` and closes with `/code-review`.
  Test the webhook receiver and the match logic; fake the Claude spawn first, wire it last.
- `/wizard` for the human-only steps: Grafana contact point pointed at the receiver, and the
  Jira token the container will hold.
- `/handoff` again at end of day rather than `/compact` if the build spills into 2026-09-15.

## Harness note

In this desktop session the auto-mode classifier initially refused env-prefixed
`JIRA_ALLOW_SITE_OPERATIONS=true jira-as ...` commands; the user allowed it afterwards. In the
new repo, put the flag in `.claude/settings.json` so no env prefix is needed.
