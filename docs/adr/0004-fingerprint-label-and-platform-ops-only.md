# Incidents are keyed by a Fingerprint label and managed with platform operations only

Matching an Alert to an Incident is exact: the open Incident carrying the label `fp-<fingerprint>`, found with `project = OPS AND issuetype = Incident AND labels = fp-<fingerprint> AND statusCategory != Done`. Fuzzy matching on alert name and labels was rejected because Grafana already provides a stable identity, and a resolved-then-refired Alert deliberately gets a new Incident so that chapter two's Problem grouping has something to group. Although OPS is a JSM project, the Run uses only platform operations (search, create, edit, comment, transition), because they are project-keyed and the Incidents queue filters on issue type alone. No servicedeskapi call is needed.

## Consequences

- Chapter two is a label lookup plus one link of type 10006, not a new matching design.
- Completed must set a resolution, or the Incident stays in the unresolved queues. Verified against real OPS issues in ticket 04: the `Resolve` transition leaves `resolution` null on its own, and `jira-as lifecycle transition <key> --id <id> --resolution Done` sets it. It is the only transition on this workflow that accepts one — `Cancel` and `Close` have it rejected by their screens, `editIssue` cannot set it, and `Canceled` has no way out but `Close`. So an Incident parked in `Canceled` sits in the Incidents queue for good, and `Resolve` with a resolution is the only clean exit, for automation and for cleaning up after a rehearsal alike.
