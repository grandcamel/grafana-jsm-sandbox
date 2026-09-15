# 05 — The public repository exists and builds from a fresh clone

**What to build:** `grandcamel/grafana-jsm-sandbox` exists on GitHub as a public repository with `main` as its default branch, pushed from this tree with a one-sentence description. A fresh clone into a temporary directory passes the offline suite and builds both images from the pinned base without any file from this machine. The rendered README reads correctly on GitHub.

**Blocked by:** 04 — The tree is ready for a stranger to clone

**Status:** ready-for-agent

- [ ] The repository is created public with the description from the spec and `main` pushed; Issues on, no Actions; the URL is recorded in this ticket and in the README
- [ ] A fresh clone into a temporary directory passes `python3 -m pytest` with no network beyond PyPI for the dev dependencies
- [ ] From the same clone, `docker compose build` succeeds with the placeholder certificate, pulling only the pinned base images
- [ ] The README renders on GitHub with its links resolving; any broken link is fixed and re-pushed
