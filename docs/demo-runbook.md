# Demo runbook: Grafana Alert to OPS Incident

For the presenter, to be followed cold. The demo is one Alert's lifetime: traffic stops, Grafana
fires, a Run opens an Incident; Grafana repeats, a Run adds a trend and moves it on; traffic
returns, Grafana resolves, a Run completes it. About four minutes from the one action to the
Incident leaving the queue, three Runs, about $0.50.

Vocabulary is [CONTEXT.md](../CONTEXT.md). Every command below is run from the repo root, in a
shell that has the Jira credential (`JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`) and Docker.

## The screen

One screen, three windows, arranged before anyone is watching. Left column is what the machine
does; right column is what the audience believes.

| Window | Where | What it shows |
| --- | --- | --- |
| Top left: **Grafana** | <http://localhost:3000/alerting/list?search=rolldice> | The one rule, `rolldice request rate is zero`, and its state: Normal, Pending, Firing. No login |
| Bottom left: **container log** | a terminal running `docker compose logs -f demo` | Every Run as it happens: its reasoning, every `jira-as` command in full, every `forwarded` line, any `[DENIED]` |
| Right: **OPS Incidents queue** | <https://jasonkrue.atlassian.net/jira/servicedesk/projects/OPS/queues/custom/608> | The Incident appearing, changing status, and leaving |
| Hidden: **presenter shell** | a second terminal, repo root | The two commands the presenter types. Keep it out of the projected area or the audience reads ahead |

Reload the queue and the Grafana list by hand when the log says a Run has finished. Neither
refreshes fast enough on its own to be trusted during the demo.

Have two more tabs ready but not shown: [`skill/incident-sync/SKILL.md`](../skill/incident-sync/SKILL.md)
in an editor, and the Incident itself once it exists (click it in the queue), for the comments.

## Fifteen minutes before: pre-demo checks

Run them in this order. Every one must pass before the audience arrives; none takes more than a
minute except the first.

1. **Stack up.** `docker compose ps` shows four services running and `demo` healthy. If not:

    ```bash
    docker compose up -d --build
    ```

    A cold build pulls nothing new when the images are already on this machine; it has been
    known to hang for minutes on a Docker Hub pull if they are not. Start early.

2. **Health green.**

    ```bash
    curl -fsS http://localhost:8080/health
    ```

    Prints `ok`. Anything else: `docker compose logs demo` names the variable that is missing
    from `.env`.

