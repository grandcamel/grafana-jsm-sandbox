# 02 — Log formatter renders stream-json into audience lines

**What to build:** The audience log window shows what a Run is doing one line at a time: assistant text, each tool call with its command, trimmed tool results, permission-denied events called out prominently, and a final result line with cost and duration. Built as a pure function over one stream-json event, plus a command-line entry that formats a saved transcript so it can be checked by eye before any real Run exists.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] A pure function maps one stream-json event to zero or more text lines
- [ ] Table-driven tests cover assistant text, a Bash tool call, a tool result longer than the trim limit, a permission-denied system event, and a final result event
- [ ] Permission-denied lines are unmistakable in a terminal (prefix or marker), since they are the audience-visible proof that the Run cannot escape
- [ ] Malformed or unknown event types produce no crash and at most one diagnostic line
- [ ] A recorded fixture transcript is committed and the command-line entry renders it end to end
- [ ] Nothing in the output ever includes an Authorization header or a token-shaped value from tool input
