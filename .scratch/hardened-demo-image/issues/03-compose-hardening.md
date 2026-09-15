# 03 — The demo container runs the way Anthropic's deployment guide describes

**What to build:** The demo service runs with every Linux capability dropped, `no-new-privileges`, a read-only root filesystem with tmpfs for the temp directory, the runs directory and the Run user's home, a process limit, and memory and CPU limits sized for three Runs in a row on a laptop. The lifecycle still runs end to end under those limits. The default test run reads each control off the committed compose file; the opt-in stack run proves the root filesystem refuses a write and the tmpfs paths accept one. The runbook's spoken points name which controls are Anthropic's recommendations.

**Blocked by:** 01 — The demo image carries only what a Run needs

**Status:** done

- [x] The demo service declares `cap_drop: [ALL]`, `no-new-privileges`, `read_only: true`, tmpfs mounts for the temp directory, the runs directory and the Run user's home, `pids_limit`, and memory and CPU limits; each is read off the compose file by a default-run check
- [x] The opt-in stack check shows a write to the root filesystem refused and a write to each tmpfs path accepted, from inside the running container
- [x] The Receiver starts, the onboarding flag is written, and the replay drives an Incident from created to Completed under the limits; the outcome is recorded in this ticket
- [x] The runbook's spoken points say which controls come from Anthropic's secure-deployment guide and which are this repo's, and the README's container section lists the hardening

## Comments

Done. The demo service declares `cap_drop: [ALL]`, keeps `no-new-privileges:true`, and is
`read_only: true` with three tmpfs mounts: `/tmp` (256m), `/app/runs` (64m) and `/home/demo`
(512m), the last two the Run user's own (`uid=1000,gid=1000,mode=0700`, the uid the Dockerfile's
`useradd` gives the account). `pids_limit: 256`, `mem_limit: 2g`, `cpus: 2`. The three
directories are exactly what `docker diff` listed on the ticket-02 container after its three
Runs, and nothing else; under the read-only root, `docker diff` after a lifecycle is empty.

Verified on this laptop against the real OPS project:

- **Default run.** The container checks read each control off the compose file: the capability
  drop, the security option, the read-only root, exactly three tmpfs mounts and no volume, the
  uid, gid and mode on the two the user owns, a size on each, and each limit with headroom over
  the measured peak. `test_container.py` is 54 passed, 18 skipped with no stack up.
- **Opt-in.** `DEMO_CONTAINER=1 python3 -m pytest tests/test_container.py`: 81 passed, 1 skipped
  (the named-certificate case, since the placeholder was built). Inside the running container the
  kernel says uid 1000, all four capability masks `0000000000000000`, `NoNewPrivs: 1`, a write to
  `/app` refused with `Read-only file system` (the user owns `/app`, so only the read-only root
  can be what refuses it), a write to each of the three tmpfs accepted, and the cgroup limits
  256 processes, 2 GiB and 2 CPUs.
- **Lifecycle.** `python3 -m grafana_jsm_sandbox.reset`, then `DEMO_END_TO_END=1
  DEMO_RECEIVER_URL=http://localhost:8080 python3 -m pytest tests/test_end_to_end.py` passed in
  103s. OPS-18: three Runs exiting 0 in 21.17s, 30.06s and 37.92s, opened, commented, then
  Completed; cleanup left it Closed. No `[DENIED]`, nothing on stderr. Sampled every 0.7s
  through the run, the cgroup held at most **24 tasks** (processes and threads together) and
  peaked at **227 MB** (`memory.max_usage_in_bytes`). The offline suite is 226 passed,
  37 skipped; ruff is clean; mypy's three findings are the pre-existing ones.

Four things worth recording:

- **This laptop's Compose v2.0.0-rc.2 applies `read_only`, `cap_drop`, `security_opt`, tmpfs
  with options and `mem_limit`, and silently ignores `pids_limit` and `cpus`.** Read from the
  Compose source at its tags: `pids_limit` reaches the host config from v2.2.0, and the
  service-level `cpus` from v2.17.0 (before that it fed a Windows-only `CPUPercent` field).
  The `deploy.resources.limits` form was tried and rejected: this Compose refuses `pids` under
  it outright and turns `cpus: "2"` into two nanoCPUs. The classic keys are the ones the spec
  names and a current Compose applies all three. The opt-in check therefore reads what the
  kernel enforces and, when a limit is off, fails naming the Compose version rather than
  passing on the file alone: before the stopgap it failed exactly twice, `pids_limit is declared
  but the kernel enforces 'max': Compose v2.0.0-rc.2 did not apply it` and the same for `cpus`.
  The stopgap the runbook now names, `docker update --pids-limit 256 --cpus 2` on the running
  container, is what the verification above ran under; a recreate loses it, and a current
  Docker Desktop needs it not at all.
- **A tmpfs is root's and world-writable unless told otherwise.** Docker's default is mode
  1777 owned by root, which works but leaves `ls -ld ~` inside the container showing a sticky
  world-writable directory. The runs directory and the home carry the user's uid and gid and
  mode 0700, and the default-run check reads the uid off the Dockerfile's `useradd` line so the
  two files cannot drift apart. `/tmp` keeps the default, which is what `/tmp` is.
- **Docker mounts a tmpfs `noexec,nosuid,nodev`.** Seen in `mount` inside a probe container.
  Nothing a Run does executes from `/tmp` or the home: Claude Code's binary is under
  `/usr/local/lib`, and the shell snapshot it writes under `~/.claude` is sourced, not run.
  The lifecycle ran clean under it.
- **The process limit counts threads.** The peak of 24 is tasks, not processes, and a 0.7s
  sample misses the moment a Bash tool call forks. The guide's example uses 100; 256 is that
  with room for what the sample misses, and the sizing check holds each limit to at least four
  times the measured peak so a smaller limit someday has to argue with the number.

Not done here, by design: a container-level egress allowlist and a custom seccomp profile
(Docker's default profile is what runs), both recorded in the spec as the next steps, and
tickets 04 and 05.
