# Spec: A minimal, hardened demo image that trusts a corporate CA, published for the work laptop

Status: ready-for-agent
Created: 2026-09-15
Supersedes: `.scratch/publish-to-github/spec.md` (its steps are tickets 04 and 05 here; its four
open decisions were taken on 2026-09-15 and are recorded below)

## Problem Statement

The demo image extends `grandcamel/claude-devcontainer`, a 4.1 GB batteries-included developer
image built for interactive work: it carries `sudo`, the `docker` CLI, `docker`-group membership,
`gh`, `iptables` and some thirty developer tools that no Run needs and that a corporate audience
will ask about. The research in `docs/research/harness-sandbox-containers-2026-09.md` found that
Anthropic's own guidance for a headless, tool-restricted agent is a minimal container hardened
with dropped capabilities, a read-only root and a non-root user, with credentials behind a proxy,
which is what the Forwarder already is.

The next showing is on a corporate work laptop behind Zscaler. That laptop can clone only a
public GitHub repository, and every TLS connection from a process on it, including from inside a
container, is intercepted by Zscaler and presents a certificate chain ending in the corporate root
CA. Today nothing in the image, the build, the Receiver, the Forwarder or a Run trusts that CA, so
`npm install` and `pip install` fail during the build, the Forwarder cannot reach Atlassian, and
a Run cannot reach Anthropic. The repo also has no remote, no license, and a few private strings.

## Solution

The demo image is rebuilt from a slim official Node image plus Python, with exactly Claude Code
and `jira-as` pinned, a non-root user and nothing else. An optional corporate CA certificate is
taken at build time as a build argument, defaulting to a committed placeholder, is installed into
the system trust store before any package install in both images this repo builds, and is exposed
to Python, Node, pip and curl through the standard trust-store variables, which each Run inherits
alongside its sentinel. Compose runs the container with all capabilities dropped, a read-only root,
tmpfs scratch, a process limit and resource limits. The tree is scrubbed, licensed and pushed to a
public GitHub repository, and the runbook gains the presenter's steps for the work laptop. The
Receiver, the Forwarder, the Skill, the Run's permission mode and the sentinel are unchanged; ADRs
0001 to 0004 stand.

## User Stories

### Presenter on the work laptop

1. As a presenter, I want to clone the public repository on the work laptop and run one compose
   command, so that the demo builds there without any file that only exists on the personal laptop.
2. As a presenter, I want to point the build at the corporate root CA with one environment
   variable, so that the build's `npm` and `pip` installs succeed behind Zscaler.
3. As a presenter, I want the Forwarder to reach the Atlassian site through Zscaler, so that a Run's
   Jira calls succeed on the work laptop exactly as they do at home.
4. As a presenter, I want a Run's Claude Code to reach Anthropic through Zscaler, so that the Run
   itself starts and finishes on the work laptop.
5. As a presenter, I want the rolldice image to build behind Zscaler too, so that the Alert has
   something to fire about.
6. As a presenter, I want the certificate file never to be committed, so that a corporate artifact
   does not end up in a public repository.
7. As a presenter, I want the runbook to have a work-laptop section: where the certificate comes
   from, which variable names it, what the shell's own `jira-as` needs, and what to check before
   the demo, so that I can follow it cold on a machine I did not prepare the night before.
8. As a presenter, I want a build with no certificate to behave exactly as today, so that the
   personal laptop and the work laptop run the same repository at the same commit.

### Audience

9. As an audience member, I want the container to hold nothing but Claude Code, `jira-as` and the
   Skill, so that the answer to "what else can the Run reach for" is "nothing" and can be shown with
   one command.
10. As an audience member, I want the container to run with no capabilities, a read-only root and
    a non-root user, so that the boundary is the one Anthropic's own deployment guide describes.
11. As an audience member, I want the presenter to say which controls are Anthropic's
    recommendations and which are this repo's, so that the story is honest.
12. As an audience member, I want the repository to be public with a license, so that I can clone
    it after the session.

### Operator

13. As an operator, I want the image to be a fraction of today's size, so that a rebuild an hour
    before the demo is minutes, not tens of minutes, and pulls nothing that is not on the machine.
14. As an operator, I want `sudo`, the `docker` CLI and the `docker` group gone from the image, so
    that there is nothing to explain away.
15. As an operator, I want the Receiver to run as a non-root user in an image that has no root
    escalation path, so that `no-new-privileges` is a belt on a pair of trousers rather than the
    only thing holding them up.
16. As an operator, I want the certificate applied before any package install in the build, so
    that the build itself works behind the intercepting proxy, not only the runtime.
17. As an operator, I want the trust-store variables set once, image-wide, so that the Receiver,
    the Forwarder and every child process see the same bundle without per-process configuration.
18. As an operator, I want a Run's scrubbed environment to carry the trust-store variables and
    nothing else new, so that the credential story from ADR 0002 is unchanged.
19. As an operator, I want the read-only root to leave the Receiver's runs directory, Claude Code's
    configuration directory and a temp directory writable on tmpfs, so that a Run has what it
    needs and nothing persists across a container restart.
