# The demo container: the Receiver is its main process, and a Run is a child of that.
#
# It extends the claude-devcontainer image already on this machine, which brings
# Claude Code, Python and a non-root `devuser`. What this adds is the three things
# a Run needs and nothing else: a current Claude Code, jira-as, and the skill.
#
# No bubblewrap, no sandbox package, no Docker socket. The boundary a Run runs
# inside is the permission mode it is started with (ADR 0003) and the sentinel in
# its environment (ADR 0002), not anything installed here.
#
#     docker compose build

ARG BASE_IMAGE=grandcamel/claude-devcontainer:latest
FROM ${BASE_IMAGE}

ARG CLAUDE_CODE_VERSION=2.1.272
ARG JIRA_AS_VERSION=2.0.0

USER root

# The base image's Claude Code is eight months old. A Run's Transcript is what the
# audience reads and the formatter renders its event shapes, so this is pinned to
# the version the container was rehearsed on rather than left to drift.
RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
    && npm cache clean --force

# /app is the Receiver's home and the parent of every Run's working directory, so
# it belongs to the user the Receiver runs as.
RUN mkdir -p /app/runs && chown -R devuser:node /app

USER devuser

# The only thing a Run may execute. Pinned, because the skill is written in its
# invocations and was verified against this version.
RUN pip3 install --no-cache-dir "jira-as==${JIRA_AS_VERSION}"

WORKDIR /app
COPY --chown=devuser:node grafana_jsm_sandbox/ /app/grafana_jsm_sandbox/
COPY --chown=devuser:node skill/ /app/skill/
COPY --chown=devuser:node docker/entrypoint.sh /app/entrypoint.sh

# Where this container keeps the two directories the Receiver is told about. The
# credentials are not here and are not in the image: compose hands them in from an
# env file that git and the build context both refuse.
ENV SKILL_DIRECTORY=/app/skill \
    RUNS_DIRECTORY=/app/runs \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
