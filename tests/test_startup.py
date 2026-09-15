"""Starting the container's main process: the Receiver, its Forwarder, its spawner.

A misconfigured container that starts anyway and no-ops is the worst thing that
can happen during the demo, because nothing says so until an Alert fires and
nothing happens. These tests are the fail-fast: every variable that is missing
is named, and named all at once, before anything is listening.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from grafana_jsm_sandbox.__main__ import Settings, main
from grafana_jsm_sandbox.run_command import SKILL_FILE
from grafana_jsm_sandbox.run_spawner import ANTHROPIC_TOKEN_VARIABLE

COMPLETE = {
    "JIRA_SITE_URL": "https://example.atlassian.net",
    "JIRA_EMAIL": "ops@example.invalid",
    "JIRA_API_TOKEN": "a-real-token",
    ANTHROPIC_TOKEN_VARIABLE: "an-anthropic-oauth-token",
}


def complete_but(**overrides) -> dict[str, str]:
    """The complete environment with variables replaced, or removed when set to None."""
    environment = dict(COMPLETE, **overrides)
    return {name: value for name, value in environment.items() if value is not None}


def test_a_complete_environment_gives_the_receiver_everything_a_run_needs():
    settings = Settings.from_environment(COMPLETE)

    assert settings.credential.site_url == "https://example.atlassian.net"
    assert settings.credential.email == "ops@example.invalid"
    assert settings.credential.api_token == "a-real-token"
    assert settings.anthropic_token == "an-anthropic-oauth-token"


def test_the_skill_directory_defaults_to_the_one_in_this_repo():
    settings = Settings.from_environment(COMPLETE)

    assert (settings.skill_directory / SKILL_FILE).is_file()


def test_the_receiver_listens_where_the_container_expects_it_to():
    settings = Settings.from_environment(COMPLETE)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8080


def test_the_container_can_say_where_everything_lives(tmp_path):
    settings = Settings.from_environment(
        complete_but(
            RECEIVER_HOST="127.0.0.1",
            RECEIVER_PORT="9000",
            RUNS_DIRECTORY=str(tmp_path / "runs"),
            SKILL_DIRECTORY="/srv/skill",
            RUN_TIMEOUT="45",
        )
    )

    assert (settings.host, settings.port) == ("127.0.0.1", 9000)
    assert settings.runs_directory == tmp_path / "runs"
    assert settings.skill_directory == Path("/srv/skill")
    assert settings.run_timeout == 45


@pytest.mark.parametrize(
    "variable",
    ["JIRA_SITE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", ANTHROPIC_TOKEN_VARIABLE],
)
def test_startup_stops_and_names_a_missing_credential(variable, capsys):
    assert main([], environment=complete_but(**{variable: None})) == 1

    assert variable in capsys.readouterr().err


def test_startup_names_every_missing_credential_at_once(capsys):
    assert main([], environment={}) == 1

    said = capsys.readouterr().err
    for variable in COMPLETE:
        assert variable in said


def test_startup_stops_on_a_site_url_that_is_not_a_url(capsys):
    assert main([], environment=complete_but(JIRA_SITE_URL="example.atlassian.net")) == 1

    assert "JIRA_SITE_URL" in capsys.readouterr().err


def test_startup_stops_on_a_port_that_is_not_a_number(capsys):
    assert main([], environment=complete_but(RECEIVER_PORT="eight thousand")) == 1

    assert "RECEIVER_PORT" in capsys.readouterr().err


def test_startup_stops_on_a_timeout_that_is_not_a_number(capsys):
    assert main([], environment=complete_but(RUN_TIMEOUT="five minutes")) == 1

    assert "RUN_TIMEOUT" in capsys.readouterr().err


def test_startup_says_nothing_of_the_credential_it_could_not_read(capsys):
    """A container that fails to start still prints its log where an audience can see it."""
    main([], environment=complete_but(JIRA_EMAIL=None))

    assert "a-real-token" not in capsys.readouterr().err
