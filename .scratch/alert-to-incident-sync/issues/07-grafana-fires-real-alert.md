# 07 — Grafana fires the real Alert from synthetic traffic

**What to build:** With the stack up, a rolldice example app receives synthetic traffic and Grafana is quiet. The presenter stops the traffic service; within about a minute Grafana fires the Alert, the Receiver gets the Notification, and an Incident appears in OPS. Repeat Firings arrive every minute and add trend comments. The presenter restarts traffic; the Alert resolves and the Incident Completes. Total lifecycle under five minutes, driven entirely from this repo's provisioning files.

**Blocked by:** 06 — Demo container and compose

**Status:** ready-for-agent

- [ ] Provisioning files in this repo, mounted into the LGTM container's alerting provisioning directory, define a webhook contact point aimed at the demo service, a notification policy with one-minute repeat interval and short group wait, and one alert rule
- [ ] The rule fires when the rolldice request rate is zero for thirty seconds, evaluated every ten seconds, with labels for severity and service that the field mapping consumes
- [ ] rolldice and its traffic generator run as compose services; stopping and starting the traffic service is the only presenter action
- [ ] Grafana shows the rule Firing, then Normal, on the laptop
- [ ] The Notification Grafana sends passes the Receiver's validation unchanged; any shape difference from the canned fixtures is reconciled in the fixtures, not by loosening validation
- [ ] Observed timings for fire, first repeat, and resolve are recorded in the ticket
- [ ] The four-hour default repeat interval is overridden and the override is documented in the README
