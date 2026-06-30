"""Unit tests for the gh-init pipeline."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from github import GithubException

from repo_scaffold import github_init
from repo_scaffold.cli import cli
from repo_scaffold.github_init import GhInitClient
from repo_scaffold.github_init import GhInitConfig
from repo_scaffold.github_init import build_config
from repo_scaffold.github_init import git_push
from repo_scaffold.github_init import init_repository
from repo_scaffold.github_init import parse_dotenv


def _write_pyproject(path: Path, *, name: str, description: str = "") -> None:
    path.write_text(
        f'[project]\nname = "{name}"\ndescription = "{description}"\n',
        encoding="utf-8",
    )


def test_parse_dotenv_handles_quotes_and_comments():
    """Parse honors quoted values, trims whitespace, and skips comments and bare lines."""
    text = """
# comment line
A=plain
B="quoted value"
C='single quoted'
   D=trimmed
EMPTY=
not-a-line-no-equals
"""
    assert parse_dotenv(text) == {
        "A": "plain",
        "B": "quoted value",
        "C": "single quoted",
        "D": "trimmed",
        "EMPTY": "",
    }


def test_build_config_pulls_defaults_from_pyproject(tmp_path):
    """Defaults flow from pyproject.toml when nothing is overridden."""
    _write_pyproject(tmp_path / "pyproject.toml", name="my-pkg", description="hello")
    config = build_config(tmp_path, extra_env={})

    assert config.name == "my-pkg"
    assert config.description == "hello"
    assert config.secrets == {}
    assert config.variables == {}
    assert config.default_branch in {"master", "main"}  # detect helper falls through to "master"
    assert config._skipped_secrets == [
        "PERSONAL_ACCESS_TOKEN",
        "PYPI_TOKEN",
        "PYPI_SERVER_USERNAME",
        "PYPI_SERVER_PASSWORD",
    ]


def test_build_config_resolves_secrets_from_env_then_dotenv(tmp_path):
    """Process env wins over .env; missing keys are dropped, not stored as empty."""
    _write_pyproject(tmp_path / "pyproject.toml", name="x")
    (tmp_path / ".env").write_text(
        "PYPI_TOKEN=from-dotenv\nPYPI_SERVER_USERNAME=from-dotenv-user\n",
        encoding="utf-8",
    )
    extra_env = {
        "PYPI_TOKEN": "from-process-env",
        "PUBLISH_TO_PUBLIC_PYPI": "true",
    }

    config = build_config(tmp_path, extra_env=extra_env)

    # Process env wins over .env.
    assert config.secrets["PYPI_TOKEN"] == "from-process-env"
    # Falls back to .env when env is absent.
    assert config.secrets["PYPI_SERVER_USERNAME"] == "from-dotenv-user"
    # Variables come through the same chain.
    assert config.variables == {"PUBLISH_TO_PUBLIC_PYPI": "true"}
    # Missing values are dropped, not stored as empty strings.
    assert "PERSONAL_ACCESS_TOKEN" not in config.secrets


def test_build_config_kwargs_take_precedence(tmp_path):
    """Explicit kwargs override env, dotenv, and pyproject defaults."""
    _write_pyproject(tmp_path / "pyproject.toml", name="from-pyproject")

    config = build_config(
        tmp_path,
        name="from-kwarg",
        description="from-kwarg-desc",
        owner="some-org",
        private=True,
        default_branch="main",
        extra_env={},
    )

    assert config.name == "from-kwarg"
    assert config.description == "from-kwarg-desc"
    assert config.owner == "some-org"
    assert config.private is True
    assert config.default_branch == "main"


def test_build_config_prompter_fills_missing_values(tmp_path):
    """The prompter callback supplies values not present in env/dotenv/pyproject."""
    _write_pyproject(tmp_path / "pyproject.toml", name="x")
    answers = {"PYPI_TOKEN": "prompted-token", "PUBLISH_TO_PUBLIC_PYPI": "true"}

    def prompter(key: str, default: str | None) -> str:
        return answers.get(key, "")

    config = build_config(tmp_path, extra_env={}, prompter=prompter)

    assert config.secrets == {"PYPI_TOKEN": "prompted-token"}
    assert config.variables == {"PUBLISH_TO_PUBLIC_PYPI": "true"}


def _make_config(tmp_path: Path, **overrides: Any) -> GhInitConfig:
    base: dict[str, Any] = {
        "project_path": tmp_path,
        "name": "demo",
        "description": "demo project",
        "private": False,
        "default_branch": "master",
        "secrets": {"PYPI_TOKEN": "token-value", "PERSONAL_ACCESS_TOKEN": "pat-value"},
        "variables": {"PUBLISH_TO_PUBLIC_PYPI": "true"},
        "owner": None,
        "push": False,
        "force_push": False,
        "allow_existing": False,
    }
    base.update(overrides)
    return GhInitConfig(**base)


def test_init_repository_calls_client_in_order(tmp_path):
    """Orchestrator calls login, repo creation, then secrets and variables in order."""
    config = _make_config(tmp_path)

    repo = MagicMock()
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.authenticated_login.return_value = "me"
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    client.authenticated_login.assert_called_once_with()
    client.get_or_create_repo.assert_called_once_with(
        None, "demo", description="demo project", private=False, allow_existing=False
    )
    # Both secrets are set, in iteration order of the dict.
    assert client.set_secret.call_args_list == [
        ((repo, "PYPI_TOKEN", "token-value"), {}),
        ((repo, "PERSONAL_ACCESS_TOKEN", "pat-value"), {}),
    ]
    assert client.set_variable.call_args_list == [((repo, "PUBLISH_TO_PUBLIC_PYPI", "true"), {})]
    assert result.html_url == "https://github.com/me/demo"
    assert result.actions_url == "https://github.com/me/demo/actions"
    assert result.pages_url == "https://me.github.io/demo"
    assert result.pushed is False


def test_init_repository_skips_push_when_disabled(tmp_path, monkeypatch):
    """git_push is not invoked when ``config.push`` is False."""
    config = _make_config(tmp_path, push=False)
    monkeypatch.setattr(github_init, "git_push", MagicMock(side_effect=AssertionError("should not push")))

    repo = MagicMock()
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    init_repository(config, client)


def test_init_repository_pushes_when_enabled(tmp_path, monkeypatch):
    """When push is enabled, git_push is called with the repo's clone URL and branch."""
    config = _make_config(tmp_path, push=True, force_push=True)
    pushed = MagicMock()
    monkeypatch.setattr(github_init, "git_push", pushed)

    repo = MagicMock()
    repo.clone_url = "https://github.com/me/demo.git"
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    pushed.assert_called_once_with(
        project_path=tmp_path,
        remote_url="https://github.com/me/demo.git",
        branch="master",
        force=True,
    )
    assert result.pushed is True


