# 02 — A corporate CA is trusted through the build and every Run

**What to build:** On a laptop behind an intercepting proxy such as Zscaler, the presenter exports the corporate root CA to a file, names it with one environment variable, and `docker compose build` succeeds: the certificate is installed into the system trust store of both images this repo builds before any `npm` or `pip` install runs. At runtime the Receiver, the Forwarder, `jira-as` and Claude Code all trust it through the standard trust-store variables set image-wide, and each Run inherits those variables alongside its sentinel and nothing else new. With no certificate named, the build uses a committed placeholder and behaves exactly as before. The real certificate file is never committed. The runbook gains a work-laptop section.

**Blocked by:** 01 — The demo image carries only what a Run needs

**Status:** done

- [x] Both Dockerfiles take an `EXTRA_CA_CERT` build argument defaulting to a committed, intentionally empty placeholder; the copy and `update-ca-certificates` precede every `npm install` and `pip install`, and the default-run container check reads that ordering off the files
- [x] The demo image sets `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `PIP_CERT` and `NODE_EXTRA_CA_CERTS` to the system bundle, read off the Dockerfile by the default-run check
- [x] Compose passes the argument into both builds from the presenter's environment with the placeholder as the default; the certificate directory's other contents are ignored by git and admitted by the build context, checked with real `git check-ignore` and the committed ignore files
- [x] The Run spawner's real-child-process test shows the trust-store variables present in a Run's environment when the Receiver has them and absent when it does not, with nothing else new either way
- [x] Built with a self-signed test CA, the opt-in stack check finds that certificate's fingerprint in the running container's bundle and Python's default SSL context loads it; built with the placeholder, the same checks pass with nothing added
- [x] The runbook has a work-laptop section: exporting the CA, the build variable, the shell's own `jira-as` bundle variable for the reset and the end-to-end check, the Docker Desktop pull caveat, and the pre-demo check that reads the certificate back out of the container

## Comments

Done. Both Dockerfiles take `ARG EXTRA_CA_CERT=certs/NO_EXTRA_CERTS`, copy the named file in
and, when it is non-empty, install it into the system trust store with `update-ca-certificates`
before the first `npm install` or `pip install`; a non-empty file that is not PEM stops the build
with `EXTRA_CA_CERT is not a PEM certificate`. The demo image sets the five trust-store variables
image-wide right after that step, before the installs, and the rolldice image sets `PIP_CERT`,
its build's only TLS client being pip and the bootstrap that runs pip. The Run spawner hands the
five on to a Run when the Receiver has them, and the real-child-process test shows them present
with the Receiver's values and absent without, with nothing else new either way.

Verified on this laptop, three ways:

- **A self-signed test CA.** `openssl req -x509 -newkey ec ... -days 1` into `certs/test-ca.crt`,
  then `EXTRA_CA_CERT=certs/test-ca.crt docker compose build`: both builds logged `1 added, 0
  removed`. `DEMO_CONTAINER=1 EXTRA_CA_CERT=certs/test-ca.crt python3 -m pytest
  tests/test_container.py` passed all 64: the certificate's SHA-256 fingerprint is in the
  container's bundle, Python's default SSL context loaded it, `/usr/local/share/ca-certificates`
  holds exactly `extra-ca.crt`, and all five variables in the container point at the bundle.
- **A file that is not a certificate.** `EXTRA_CA_CERT=certs/bogus.crt` stopped the demo build
  at the trust-store step with the message above, rather than at a TLS error under `npm`.
- **The placeholder.** A plain `docker compose build` skipped the install (no `added` line), the
  same 64 checks passed with the placeholder case selected, nothing is under
  `/usr/local/share/ca-certificates`, and the image is still 539 MB.

Then the lifecycle against the placeholder-built container: `python3 -m grafana_jsm_sandbox.reset`,
then `DEMO_END_TO_END=1 DEMO_RECEIVER_URL=http://localhost:8080 python3 -m pytest
tests/test_end_to_end.py` passed in 86s. OPS-17: three Runs exiting 0 in 25.9s, 21.9s and 27.2s,
opened, commented `Still firing`, then `Resolved after 41s, 2 Firings` and Completed with
resolution Done; cleanup left it Closed. The offline suite is 219 passed, 27 skipped; ruff is
clean; mypy's two findings are the pre-existing ones.

Three things worth recording:

- **The rolldice build context is now the repo root, not `docker/rolldice`.** The spec says the
  rolldice service is unchanged apart from the build argument, but its own directory cannot see
  a `certs/` directory at the root, and Compose here is v2.0.0-rc.2, which has no
  `additional_contexts`. Building from the root with `dockerfile: docker/rolldice/Dockerfile`
  means one variable, `certs/<file>`, names the same file for both images; the Dockerfile's two
  `COPY` lines now say `docker/rolldice/...`. The default-run check holds both contexts to the
  repo root for that reason.
- **The placeholder is genuinely empty**, zero bytes, and the Dockerfile tests `-s` rather than
  grepping a comment out of it; the explanation lives in `.gitignore` and the Dockerfile. Git
  ignores `certs/*` with one exception, and the build context admits the directory.
- **`REQUESTS_CA_BUNDLE` in the presenter's shell replaces the bundle rather than adding to it.**
  The runbook says so and gives the one-line concatenation with `certifi` for a laptop where some
  hosts bypass the proxy. `SSL_CERT_FILE` is not needed there: the reset and the end-to-end check
  reach Jira through `jira-as`, which is `requests`, and reach the Receiver over plain HTTP.

Not verified here, because this laptop has no intercepting proxy: that Claude Code's native
binary reads `NODE_EXTRA_CA_CERTS` for its Anthropic traffic, which Claude Code's own
documentation states and the spec relies on. The work-laptop rehearsal is where that is seen.
The compose hardening (ticket 03) is untouched.

## What the review changed

Nothing. The standards review found no vocabulary or style breach and judged the identical
eight-line trust-store block in the two Dockerfiles warranted, since the images share no base
and a Dockerfile has no include; the verification is deduplicated instead, parametrised over both
files. The spec review confirmed all six checklist items against the files, checked that the
ordering test's "before the earliest install" is "before every install" because a Dockerfile runs
in source order, that compose's `:-` default treats an empty variable as unset the way the
runbook says, and that `REQUESTS_CA_BUNDLE` replaces the bundle as the runbook warns. Its one flag
is the rolldice build context, recorded above as the deliberate departure from "unchanged apart
from the build argument", and it judged the reason sound.