3. **Queue empty, traffic flowing.** The reset closes every open Incident a rehearsal left
   behind and starts the traffic service:

    ```bash
    python3 -m grafana_jsm_sandbox.reset
    ```

    Prints one line per Incident it closed or left alone, then `queue is empty` and exit 0
    when nothing is left in the Incidents queue. **Until the six probes below are dealt with it
    ends `queue is NOT empty` and exit 1, naming them**, and that is the expected result on the
    day unless they have been deleted. Any other key it names is a human's: an open Incident
    in a status a Run never uses, or without an `fp-` label, finished in the Jira UI. See
    [Reset](#reset-between-takes-or-after-a-bad-one) for what it does and does not do.

4. **Grafana provisioned and the rule Normal.** The opt-in checks ask the running Grafana what it
   was actually given, and the running container who it is running as:

    ```bash
    DEMO_CONTAINER=1 python3 -m pytest tests/test_grafana.py tests/test_container.py -q
    ```

    All pass. The rule check needs the traffic to have been flowing for a minute, so run it after
    step 3, not before. If a provisioning file was edited since the stack came up, Grafana has
    not seen it: `docker compose restart lgtm`, wait a minute, rerun.

5. **Eyes.** Grafana's list shows the rule **Normal**. The Incidents queue shows nothing a Run
   made. The log's last lines are a `receiver listening` or a finished Run, not a Run in
   progress. Nothing else is posting at the Receiver: no replay, no end-to-end test in another
   shell.

**The six probes, decided before the demo.** The reset names OPS-1 to OPS-6 as stuck: the
probes from the day the workflow was mapped, `Canceled` or `Closed` without a resolution. The
queue filters on resolution, and no transition on this workflow can give them one now (ADR
0004), so they sit in the Incidents queue until one of two things is done. They are throwaway
and can be deleted, one at a time; the reset never deletes anything and this is the presenter's
call:

```bash
jira-as api call deleteIssue --issueIdOrKey OPS-1
```

The alternative is to project a filter instead of the queue, which starts empty and needs no
deletion: `project = OPS AND issuetype = Incident AND statusCategory != Done ORDER BY created DESC`.

## The demo, step by step

Times are from the one action, measured in rehearsal on this laptop (the record is at the
bottom). Grafana's parts add up: the rate window empties, then the thirty-second pending
period, then the next ten-second evaluation. The waits are real and worth narrating rather than
filling.

| When | Presenter does | Audience sees | Say meanwhile |
| --- | --- | --- | --- |
| T+0:00 | In the hidden shell: `docker compose stop traffic` (returns in about a second) | Nothing yet | What just happened: the only synthetic traffic to rolldice stopped. Grafana is about to notice |
| ~T+0:30 | Nothing | Grafana: **Pending** (reload) | The rule: request rate zero for thirty seconds, evaluated every ten. Point at the log: nothing has happened yet, because nothing has been sent |
| ~T+1:00 | Nothing | Grafana: **Firing** (reload) | Grafana has now posted one Notification at the Receiver. The Receiver acknowledged it in milliseconds and queued one Run |
| ~T+1:10 | Nothing | Log: `run ... started`, then `[claude]` lines, then `[tool] Bash: jira-as search jql ...`, then `forwarded GET ... upstream said 200` | Walk the log as it scrolls: it read the Notification, searched OPS for the Fingerprint label, found nothing, is creating. Every `forwarded` line is the Forwarder swapping the sentinel for the real token |
| ~T+1:35 | Reload the queue | **OPS-n** in the queue, status Open, Sev-2, Source Monitoring systems | Open it. Summary from the alert name and instance; Description with the annotations and the generator link; the `fp-` label; the opening comment with the value. The Run took about 30s |
| ~T+2:20 | Nothing | Log: second `run ... started` | This is the repeat: the policy resends a Firing Alert every minute. The Run finds the Match this time |
| ~T+2:45 | Reload the Incident | A trend comment: `Still firing. value=0 (previous value=0, unchanged). Open for 1m..`; status **Work in progress** | The comment reports value, change, time open, all read off Jira's clock. First repeat moves it on; later repeats only comment |
| ~T+2:50 | In the hidden shell: `docker compose start traffic` | Nothing yet | Traffic is back. Grafana needs one evaluation to see the rate, then sends the Resolved on the next group tick |
| ~T+3:05 | Nothing | Grafana: **Normal**; log: third `run ... started` | The Run is closing it: one comment with total duration and Firing count, then the `Resolve` transition with resolution Done |
| ~T+3:35 | Wait 20s, then reload the queue | Queue **empty**; the Incident is **Completed** with resolution Done | Completed, not Closed: a human closes, and Completed is the clean trigger for chapter three |

Whole lifecycle, stop to Completed: about three and a half minutes. Jira's search index lags a
resolution by ten to twenty seconds, so a queue reloaded the instant the log says `finished`
can still show the Incident. Count to twenty, then reload.

If a third `run` never starts because the repeat and the resolve landed close together, that is
Grafana coalescing, not a failure: the Resolved Run still arrives, one group interval later.

Do not `stop traffic` again for a second take until Grafana shows Normal and the queue is empty.
A re-fire deliberately gets a new Incident, which is the chapter two story, not a duplicate.

## What to say

These are the four points the audience is there for, in the order the demo makes them
available. Each has one thing on screen to point at.

**The Run can only run jira-as.** A Run is headless Claude Code in print mode with
`--permission-mode dontAsk` and an allow list of exactly two tools: `Bash(jira-as *)` and `Read`.
Anything else is denied without a prompt, and the denial is printed on a `[DENIED]` line in
the log window (ADR 0003). Show the command line:

```bash
python3 -m grafana_jsm_sandbox.run_command skill
```

The live Runs have so far never tried anything off the list, so the log has shown no denial.
The recorded Transcript in the repo has one, from a Run that was asked to `ls /etc`; render it
if the point needs a picture:

```bash
python3 -m grafana_jsm_sandbox.log_formatter fixtures/run-transcript.jsonl
```

**The Jira token lives in the Forwarder; the Run holds a sentinel.** The real token exists in
one process: the Receiver, and the Forwarder thread it owns, bound to the container's loopback.
Each Run gets an environment built from scratch, not inherited: `JIRA_SITE_URL` pointing at the
Forwarder over plain http and `JIRA_API_TOKEN` set to a random per-Run sentinel that the
Forwarder registers when the Run starts and forgets when it ends. Every `forwarded ... upstream
said` line in the log is the swap happening; a sentinel copied out of a Transcript is worth
nothing afterwards (ADR 0002). Show `RunSpawner` in
[`grafana_jsm_sandbox/run_spawner.py`](../grafana_jsm_sandbox/run_spawner.py) if asked how.
Nothing in the container is privileged: no Docker socket, non-root user, secrets from an env
file that git and the build context both refuse.

**The one credential that is not masked.** Say it plainly: the Anthropic OAuth token is in the
Run's environment, because the Run is Claude Code and that is how it authenticates. Nothing
documented masks it. Claude Code's native sandbox credential masking is the built-in equivalent
of the Forwarder, and it is the stretch goal, not what is running.

**What comes next.** Every Incident carries its Fingerprint label from day one, so chapter two,
grouping repeated Incidents of the same Alert under one Problem with the `is caused by` link, is
a lookup and one link, not a matching design. Chapter three drafts the post-incident review from
the comment history when an Incident Completes; that is why the automation stops at Completed
and never Closes.

Honest small print, if it comes up: the Description's Dashboard and Panel lines are empty
because the rule is linked to no dashboard; the repeat's value is the same zero as the first
Firing, so the trend reads `unchanged`; a lifecycle is three Runs and about fifty cents.

## Fallback: the replay

Switch to it when any of these happens. Nothing is restarted.

- Grafana has not shown Pending within a minute of the stop, or Firing within two.
- The log shows no `run ... started` within two minutes of Firing.
- Grafana's page is down or will not load.

Two commands in the hidden shell, in this order:

```bash
docker compose start traffic
```

```bash
python3 -m grafana_jsm_sandbox.replay --receiver http://localhost:8080 --pause 45
```

Traffic first, so that if Grafana wakes up mid-replay it goes Normal and sends at most a
Resolved, which a Run skips when the Incident is already Completed. The replay then posts the
three Notifications Grafana sent in a real rehearsal, Firing, repeat, Resolved, forty-five
seconds apart, and the log, the queue and the Incident do exactly what the table above says,
minus Grafana's own state changes. It runs about two and a half minutes.

The fixtures carry the real Alert's Fingerprint. If the live Firing had already opened an
Incident before Grafana went quiet, the replayed Firing comments on it instead of opening a
second: that is the Match working, and the demo is intact. The one thing not to do is run the
replay while Grafana is still Firing and posting.

## Reset: between takes, or after a bad one

```bash
python3 -m grafana_jsm_sandbox.reset
```

It finds every open OPS Incident carrying an `fp-` label, takes each out of the queue the only
clean way this workflow has, `Resolve` with resolution Done and then `Close`, leaves a comment
saying the reset did it, and then starts the traffic service so that the rule returns to Normal.
It prints what it did per key and ends with `queue is empty` and exit 0, or names what it left:
an `fp-` Incident with no road to Completed from where it is (`Pending`, which only a human
uses), an open Incident with no `fp-` label, which is not a Run's and is not touched, or a done
Incident with no resolution, which nothing but deletion can take out of the queue and which it
prints the delete command for. It does not cancel anything: `Canceled` carries no resolution and
stays in the queue for good (ADR 0004). It does not delete anything either.

After a clean take nothing is open and the reset only starts traffic. After an abandoned take,
run it, then wait for Grafana to show Normal before the next `stop traffic`. If a Run is still
in progress in the log, let it finish first; a stuck one is killed by the Receiver after five
minutes and the queue moves on.

A change to a provisioning file is the one thing the reset cannot fix: `docker compose restart
lgtm`, then a minute for Grafana to come back.

## Rehearsal record

See the ticket, [`.scratch/alert-to-incident-sync/issues/08-demo-runbook-and-rehearsal.md`](../.scratch/alert-to-incident-sync/issues/08-demo-runbook-and-rehearsal.md),
for the timed run this runbook's numbers come from and the hiccups it found.
