# Spec: Publish this repo publicly on GitHub

Status: wontfix
Created: 2026-09-15

**Folded into `.scratch/hardened-demo-image/spec.md` on 2026-09-15:** its steps are tickets 04 and 05 there, and its four decisions were taken (MIT; `.scratch/` kept and scrubbed; `grandcamel/grafana-jsm-sandbox`; placeholder URL in the runbook). Kept for the audit it records.

## Problem Statement

The demo works and has been shown. The repo has no remote, no license, and a few strings that
were fine on one laptop and are a decision when the whole world can read them. Publishing it as
`grandcamel/grafana-jsm-sandbox` should leave a stranger able to `docker compose up` it against
their own Jira and Grafana, and leave nothing in the tree or the history that the author would
not put on a slide.

## What the audit found (2026-09-15, at commit 7dbd92a)

Nothing blocks publishing outright. No credential, token or sentinel appears in the tree or in
any commit: the grep for Atlassian, Anthropic and GitHub token shapes over `git log -p --all`
finds nothing, `.env` was never committed, and the only file ever touched with "token" in its
name is ADR 0002. What a public reader would see that is personal or local:

| Where | What | Judgement |
| --- | --- | --- |
| Every commit | Author `grandcamel <jasonkrue@gmail.com>` | Already the GitHub identity. Leave it; a history rewrite to hide it is not worth it |
| `fixtures/run-transcript-repeat-firing.jsonl` | A `jira-as issue get` result carrying the Jira account's `emailAddress` and `accountId`, eight times on one line | Scrub to `ops@example.invalid` and a fake account id. The formatter tests read this fixture, so run them after |
| `docs/demo-runbook.md` | The real site URL for the Incidents queue | Presenter-specific. Replace with `https://<your-site>.atlassian.net/...` and say where the queue id comes from |
| `HANDOFF.md` | The site name, the audience company, and paths into three other local repos | A session handoff, not project documentation. Remove it from the public tree; its facts that still matter live in CONTEXT.md, the ADRs and the README |
| `.scratch/` | Spec and eight tickets; the site name in two tickets, the account email in one, the audience company in the spec, the private `as-demo` repo named in two places | Decision below: keep as the build's record with those strings scrubbed, or drop the directory |
| `Dockerfile` | `FROM grandcamel/claude-devcontainer:latest` | Public on Docker Hub and on GitHub, so a stranger's build works. Pin a tag or digest rather than `latest` so the build is reproducible |
| `docker/rolldice/` | Three files copied from `docker-otel-lgtm`'s Python example, Apache-2.0 | Needs attribution: a NOTICE line or a header comment naming the source and its license |
| `fixtures/*.jsonl` | The recording session's scratchpad path under `/private/tmp/.../-Users-jasonkrueger-...` | Cosmetic. Scrub the `cwd` to `/app/runs/<run-id>` while the fixture is open anyway |
| `.claude/settings.json` | `allowed_projects: ["OPS"]`, `allow_site_operations: true` | Fine to publish; it is the project-scoped jira-as configuration the README describes |

The Grafana fixtures carry only `localhost:3000` URLs and the synthetic rolldice labels. The
tests use `example.atlassian.net` and `example.invalid` throughout. The `.gitignore` already
holds `.env` and `runs/`.

## Decisions needed from the author

1. **License.** MIT or Apache-2.0. Apache-2.0 matches the copied rolldice code and carries a
   patent grant; MIT is shorter. Either way the rolldice files keep their Apache-2.0 attribution.
2. **The `.scratch/` record.** Keep the spec and tickets public, scrubbed, as the worked
   example of the skills workflow the README could point at; or remove the directory and keep it
   only in the local clone. `docs/agents/issue-tracker.md` names `.scratch/` as the tracker, so
   removing it means saying so there.
3. **Repository name and description.** `grandcamel/grafana-jsm-sandbox` is free. Description
   suggestion: "A Grafana alert opens, updates and resolves a Jira Service Management Incident
   through a sandboxed headless Claude Code run that holds no Jira credential."
4. **The demo site URL in the runbook.** Placeholder, or keep the real one because the runbook
   is the author's own.

## Solution

One ticket per step, in order, each committed on `main` before the next:

1. **Scrub.** The fixture email, account id and cwd; the runbook URL; the two ticket lines and the
   spec lines per decision 2. Add a test that greps every committed fixture for `@` outside
   `example.invalid`, so the next recorded Transcript cannot reintroduce it.
2. **Remove `HANDOFF.md`** and fold the one fact it alone holds, the working `createProject`
   template key, into ADR 0004 or a note in `CONTEXT.md`.
3. **License and attribution.** `LICENSE` at the root per decision 1; a `NOTICE` or a header in
   `docker/rolldice/Dockerfile` naming `grafana/docker-otel-lgtm` and Apache-2.0.
4. **Pin the base image** to a tag or digest in the `Dockerfile` and note in the README that
   `BASE_IMAGE` is overridable.
5. **README for strangers.** A first paragraph that says what this is in one breath, a
   prerequisites list (Docker, a Jira Cloud site with an ITSM project, a Claude Code OAuth token,
   `jira-as`), and the fact that the OPS field ids in the skill are this site's and must be
   re-read from the reader's own project. Link the runbook.
6. **Create and push.** `gh repo create grandcamel/grafana-jsm-sandbox --public --source . --push`
   with the description from decision 3. Then on GitHub: default branch `main`, Issues on or off
   per decision 2, no Actions yet.
7. **Verify as a stranger.** Fresh clone into a temp directory, `python3 -m pytest` offline,
   `docker compose build` from the pinned base image. Read the rendered README on GitHub once.

## Out of Scope

- CI. The default suite is offline and fast, so a GitHub Actions workflow is cheap, but it is a
  separate ticket after the repo exists.
- A history rewrite. Nothing in the history warrants one.
- Publishing the demo image itself. The Dockerfile builds it; the image holds nothing that needs
  a registry.
- Chapters two and three.

## Further Notes

- `gh` is logged in as `grandcamel` with a fine-grained PAT, so step 6 needs no new auth. Whether
  that PAT has the `administration` scope to create a repository is found out by running it.
- The author email is also the git `user.email` on this machine; a public repo shows it on every
  commit whether or not the fixture is scrubbed. If that is unwanted, GitHub's noreply address
  is the fix for future commits, not a rewrite.
