# 04 — The tree is ready for a stranger to clone

**What to build:** Nothing personal, local or unlicensed remains in the working tree. The recorded Transcript fixture no longer carries the account email, account id or the recording machine's path, and a default-run test greps every committed fixture for an `@` outside `example.invalid`. The runbook's queue URL is a placeholder. The spec and tickets under `.scratch/` stay, scrubbed of the site name, the account email and the audience company. The session handoff note is removed and the one fact only it held, the working project template key, moves into ADR 0004. An MIT `LICENSE` sits at the root; the three copied rolldice files carry their Apache-2.0 attribution in a header and a NOTICE line. The README opens with what this is, what a stranger needs, and that the OPS field ids in the Skill are one site's.

**Blocked by:** 02 — A corporate CA is trusted through the build and every Run; 03 — The demo container runs the way Anthropic's deployment guide describes

**Status:** done

- [x] The recorded Transcript fixture carries `example.invalid` in place of the account email, a fake account id, and a container-style run path; the formatter tests still pass, and a new default-run test fails on any committed fixture carrying an `@` outside `example.invalid`
- [x] No tracked file under docs, the runbook, or `.scratch/` names the Atlassian site, the account email or the audience company; the runbook's queue URL is a placeholder that says where the queue id comes from
- [x] The session handoff note is gone and ADR 0004 carries the project template key it alone held
- [x] `LICENSE` is MIT at the root; the rolldice Dockerfile and app carry an Apache-2.0 attribution header naming the source repository, and a NOTICE line exists
- [x] The README's first paragraph says what this is; a prerequisites list names Docker, a Jira Cloud site with an ITSM project, a Claude Code OAuth token and `jira-as` in the shell; and it says the OPS field ids in the Skill must be re-read from the reader's own project
- [x] The full default suite passes

## Comments

Done. The tree carries nothing that names the author, the account, the site, the audience
company or the laptop the demo was built on, and a stranger's first screen of the README says
what this is, what they need and which numbers in the Skill are not theirs.

- **The recorded Transcript.** `fixtures/run-transcript-repeat-firing.jsonl` was recorded on
  the laptop, not in the container, and carried far more than the audit's one line: the account
  email eight times, the account id sixteen (plain and URL-encoded, in the `jira-as issue get`
  result and the avatar URLs), the account's display name twelve times (in JSON and in two
  `jira-as` tables), the real site name ninety-two times, the scratchpad working directory in
  the init Run event and in the `Read` of `notification.json`, the repo's laptop path in the `Read`
  of the Skill, and an init Run event listing the laptop's plugins with their `/Users/...` paths,
  its memory directory, its claude.ai connectors, and its 134 skills and 179 slash commands by
  name. Now: `ops@example.invalid`, and its Gravatar hash where the real address's was; the
  account id with Atlassian's namespace prefix kept and the rest zeroed; `Example Admin`
  (thirteen characters, so the tables still line up); `example.atlassian.net` as the tests use;
  `/app/runs/<run-id>`
  with a run id the Receiver would mint at the Run's real time, `/app/skill/...`, and an init
  Run event with no plugins, no connectors, no user skills and a home under `/home/demo`; its
  tool and agent lists are the recording build's own and stay. Every Run event that is the Run's
  own — its text, its `jira-as` commands, their results — is untouched. The other Transcript
  lost only its connector list. The formatter renders both with no diagnostic line, as before.
- **The new default-run check**, `tests/test_fixtures.py`, reads every file `git ls-files`
  reports under `fixtures/` and fails on an `@` not followed by `example.invalid`, on a Gravatar
  hash that is not the placeholder address's, and on a path under `/Users/`, `/private/` or a
  `/home/` that is not the container's. Before the scrub it failed on the one fixture, naming the
  email and the plugin sources; after it, all fifteen pass. In a tree unpacked from an archive,
  with no git to ask, it reads every file under `fixtures/` instead.
