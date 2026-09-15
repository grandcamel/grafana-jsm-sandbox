"""The one setting that names the Jira project a Run acts on.

The Skill is written for one project key, in full, because every invocation in
it must be runnable as written and readable off a screen during the demo. A
demo against another site's project, on a laptop that is not the one the Skill
was written on, sets `JIRA_PROJECT` and nothing else: the reset and the
end-to-end check read it, and the Receiver renders the Skill for it once at
startup into a copy the Runs read instead of the committed one.
"""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Mapping
from pathlib import Path

PROJECT_VARIABLE = "JIRA_PROJECT"
"""The project key, on the laptop and in the container. Unset, it is the Skill's own."""

DEFAULT_PROJECT = "OPS"
"""The project the committed Skill is written for, so that key is a no-op to configure."""

ALLOWED_PROJECTS_VARIABLE = "JIRA_ALLOWED_PROJECTS"
"""What jira-as reads as its project allowlist, over whatever a settings file says. Set to
the one configured project wherever this repo runs jira-as, so nothing here can reach
another project by mistake, whichever tree it was started in."""

PROJECT_KEY = re.compile(r"[A-Z][A-Z0-9_]*")
"""Jira's shape for a project key: uppercase, a letter first. Anything else would fail
later, inside a Run, in JQL a Run would have to explain."""


class InvalidProjectKey(ValueError):
    """The environment names something that is not a Jira project key."""


def project_from_environment(environment: Mapping[str, str] | None = None) -> str:
    """The configured project key, or the Skill's own when nothing is set."""
    environment = os.environ if environment is None else environment
    key = environment.get(PROJECT_VARIABLE, "").strip()
    if not key:
        return DEFAULT_PROJECT
    if PROJECT_KEY.fullmatch(key) is None:
        raise InvalidProjectKey(
            f"{PROJECT_VARIABLE} is not a Jira project key: {key!r} "
            "(uppercase letters, digits and underscores, starting with a letter)"
        )
    return key


def render_skill(source: Path, project: str, destination: Path) -> Path:
    """A copy of the skill directory with the Skill's project key rewritten to `project`.

    Only whole occurrences of the key are touched, so `OPS` inside another word or
    key stays. Everything else in the copy is byte for byte the committed text, which
    is the point: what a Run reads for another project is the Skill, not a variant.
    """
    shutil.copytree(source, destination)
    written_for = re.compile(rf"\b{re.escape(DEFAULT_PROJECT)}\b")
    for markdown in destination.rglob("*.md"):
        markdown.write_text(written_for.sub(project, markdown.read_text()))
    return destination