20. As an operator, I want a process limit and memory and CPU limits on the demo container, so
    that a misbehaving Run cannot take the laptop down mid-demo.
21. As an operator, I want the healthcheck to need no tool the minimal image does not carry, so
    that compose reports the container healthy for the right reason.
22. As an operator, I want the default test run to read the hardening off the committed Dockerfile
    and compose file, so that a regression is caught with no stack up.
23. As an operator, I want the opt-in stack checks to ask the running container whether the
    escalation tools are absent and whether the trust store carries the certificate named at
    build time, so that the claim on the slide was verified on the machine giving the demo.
24. As an operator, I want the base image pinned to a tag or digest, so that a build on the work
    laptop produces the image that was rehearsed.

### Future developer

25. As a future developer, I want an ADR recording that the container is the boundary and the
    image carries only what a Run needs, so that the next person does not re-add a developer kit
    because it was convenient.
26. As a future developer, I want the publishing decisions written down (license, what stays in
    the tree), so that the public repository's shape is not re-litigated.
27. As a future developer, I want the egress allowlist and the API-key-behind-the-Forwarder
    options recorded as the next steps, with the research they come from, so that they are picked
    up as tickets and not rediscovered.

## Implementation Decisions

### Image

- The demo image is built from the official slim Debian image for the current Node LTS, with
  Python 3 and pip added from the distribution. Node 22.15 or later is required because Claude Code
  reads the operating system trust store only on that runtime or newer; the extra-CA variable is
  set as well so that the OS-store path is not the only one.
- The image installs exactly: `ca-certificates`, Python 3 with pip, Claude Code at a pinned
  version through npm, `jira-as` at a pinned version through pip, this package and the Skill.
  No `sudo`, no `docker`, no `gh`, no `git`, no `curl`, no `jq`, no shell conveniences. The
  entrypoint's onboarding pre-acceptance is rewritten in Python so that `jq` is not needed.
- One non-root user created by the Dockerfile owns the application directory and its runs
  directory. There is no `docker` group. The Dockerfile's last `USER` is that user.
- The base image reference is pinned to a specific tag (or digest) and remains overridable by
  the existing `BASE_IMAGE` build argument for a mirror on a restricted network.
- The image is expected to be well under one gigabyte. The ticket records the measured size.

### Corporate CA trust

- A build argument `EXTRA_CA_CERT` names a file in the build context. Its default is a
  committed placeholder file that is intentionally empty, following the mechanism already used by
  the `claude-devcontainer` repository. The Dockerfile copies the named file in *before* the
  `npm` and `pip` installs, and when it is non-empty installs it into the system trust store with
  `update-ca-certificates`.
- The same mechanism is applied to the rolldice image, whose build runs `pip install` and
  `opentelemetry-bootstrap`, both of which reach PyPI through the proxy.
- The demo image sets, image-wide: `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`,
  `PIP_CERT` and `NODE_EXTRA_CA_CERTS`, all pointing at the system bundle. Python's `ssl` module
  and therefore the Forwarder's `urllib` honour `SSL_CERT_FILE`; the `requests` library that
  `jira-as` uses honours `REQUESTS_CA_BUNDLE`; Claude Code documents `NODE_EXTRA_CA_CERTS` as the
  custom-CA setting. A Run's Jira traffic goes to the Forwarder over plain HTTP on loopback and
  needs no trust store; its Anthropic traffic does.
- The Run spawner adds the trust-store variables to a Run's environment when they are present in
  the Receiver's environment, and nothing else new. The scrubbed-environment rule from ADR 0002
  holds: the real Jira token still never reaches a Run.
- Compose passes `EXTRA_CA_CERT` into both builds from the presenter's shell environment, with
  the placeholder as the default, so the build command is the same on both laptops. The real
  certificate lives in a directory whose contents git ignores; the placeholder in that directory
  is the one committed file. The build context admits that directory.
- The runbook gains a section for the work laptop: exporting the certificate from the OS trust
  store, the variable to set before `docker compose build`, the same bundle variable for the
  shell's own `jira-as` (used by the reset and the end-to-end check), the fact that Docker Desktop
  must already trust the corporate CA for image pulls (outside this repo), and the pre-demo check
  that reads the certificate back out of the running container.

### Compose hardening

- The demo service gains `cap_drop: [ALL]`, keeps `no-new-privileges`, and gains `read_only:
  true` with tmpfs mounts for the temp directory, the runs directory and the Run user's home (where
  Claude Code writes its configuration). It gains `pids_limit` and memory and CPU limits sized for
  three Runs in a row on a laptop.
- The healthcheck calls the health endpoint with Python's standard library, since the image has
  no `curl`.
- The `traffic` and `lgtm` services are unchanged. The `rolldice` service is unchanged apart from
  the build argument.

### Publishing

- License: MIT, at the repository root. The three rolldice files copied from
  `grafana/docker-otel-lgtm` keep their Apache-2.0 attribution in a header comment and a NOTICE
  line.