def test_get_or_create_repo_recovers_when_allow_existing(tmp_path):
    """A 422 from create_repo falls back to get_repo when allow_existing=True."""
    client = GhInitClient.__new__(GhInitClient)
    fake_user = MagicMock()
    fake_user.create_repo.side_effect = GithubException(status=422, data={"message": "exists"})
    fake_repo = MagicMock(name="existing-repo")

    fake_gh = MagicMock()
    fake_gh.get_user.return_value = fake_user
    fake_gh.get_repo.return_value = fake_repo
    client._gh = fake_gh
    client._user_login = "me"

    repo = client.get_or_create_repo(None, "demo", description="", private=False, allow_existing=True)
    assert repo is fake_repo
    fake_gh.get_repo.assert_called_once_with("me/demo")


def test_get_or_create_repo_reraises_without_allow_existing(tmp_path):
    """Without allow_existing the 422 propagates so the caller sees the conflict."""
    client = GhInitClient.__new__(GhInitClient)
    fake_user = MagicMock()
    fake_user.create_repo.side_effect = GithubException(status=422, data={"message": "exists"})
    fake_gh = MagicMock()
    fake_gh.get_user.return_value = fake_user
    client._gh = fake_gh
    client._user_login = "me"

    with pytest.raises(GithubException):
        client.get_or_create_repo(None, "demo", description="", private=False, allow_existing=False)


def test_set_variable_falls_back_to_edit_on_conflict():
    """A 422/409 from create_variable triggers an edit on the existing variable."""
    client = GhInitClient.__new__(GhInitClient)
    repo = MagicMock()
    repo.create_variable.side_effect = GithubException(status=422, data={"message": "exists"})

    client.set_variable(repo, "PUBLISH_TO_PUBLIC_PYPI", "true")

    repo.create_variable.assert_called_once_with("PUBLISH_TO_PUBLIC_PYPI", "true")
    repo.get_variable.assert_called_once_with("PUBLISH_TO_PUBLIC_PYPI")
    repo.get_variable.return_value.edit.assert_called_once_with(value="true")


