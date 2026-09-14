# 02 — Log formatter renders stream-json into audience lines

**What to build:** The audience log window shows what a Run is doing one line at a time: assistant text, each tool call with its command, trimmed tool results, permission-denied events called out prominently, and a final result line with cost and duration. Built as a pure function over one stream-json event, plus a command-line entry that formats a saved transcript so it can be checked by eye before any real Run exists.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [x] A pure function maps one stream-json event to zero or more text lines
- [x] Table-driven tests cover assistant text, a Bash tool call, a tool result longer than the trim limit, a permission-denied system event, and a final result event
- [x] Permission-denied lines are unmistakable in a terminal (prefix or marker), since they are the audience-visible proof that the Run cannot escape
- [x] Malformed or unknown event types produce no crash and at most one diagnostic line
- [x] A recorded fixture transcript is committed and the command-line entry renders it end to end
- [x] Nothing in the output ever includes an Authorization header or a token-shaped value from tool input

## Comments

**2026-09-14 — implemented.** Every acceptance criterion is covered by a test in
`tests/test_log_formatter.py`; 79 tests pass from a clean checkout with `python3 -m pytest`.

- `grafana_jsm_sandbox/log_formatter.py` — `format_event` (the pure function), `format_stream`,
  `redact`, and the `python3 -m grafana_jsm_sandbox.log_formatter [transcript.jsonl]` entry that
  reads a file or stdin.
- `fixtures/run-transcript.jsonl` — the recorded Transcript, and what the command-line entry
  renders end to end. The README shows its output verbatim.

**The fixture is a real recording, with two edits.** It came from actually running
`claude -p --permission-mode dontAsk --allowedTools "Bash(seq *)" "Read" --output-format
stream-json --verbose` over a prompt that runs one allowed command and one that is not, so the
`system/permission_denied` event, its `decision_reason_type`, the `tool_result_meta`
`non_execution_kind`, and the result's `permission_denials` list are all shapes the CLI really
emits rather than shapes we guessed. Two edits: the init event's inventory was reduced to what a
container Run carries (the recording listed this laptop's whole tool, skill and plugin set,
including Gmail and Drive tools that have no business in a Jira demo), and `rate_limit_event`
events were dropped because they carry account utilisation figures. Every other event is
byte-for-byte as recorded.

**The redaction was broken and the tests were hiding it.** The credential table originally used an
`ATATT`-prefixed sentinel, so the prefix rule rescued every case no matter what the rule under
test did. A per-Run sentinel has no prefix (spec: "a random token generated per Run"), and with a
prefix-free one, four realistic commands leaked in full: `--token "..."` quoted, `curl -u
user:token`, an unquoted `--token` (the flag pattern required a letter before the keyword, so
`--token` itself never matched), and `Authorization: SSWS <token>`, where an unrecognised scheme
made the rule redact the scheme and print the secret next to it. All eight rules were then checked
by disabling each one in turn and confirming a test fails — the same check found that a broad
catch-all was masking the narrow rules, and that one rule had no test at all until one was added.

Three deliberate choices beyond the checklist:

- A `[run]` line renders the init event with the model, the permission mode and the allowed tools.
  The spec's formatter list does not ask for it, but it is the line that shows an audience the Run
  started with `dontAsk` and two tools (stories 7 and 38), so it earns its place.
- A tool call's command is never truncated, while tool results are trimmed to five lines and 200
  characters. Story 5 wants every jira-as command in the log, and a command cut off halfway is the
  line that invites the question of what the rest of it said.
- The `tool_result` of a denied call is dropped, because it is the denial paragraph handed back to
  the model. The `[DENIED]` line above it and the result's denial recap below both still report
  the denial, so it cannot go silent, and the line the audience should notice is not buried under
  a repeated paragraph.

Known and deliberate: redaction does not fire on the bare word "token", because "the token is a
sentinel" is a sentence the demo wants the audience to read. It fires on credential flags,
assignments, Authorization headers of any scheme, `curl -u`, known token prefixes, a credential
word followed by a 16-character-plus opaque value, and any bare 32-character-plus run of letters
and digits. Fingerprints, Incident keys, URLs, UUIDs and timestamps all survive it, which is
tested.

`Transcript` and `Run event` were added to CONTEXT.md. Both are load-bearing now, and "event" is
on the _Avoid_ list for Alert and Notification, so the collision needed saying out loud.

Nothing pipes a live Run through the formatter yet — the Receiver's spawner is still the injected
fake, and wiring the two together is ticket 05.
