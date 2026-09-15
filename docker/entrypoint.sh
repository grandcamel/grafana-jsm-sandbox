#!/bin/sh
# The demo container's entrypoint: get Claude Code past onboarding, then become the
# Receiver.
#
# Headless Claude will not start against a config that has never been through
# onboarding, and there is no one here to click through it, so this writes the one
# flag that says it has been. It writes only that one.
#
# The existing container entrypoints on this machine also pre-accept bypass
# permissions mode. This one deliberately does not: a Run's boundary is the
# permission mode it is started in, and ADR 0003 is explicit that this demo does
# not take the skip-permissions route every other wrapper here takes. There is
# nothing in this container that would let a Run out of `dontAsk`.
#
# Nothing else is done. The Receiver reads its own configuration and refuses to
# start without a Jira credential and an Anthropic token, which is a better message
# than anything this script could print.
#
# Unlike the entrypoint this borrows from, a command given to the container is
# honoured — `docker compose run --rm demo sh` is how you look around inside.
set -eu

CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ONBOARDING="$CLAUDE_CONFIG_DIR/.claude.json"

mkdir -p "$CLAUDE_CONFIG_DIR"
if [ -f "$ONBOARDING" ]; then
    jq '. + {hasCompletedOnboarding: true}' "$ONBOARDING" > "$ONBOARDING.tmp" \
        && mv "$ONBOARDING.tmp" "$ONBOARDING"
else
    echo '{"hasCompletedOnboarding": true}' > "$ONBOARDING"
fi
chmod 600 "$ONBOARDING"

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

exec python3 -m grafana_jsm_sandbox
