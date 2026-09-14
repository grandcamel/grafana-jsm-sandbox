# 04 — Run skill drives one Alert through its Incident lifecycle on OPS

**What to build:** Running Claude headless by hand from the laptop, with the purpose-built skill and a canned Notification, produces the right Incident behaviour in OPS: a Firing Alert with no Match creates an Open Incident carrying the Fingerprint label and the field mapping; a repeat Firing comments with the trend and moves it to Work in progress; a Resolved Alert comments and Completes it. The Run is started in dontAsk mode with only jira-as and file reading allowed, and its Jira traffic goes through the Forwarder. This is where the transition names and the resolution behaviour flagged in the spec get verified against a real issue.

**Blocked by:** 03 — Forwarder holds the Jira token

**Status:** ready-for-agent

- [ ] Three canned Notification fixtures exist: firing, repeat firing with a different value, resolved, all sharing one Fingerprint
- [ ] The skill file states the OPS facts, the label format, the match JQL, the field mapping, the lifecycle rule, and the rule to read transition ids by name from the issue, in terms of jira-as invocations only
- [ ] The Run command line uses print mode, dontAsk permission mode, an allow list of jira-as execution and Read, stream-json with verbose, and the skill directory
- [ ] Firing with no Match: an Incident is created in Open with Summary, Description including annotations and links, Source Monitoring systems, Severity and Urgency per mapping, Component from the service label, and label fp-<fingerprint>
- [ ] Repeat Firing: exactly one comment is added stating current value, change since the previous comment, and time since open; status becomes Work in progress; no second Incident is created
- [ ] A further repeat only comments; status stays Work in progress
- [ ] Resolved: one closing comment stating duration and firing count; status becomes Completed; the Incident leaves the Incidents queue (resolution is set, or the ticket records how it must be set)
- [ ] Resolved with no Match: nothing is created; the Run reports it skipped
- [ ] The Run ends with a one-line summary per Alert
- [ ] A recorded stream-json transcript from one real Run is saved as a fixture for ticket 02's formatter
- [ ] Leftover test Incidents are moved to Canceled at the end
