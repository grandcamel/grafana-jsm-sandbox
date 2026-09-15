# 04 — The tree is ready for a stranger to clone

**What to build:** Nothing personal, local or unlicensed remains in the working tree. The recorded Transcript fixture no longer carries the account email, account id or the recording machine's path, and a default-run test greps every committed fixture for an `@` outside `example.invalid`. The runbook's queue URL is a placeholder. The spec and tickets under `.scratch/` stay, scrubbed of the site name, the account email and the audience company. The session handoff note is removed and the one fact only it held, the working project template key, moves into ADR 0004. An MIT `LICENSE` sits at the root; the three copied rolldice files carry their Apache-2.0 attribution in a header and a NOTICE line. The README opens with what this is, what a stranger needs, and that the OPS field ids in the Skill are one site's.

**Blocked by:** 02 — A corporate CA is trusted through the build and every Run; 03 — The demo container runs the way Anthropic's deployment guide describes

**Status:** ready-for-agent

- [ ] The recorded Transcript fixture carries `example.invalid` in place of the account email, a fake account id, and a container-style run path; the formatter tests still pass, and a new default-run test fails on any committed fixture carrying an `@` outside `example.invalid`
- [ ] No tracked file under docs, the runbook, or `.scratch/` names the Atlassian site, the account email or the audience company; the runbook's queue URL is a placeholder that says where the queue id comes from
- [ ] The session handoff note is gone and ADR 0004 carries the project template key it alone held
- [ ] `LICENSE` is MIT at the root; the rolldice Dockerfile and app carry an Apache-2.0 attribution header naming the source repository, and a NOTICE line exists
- [ ] The README's first paragraph says what this is; a prerequisites list names Docker, a Jira Cloud site with an ITSM project, a Claude Code OAuth token and `jira-as` in the shell; and it says the OPS field ids in the Skill must be re-read from the reader's own project
- [ ] The full default suite passes
