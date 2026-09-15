# The Jira project is one setting, and the Skill is rendered for it

The Skill names its project key, `OPS`, in every invocation, because each must be runnable as written and readable off a screen during the demo. A demo against another site's project used to mean editing the Skill, the reset, the end-to-end check and the shell's `jira-as` allowlist by hand, four places that drift. Now one variable, `JIRA_PROJECT`, names the project: the container reads it from `.env`, and the laptop-side tools read it from the shell or, failing that, from the same `.env`. The committed Skill stays written for `OPS`. For any other key the Receiver copies the skill directory once at startup, under `/tmp`, with whole occurrences of `OPS` rewritten, and points every Run at the copy; a demo for `OPS` reads the committed file exactly as before.

A Run's `jira-as` is held to that one project through `JIRA_ALLOWED_PROJECTS`, which `jira-as` reads over any settings file. This is one variable more in a Run's environment than the hardened-image spec's "nothing else new" allowed for, and it is added on purpose: a Run's working directory has no settings file, so until now a Run's `jira-as` had no project allowlist at all while the laptop's shell had one. The variable gates which project `jira-as` will address, not what the credential behind the Forwarder can reach, so it widens nothing; the scrubbed environment of ADR 0002 is otherwise unchanged and the real Jira token still never reaches a Run. The reset and the end-to-end check set the same variable on the `jira-as` they run.

## Consequences

- `JIRA_PROJECT=<key>` in `.env` is the whole change for another project. The site's own Incident field ids are still read from that site and edited into the Skill (ADR 0004); a key is a setting, a field id is a fact about a site.
- The default test run holds the committed Skill to `OPS` and the rendered copy to the configured key in the four places a Run types it, with `OPS` inside another word or key left alone.
- The shell's `.claude/settings.json` still allows `OPS` only; a presenter's own `jira-as` commands against another project need `JIRA_ALLOWED_PROJECTS=<key>` exported too. Everything this repo runs sets it for itself.
- The rendered copy lives on tmpfs and is made again at every container start, which is the only time it can change.
