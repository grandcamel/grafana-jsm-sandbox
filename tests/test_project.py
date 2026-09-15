"""The one setting that names the Jira project a Run acts on.

The Skill is static text copied into the image and written for one project key,
because every invocation in it must be runnable as written and readable off a
screen. A demo against another site's project keeps that text and rewrites the
key once, at startup, into a copy the Runs read instead.
"""

from __future__ import annotations

import re

import pytest

from grafana_jsm_sandbox.project import (
    DEFAULT_PROJECT,
    PROJECT_VARIABLE,
    InvalidProjectKey,
    project_from_environment,
    project_from_shell,
    render_skill,
)
from grafana_jsm_sandbox.run_command import SKILL_FILE
from tests.conftest import REPOSITORY

COMMITTED_SKILL = REPOSITORY / "skill"


def test_the_project_is_ops_unless_the_environment_says_otherwise():
    assert project_from_environment({}) == "OPS"
    assert project_from_environment({PROJECT_VARIABLE: "SIEM"}) == "SIEM"
    assert project_from_environment({PROJECT_VARIABLE: "  SIEM \n"}) == "SIEM"
    assert project_from_environment({PROJECT_VARIABLE: ""}) == DEFAULT_PROJECT


@pytest.mark.parametrize("key", ["siem", "siem-staging", "1OPS", "OPS SIEM", "project = OPS"])
def test_anything_that_is_not_a_jira_project_key_is_refused_by_name(key):
    with pytest.raises(InvalidProjectKey) as refusal:
        project_from_environment({PROJECT_VARIABLE: key})
    assert PROJECT_VARIABLE in str(refusal.value)
    assert key in str(refusal.value)


def test_the_committed_skill_is_written_for_the_default_project():
    """What makes the default a no-op: the text a Run reads already names it."""
    skill = (COMMITTED_SKILL / SKILL_FILE).read_text()

    assert f"| Project | `{DEFAULT_PROJECT}` |" in skill


def test_a_rendered_skill_names_the_other_project_everywhere_a_run_would_type_it(tmp_path):
    rendered = render_skill(COMMITTED_SKILL, "SIEM", tmp_path / "rendered")
    skill = (rendered / SKILL_FILE).read_text()

    assert "| Project | `SIEM` |" in skill
    assert "project = SIEM AND issuetype = Incident" in skill
    assert "jira-as issue create -p SIEM -t Incident" in skill
    assert "getProjectComponents --projectIdOrKey SIEM" in skill
    assert re.search(r"\bOPS\b", skill) is None


def test_rendering_changes_nothing_but_the_key(tmp_path):
    rendered = render_skill(COMMITTED_SKILL, "SIEM", tmp_path / "rendered")
    original = (COMMITTED_SKILL / SKILL_FILE).read_text()
    skill = (rendered / SKILL_FILE).read_text()

    assert skill.replace("SIEM", "OPS") == original
    assert (COMMITTED_SKILL / SKILL_FILE).read_text() == original, "the committed file is untouched"


def test_the_rendered_directory_has_the_skills_shape(tmp_path):
    """The Run is pointed at the copy the way it is pointed at the original."""
    rendered = render_skill(COMMITTED_SKILL, "SIEM", tmp_path / "rendered")

    assert rendered == tmp_path / "rendered"
    assert (rendered / SKILL_FILE).is_file()
    assert sorted(p.relative_to(rendered) for p in rendered.rglob("*")) == sorted(
        p.relative_to(COMMITTED_SKILL) for p in COMMITTED_SKILL.rglob("*")
    )


def test_the_key_a_run_types_is_the_key_that_was_configured(tmp_path):
    """A key that is a prefix of another must not bleed: `OPS` inside a word stays."""
    source = tmp_path / "skill" / "incident-sync"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("project = OPS, OPSEC, OPS-12, `OPS`\n")

    rendered = render_skill(tmp_path / "skill", "SIEM", tmp_path / "rendered")

    assert (rendered / "incident-sync" / "SKILL.md").read_text() == (
        "project = SIEM, OPSEC, SIEM-12, `SIEM`\n"
    )


def test_the_laptop_side_tools_read_the_project_the_container_was_started_for(tmp_path):
    """The reset and the end-to-end check act on what `.env` names, which is what the
    container read, unless the shell says otherwise; so the key is set in one place."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# the demo's credentials\nJIRA_SITE_URL=https://x.atlassian.net\nJIRA_PROJECT=SIEM\n"
    )

    assert project_from_shell({}, env_file) == "SIEM"
    assert project_from_shell({PROJECT_VARIABLE: "OPS"}, env_file) == "OPS"
    assert project_from_shell({}, tmp_path / "no-such-file") == DEFAULT_PROJECT


def test_a_commented_out_project_in_the_env_file_is_the_default(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# JIRA_PROJECT=SIEM\nJIRA_PROJECT = \n")

    assert project_from_shell({}, env_file) == DEFAULT_PROJECT


def test_the_env_files_project_is_held_to_the_same_shape(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("JIRA_PROJECT=siem\n")

    with pytest.raises(InvalidProjectKey):
        project_from_shell({}, env_file)