def test_set_variable_reraises_on_other_errors():
    """Any non-conflict GitHub error propagates instead of being swallowed."""
    client = GhInitClient.__new__(GhInitClient)
    repo = MagicMock()
    repo.create_variable.side_effect = GithubException(status=500, data={"message": "boom"})

    with pytest.raises(GithubException):
        client.set_variable(repo, "X", "Y")


def test_cli_gh_init_requires_token(tmp_path, monkeypatch):
    """gh-init exits non-zero with a clear message when GITHUB_TOKEN is missing."""
    _write_pyproject(tmp_path / "pyproject.toml", name="x")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    result = CliRunner().invoke(cli, ["gh-init", str(tmp_path), "--no-input"])

    assert result.exit_code != 0
    assert "GITHUB_TOKEN" in result.output


def test_cli_gh_init_invokes_orchestrator(tmp_path, monkeypatch):
    """The CLI builds a config, constructs the client, and prints the result URLs."""
    _write_pyproject(tmp_path / "pyproject.toml", name="demo", description="d")
    monkeypatch.setenv("GITHUB_TOKEN", "stub")
    captured = {}

    class StubClient:
        def __init__(self, token: str):
            captured["token"] = token

    def fake_init(config, client):
        captured["config"] = config
        captured["client"] = client
        return github_init.GhInitResult(
            html_url="https://github.com/me/demo",
            actions_url="https://github.com/me/demo/actions",
            pages_url="https://me.github.io/demo",
            skipped_secrets=["PYPI_TOKEN"],
            pushed=True,
        )

    monkeypatch.setattr("repo_scaffold.cli.GhInitClient", StubClient)
    monkeypatch.setattr("repo_scaffold.cli.init_repository", fake_init)

    result = CliRunner().invoke(
        cli,
        ["gh-init", str(tmp_path), "--no-input", "--no-push"],
    )

    assert result.exit_code == 0, result.output
    assert captured["token"] == "stub"
    assert captured["config"].name == "demo"
    assert captured["config"].push is False
    assert "Repository ready" in result.output
    assert "Skipped secrets" in result.output


def _record_calls(monkeypatch, *, head_exists: bool = False):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        rc = 0
        # Probe for HEAD: returncode 1 simulates no commits yet; 0 means HEAD exists.
        if "rev-parse" in cmd and "HEAD" in cmd:
            rc = 0 if head_exists else 1
        return subprocess.CompletedProcess(cmd, rc, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def test_git_push_initializes_and_pushes(tmp_path, monkeypatch):
    """git_push runs init, add, commit, branch -M, remote add, and push -u in order."""
    calls = _record_calls(monkeypatch, head_exists=False)
    git_push(tmp_path, "git@github.com:me/demo.git", branch="master", force=False)

    flat = [" ".join(c) for c in calls]
    assert any(c.startswith("git init ") for c in flat)
    assert any(c.endswith("add -A") for c in flat)
    assert any("commit" in c and INITIAL_COMMIT_MESSAGE in c for c in flat)
    assert any("branch -M master" in c for c in flat)
    assert any("remote add origin git@github.com:me/demo.git" in c for c in flat)
    assert any(c.endswith("push -u origin master") for c in flat)


def test_git_push_force_flag_added(tmp_path, monkeypatch):
    """``--force-push`` adds ``--force`` to the final ``git push`` invocation."""
    calls = _record_calls(monkeypatch, head_exists=False)
    git_push(tmp_path, "url", branch="main", force=True)

    flat = [" ".join(c) for c in calls]
    assert any(c.endswith("push -u --force origin main") for c in flat)


def test_git_push_skips_commit_when_head_exists(tmp_path, monkeypatch):
    """When HEAD already exists, git_push does not stage or commit again."""
    calls = _record_calls(monkeypatch, head_exists=True)
    (tmp_path / ".git").mkdir()  # skip git init step
    git_push(tmp_path, "url", branch="master", force=False)

    # Inspect tokens, not stringified commands, so the "commit" token in
    # `INITIAL_COMMIT_MESSAGE` doesn't trigger a false positive.
    assert not any("add" in c and "-A" in c for c in calls)
    assert not any("commit" in c for c in calls)


# Constant under test, kept local to avoid importing internal name into tests.
INITIAL_COMMIT_MESSAGE = "chore: initial commit from repo-scaffold [skip ci]"