- The `.scratch/` spec and tickets stay in the public tree, scrubbed of the site name, the account
  email and the audience company. The demo runbook's queue URL becomes a placeholder. The
  `HANDOFF.md` session note is removed; the one fact only it holds, the working project template
  key, moves into ADR 0004.
- The recorded Transcript fixture is scrubbed of the account email, account id and the recording
  machine's scratchpad path, and a default-run test greps every committed fixture for an `@` that
  is not `example.invalid`.
- Repository: `grandcamel/grafana-jsm-sandbox`, public, default branch `main`, no Actions. The
  README's opening tells a stranger what this is, what they need (Docker, a Jira Cloud site with an
  ITSM project, a Claude Code OAuth token, `jira-as` in the shell), and that the OPS field ids in
  the Skill are one site's and must be re-read from theirs.
- Verification is a fresh clone into a temp directory: the offline suite passes and the image
  builds from the pinned base.

### Records

- An ADR records the decision this spec implements: the container is the boundary, the image
  carries only what a Run needs, and the hardening follows Anthropic's secure-deployment guide;
  bubblewrap-based sandboxing is deliberately not layered inside the container.

## Testing Decisions

- A good test drives a seam from the outside and asserts observable behaviour. Two existing seams
  carry everything here; no new seam is added.
- **The container checks.** The default run reads the committed Dockerfile, compose file and
  example env file as text and holds them to the decisions above: the base image is the slim
  Node image at a pinned tag; the last `USER` is not root; no line installs `sudo`, `docker`, `gh`
  or `jq`; the extra-CA copy and `update-ca-certificates` precede every `npm install` and
  `pip install`; the five trust-store variables are set; the demo service drops all capabilities,
  is read-only with the three tmpfs mounts, and carries a pids limit and resource limits; both
  builds take the `EXTRA_CA_CERT` argument; the placeholder is committed and its directory's
  other contents are ignored by git; the healthcheck names no `curl`. Prior art: every existing
  test in the container check that reads the Dockerfile and compose file back.
- The opt-in stack run asks the running container: the user is not root; `sudo`, `docker` and `gh`
  are not on the PATH; `claude` and `jira-as` are; the root filesystem refuses a write and the
  tmpfs paths accept one; and, when the presenter's shell names an `EXTRA_CA_CERT`, that
  certificate's fingerprint is in the container's bundle and Python's default SSL context loads
  it. Prior art: `TestAStackThatIsUp`.
- **The Run spawner.** The existing real-child-process test that dumps a Run's environment gains
  the case that the trust-store variables, when set for the Receiver, appear in the Run's
  environment with the same values, and that a Receiver without them starts a Run without them.
  The existing assertion that nothing else appears stays.
- The replay against the rebuilt container, and the opt-in end-to-end check, are the proof that
  the lifecycle still runs; they are run and their outcome recorded in the ticket, not added to.
- A self-signed test CA generated by the presenter (or the ticket's author) is the way to exercise
  the certificate path without the corporate certificate; the tests accept any certificate file.

## Out of Scope

- A container-level egress allowlist (the reference devcontainer's iptables approach). Zscaler
  restricts egress on the work laptop; on the personal laptop the OAuth token remains
  exfiltratable by design, and the runbook keeps saying so. Recorded as the next step.
- Replacing the OAuth token with an API key behind the Forwarder via `--bare` and
  `ANTHROPIC_BASE_URL`. Changes billing and what a Run loads; a ticket of its own later.
- Claude Code's built-in Bash sandbox, `enableWeakerNestedSandbox`, or the sandbox runtime inside
  the container.
- gVisor or a microVM runtime.
- CI on GitHub.
- Trusting the corporate CA in Docker Desktop itself, or in the presenter's shell tools beyond
  the one variable the runbook names.
- Any change to the Receiver, Forwarder, Skill, permission mode or sentinel design.
- Chapters two and three.

## Further Notes

- The research this follows is `docs/research/harness-sandbox-containers-2026-09.md`; the
  hardened `docker run` shape and the credential-proxy recommendation are quoted there from
  Anthropic's secure-deployment guide, and the "considerably weakens security" line about nested
  bubblewrap from the sandboxing guide.
- Claude Code's network page lists the hosts a Run must reach: `api.anthropic.com`, and for OAuth
  `claude.ai` and `platform.claude.com`. All three go through Zscaler on the work laptop.
- `read_only: true` moves three things onto tmpfs: `/tmp`, the runs directory, and the Run user's
  home, because the entrypoint writes the onboarding flag there and Claude Code writes its
  configuration and debug logs there. Nothing in the demo needs to survive a container restart.
- The `traffic` service is Alpine and makes no TLS connection; the LGTM image is pulled, not built,
  and makes no outbound connection at runtime. Neither needs the certificate.
- The earlier publishing spec's audit (no credential in the tree or history; author email on every
  commit is the GitHub identity and stays) is not repeated here; ticket 04 carries its scrub list.
- Docker Desktop on a corporate laptop usually trusts the OS keychain for image pulls. If a pull
  fails there, that is a Docker Desktop setting, not this repo, and the runbook says so.
