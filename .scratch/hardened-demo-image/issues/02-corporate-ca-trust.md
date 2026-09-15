# 02 — A corporate CA is trusted through the build and every Run

**What to build:** On a laptop behind an intercepting proxy such as Zscaler, the presenter exports the corporate root CA to a file, names it with one environment variable, and `docker compose build` succeeds: the certificate is installed into the system trust store of both images this repo builds before any `npm` or `pip` install runs. At runtime the Receiver, the Forwarder, `jira-as` and Claude Code all trust it through the standard trust-store variables set image-wide, and each Run inherits those variables alongside its sentinel and nothing else new. With no certificate named, the build uses a committed placeholder and behaves exactly as before. The real certificate file is never committed. The runbook gains a work-laptop section.

**Blocked by:** 01 — The demo image carries only what a Run needs

**Status:** ready-for-agent

- [ ] Both Dockerfiles take an `EXTRA_CA_CERT` build argument defaulting to a committed, intentionally empty placeholder; the copy and `update-ca-certificates` precede every `npm install` and `pip install`, and the default-run container check reads that ordering off the files
- [ ] The demo image sets `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `PIP_CERT` and `NODE_EXTRA_CA_CERTS` to the system bundle, read off the Dockerfile by the default-run check
- [ ] Compose passes the argument into both builds from the presenter's environment with the placeholder as the default; the certificate directory's other contents are ignored by git and admitted by the build context, checked with real `git check-ignore` and the committed ignore files
- [ ] The Run spawner's real-child-process test shows the trust-store variables present in a Run's environment when the Receiver has them and absent when it does not, with nothing else new either way
- [ ] Built with a self-signed test CA, the opt-in stack check finds that certificate's fingerprint in the running container's bundle and Python's default SSL context loads it; built with the placeholder, the same checks pass with nothing added
- [ ] The runbook has a work-laptop section: exporting the CA, the build variable, the shell's own `jira-as` bundle variable for the reset and the end-to-end check, the Docker Desktop pull caveat, and the pre-demo check that reads the certificate back out of the container