- **The rest of the scrub.** The runbook's queue URL is `https://<your-site>.atlassian.net/...
  /queues/custom/<queue-id>` with a paragraph on where both come from. Under `.scratch/`: the
  site name out of two tickets, the account email out of one ticket and the publishing audit,
  the audience company out of this feature's spec (four places), and a private earlier demo
  repo's name out of the first spec, one ticket and the audit; ADR 0001 named that repo too and
  no longer does. `HANDOFF.md` is removed; the template key
  `com.atlassian.servicedesk:itil-v2-service-desk-project` and the enum key that does not work
  are a consequence in ADR 0004, and `CLAUDE.md` points at the README, the Skill and that ADR
  instead of the handoff.
- **License and attribution.** `LICENSE` is MIT. `NOTICE` names `grafana/docker-otel-lgtm`
  and Apache-2.0 for the three files under `docker/rolldice/`, and each carries the header:
  `app.py` and `requirements.txt` unchanged but for it, the Dockerfile with the Apache-required
  note that it was modified and how. The Dockerfile's comment also stopped naming a path on the
  laptop. `pyproject.toml` declares the license.
- **The README** opens with what this is in one paragraph, then "What you need": Docker with a
  Compose new enough for the limits, a Jira Cloud site with an ITSM project, a Claude Code OAuth
  token from `claude setup-token`, and `jira-as` 2.x in the shell; then the field-id warning
  with the command that lists a site's fields. `jira-as -o json api call getFields` was run from
  this repo root before it was written down: 152 fields, Severity, Urgency, Source and Major
  incident among them under this site's ids. A "License" section closes the file, and the
  provisioning section no longer refers to "the other repo".

The suite is 241 passed, 36 skipped (fifteen new); ruff is clean; mypy's two findings are the
pre-existing ones. Nothing here touched the image or the compose file.

Judgement calls beyond the ticket's list, all in the direction of less: the site name and the
display name in the fixture (the ticket names the email and the account id; the site appeared
ninety-two times and the name is the same account); the init event's inventory, because the
`@` test the ticket asks for cannot pass with `plugin@marketplace` sources in it and a
container Run has none; the private repo name in ADR 0001. Kept: `Zscaler`, a product and not
the company; the rehearsal's "this laptop" and "this machine", which are the author's own
measurements and say so; the git author identity, per the audit.

Not done here, by design: ticket 05, creating the repository, pushing and verifying from a
fresh clone.

## What the review changed

The standards review caught one vocabulary breach, "agent" twice in the README's opening where
CONTEXT.md says Run, and two claims the files did not bear out: the README said an older Compose
skips "two" limits when the runbook has them at different versions (`pids_limit` from 2.2,
`cpus` from 2.17), and this ticket said the fixture's init Run event was reduced to what the
container has when its tool and agent lists are the recording build's. All three are fixed above.
Its judgement calls taken: the parametrize decorators share one mark, `every_committed_fixture`;
`foreign_addresses` is `addresses_off_the_placeholder_domain`; CLAUDE.md's opening line uses the
glossary's words; "init event" is "init Run event" here. Declined: the PEP 639 string form for
the license field, since nothing installs this package and the table form works on every
setuptools.

The spec review found the one real gap: the account email survived as its Gravatar hash, the MD5
of the address, thirty-two times in the avatar URLs, where no `@` grep can see it. The hash is now
the placeholder address's, and a third check holds every Gravatar hash in a fixture to that one.
It judged each departure from the ticket's list justified. It also noted that "the other repo"
was left dangling in a provisioning comment and a test docstring once the README stopped
explaining it (both now name `grafana/docker-otel-lgtm`), that the committed-fixtures enumeration
would error a tree unpacked without git (it falls back to every file under `fixtures/`), and that
"all-zero account id" was loose (the namespace prefix stays, and the wording above says so).
Observed and left: the rolldice headers point at the Apache License by URL rather than shipping
its text, which is what the ticket asked for. One more thing while the tree was open: `.DS_Store`
is ignored, since one was sitting untracked at the root.
