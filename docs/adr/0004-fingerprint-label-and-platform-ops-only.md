# Incidents are keyed by a Fingerprint label and managed with platform operations only

Matching an Alert to an Incident is exact: the open Incident carrying the label `fp-<fingerprint>`, found with `project = OPS AND issuetype = Incident AND labels = fp-<fingerprint> AND statusCategory != Done`. Fuzzy matching on alert name and labels was rejected because Grafana already provides a stable identity, and a resolved-then-refired Alert deliberately gets a new Incident so that chapter two's Problem grouping has something to group. Although OPS is a JSM project, the Run uses only platform operations (search, create, edit, comment, transition), because they are project-keyed and the Incidents queue filters on issue type alone. No servicedeskapi call is needed.

## Consequences

- Chapter two is a label lookup plus one link of type 10006, not a new matching design.
- Completed must set a resolution, or the Incident stays in the unresolved queues. Verify against a real issue's transitions before relying on it.
