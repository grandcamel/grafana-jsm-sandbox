# 05 — The public repository exists and builds from a fresh clone

**What to build:** `grandcamel/grafana-jsm-sandbox` exists on GitHub as a public repository with `main` as its default branch, pushed from this tree with a one-sentence description. A fresh clone into a temporary directory passes the offline suite and builds both images from the pinned base without any file from this machine. The rendered README reads correctly on GitHub.

**Blocked by:** 04 — The tree is ready for a stranger to clone

**Status:** done

**Repository:** https://github.com/grandcamel/grafana-jsm-sandbox

- [x] The repository is created public with the description from the spec and `main` pushed; Issues on, no Actions; the URL is recorded in this ticket and in the README
- [x] A fresh clone into a temporary directory passes `python3 -m pytest` with no network beyond PyPI for the dev dependencies
- [x] From the same clone, `docker compose build` succeeds with the placeholder certificate, pulling only the pinned base images
- [x] The README renders on GitHub with its links resolving; any broken link is fixed and re-pushed

## Comments

Done. https://github.com/grandcamel/grafana-jsm-sandbox is public, `main` is its default and
only branch, and a stranger's clone of it passes the suite and builds both images from the
pinned bases with nothing from this machine.

- **Creating it.** `gh repo create grandcamel/grafana-jsm-sandbox --public --source=.
  --remote=origin --push --description "..."`, with the sentence the publishing spec's decision 3
  proposed, verbatim: "A Grafana alert opens, updates and resolves a Jira Service Management
  Incident through a sandboxed headless Claude Code run that holds no Jira credential." The
  fine-grained token in the shell's `GH_TOKEN` was refused `CreateRepository`, as the earlier
  audit said might happen; the keyring login for the same account, an OAuth token with the `repo`
  scope, created it (`env -u GH_TOKEN gh repo create ...`). `origin` is set, `main` tracks
  `origin/main`, and the two heads agreed before this ticket's own commit. Read back from the
  API: visibility `PUBLIC`, default branch `main`, the description above, Issues on, GitHub's
  license detection saying MIT. Actions were switched off with `PUT
  /repos/grandcamel/grafana-jsm-sandbox/actions/permissions {"enabled": false}` and read back as
  `enabled: false`. The wiki is at GitHub's default, on; the ticket did not name it.
- **The README** records the URL as the first two lines of the container section's block, `git
  clone https://github.com/grandcamel/grafana-jsm-sandbox.git` and `cd grafana-jsm-sandbox`,
  ahead of the `cp .env.example .env` that was already there, so the block is a stranger's
  complete first five commands.
- **The fresh clone, twice.** Before the push, a clone of this tree's `HEAD` into the session's
  scratchpad: 78 tracked files, nothing untracked or ignored in it. Under a venv holding only
  `pytest` and `PyYAML` from PyPI, `python -m pytest` is 241 passed, 36 skipped in ten seconds.
  After the push, a clone from GitHub: the same 78 files, the same 241 passed, 36 skipped.
- **The build.** `docker compose build` in the clone with no `.env` stops before building
  anything: compose loads the demo service's `env_file` first and says `open .../.env: no such
  file or directory`. That is the same refusal that keeps `up` from starting a half-configured
  demo, and the README's first step after the clone is `cp .env.example .env`; so, with the
  example copied in, `docker compose build --no-cache` built both images from scratch. Nothing
  was pulled: the log resolves `node:24.21.0-trixie-slim` and `python:3.13-slim` locally in 0.0s
  each, and the only network is npm for Claude Code 2.1.272 (15.5s), PyPI for `jira-as` 2.0.0
  (8.9s) and for the rolldice instrumentation (32.6s). The images are 539 MB and 171 MB, the sizes
  tickets 01 and 03 recorded. The GitHub clone's `docker compose build`, with the same example
  env, then succeeded from the layer cache in seconds.
- **The rendered README.** Every link in it was fetched from GitHub as the page resolves it: the
  eleven relative ones as `blob/main/...` for files and `tree/main/...` for directories (the two
  `.scratch/` directories included), and the one external link to `grafana/docker-otel-lgtm`;
  all `200`. The page itself was read and looked at: the description is the tab title, the MIT
  badge is on the sidebar, the code blocks, tables and the field-id warning render as written.
  Nothing was broken, so nothing was re-pushed for a link.

Judgement calls: the description is the superseded spec's sentence rather than the README's
near-twin of it, because the ticket says "the description from the spec" and that is the one
sentence written down as a description. Actions are off at the repository setting rather than
merely absent, since "no Actions" reads as a setting and the change is one API call to undo.
The `.env` requirement for `docker compose build` is recorded, not worked around: `env_file`'s
`required: false` needs a Compose newer than the runbook assumes.

Not done here, by design: no test was added. The spec's testing decisions name the fresh clone as
this ticket's verification and say no new seam is added, so the link check above was a
throwaway script over `git ls-files`, not a committed test. The `--no-cache` build left the
previous builds' layers as dangling images on this laptop; pruning them is the presenter's call.
The first attempt at `gh repo create` was refused by the session's permission classifier as the
creation of a public surface; the author approved publishing in chat before the second.
