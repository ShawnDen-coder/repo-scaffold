"""Unit tests for the gh-init pipeline."""

from __future__ import annotations

import base64
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


def test_build_config_setup_pages_defaults_true(tmp_path):
    """setup_pages defaults to True (and protect_branch to False); both overridable."""
    _write_pyproject(tmp_path / "pyproject.toml", name="x")
    default = build_config(tmp_path, extra_env={})
    assert default.setup_pages is True
    assert default.protect_branch is False
    assert build_config(tmp_path, extra_env={}, setup_pages=False).setup_pages is False
    assert build_config(tmp_path, extra_env={}, protect_branch=True).protect_branch is True


def test_detect_owner_from_pyproject_urls(tmp_path):
    """Owner is read from a github.com URL in [project.urls]."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[project.urls]\nRepository = "https://github.com/my-org/x"\n',
        encoding="utf-8",
    )
    assert github_init.detect_owner(tmp_path) == ("my-org", "pyproject")


def test_detect_owner_falls_back_to_cog(tmp_path):
    """Without pyproject URLs, owner comes from cog.toml [changelog].owner."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    (tmp_path / "cog.toml").write_text('[changelog]\nowner = "cog-org"\nrepository = "x"\n', encoding="utf-8")
    assert github_init.detect_owner(tmp_path) == ("cog-org", "cog.toml")


def test_detect_owner_none_when_absent(tmp_path):
    """No URL and no cog.toml yields no detected owner."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert github_init.detect_owner(tmp_path) == (None, None)


def test_build_config_resolves_owner_from_project(tmp_path):
    """build_config picks up the detected owner and records its source."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[project.urls]\nHomepage = "https://github.com/auto-org/x"\n',
        encoding="utf-8",
    )
    config = build_config(tmp_path, extra_env={})
    assert config.owner == "auto-org"
    assert config._owner_source == "pyproject"


def test_build_config_explicit_owner_wins_over_detection(tmp_path):
    """An explicit --owner overrides any detected owner."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[project.urls]\nHomepage = "https://github.com/auto-org/x"\n',
        encoding="utf-8",
    )
    config = build_config(tmp_path, owner="flag-org", extra_env={})
    assert config.owner == "flag-org"
    assert config._owner_source == "flag"


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
        token=client.token,
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


def test_set_homepage_edits_repo():
    """set_homepage points the repo Website field at the docs URL."""
    client = GhInitClient.__new__(GhInitClient)
    repo = MagicMock()

    client.set_homepage(repo, "https://me.github.io/demo")

    repo.edit.assert_called_once_with(homepage="https://me.github.io/demo")


def test_deploy_docs_runs_just_recipe(tmp_path, monkeypatch):
    """deploy_docs shells out to the project's deploy-gh-pages just recipe."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((list(cmd), kwargs.get("cwd")))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    github_init.deploy_docs(tmp_path)

    assert calls == [(["uvx", "--from", "rust-just", "just", "deploy-gh-pages"], str(tmp_path))]


def test_deploy_docs_raises_runtime_error_on_failure(tmp_path, monkeypatch):
    """A non-zero mkdocs gh-deploy surfaces as a RuntimeError with the stderr tail."""

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, output="", stderr="boom: build failed")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="gh-deploy"):
        github_init.deploy_docs(tmp_path)


def test_deploy_docs_passes_token_in_env(tmp_path, monkeypatch):
    """With a token, deploy_docs injects the PAT into the subprocess env.

    ``mkdocs gh-deploy`` shells out to ``git push`` itself, so the PAT is passed
    as an ``http.extraheader`` ``Authorization: Basic`` header via
    ``GIT_CONFIG_PARAMETERS`` (and the terminal prompt is disabled) rather than
    being written to ``.git/config``.
    """
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    github_init.deploy_docs(tmp_path, token="test")

    env = captured["env"]
    assert env is not None
    expected_creds = base64.b64encode(b"x-access-token:test").decode()
    assert env["GIT_CONFIG_PARAMETERS"] == f"'http.extraheader=Authorization: Basic {expected_creds}'"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    # The existing environment is preserved alongside the injected entries.
    assert "PATH" in env


def test_deploy_docs_omits_env_without_token(tmp_path, monkeypatch):
    """Without a token, deploy_docs passes no custom env (lets git auth itself)."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    github_init.deploy_docs(tmp_path)

    assert captured["env"] is None


def test_enable_pages_creates_site():
    """enable_pages POSTs the source config to the Pages endpoint."""
    client = GhInitClient.__new__(GhInitClient)
    repo = MagicMock()
    repo.url = "https://api.github.com/repos/me/demo"

    client.enable_pages(repo, "gh-pages")

    repo.requester.requestJsonAndCheck.assert_called_once_with(
        "POST",
        "https://api.github.com/repos/me/demo/pages",
        input={"source": {"branch": "gh-pages", "path": "/"}},
    )


def test_enable_pages_updates_on_conflict():
    """When a Pages site already exists, enable_pages falls back to a PUT update."""
    client = GhInitClient.__new__(GhInitClient)
    repo = MagicMock()
    repo.url = "https://api.github.com/repos/me/demo"
    repo.requester.requestJsonAndCheck.side_effect = [
        GithubException(status=409, data={"message": "exists"}),
        (None, None),
    ]

    client.enable_pages(repo, "gh-pages")

    assert repo.requester.requestJsonAndCheck.call_count == 2
    assert repo.requester.requestJsonAndCheck.call_args_list[1][0][0] == "PUT"


def test_init_repository_configures_pages_after_push(tmp_path, monkeypatch):
    """With push + setup_pages + a docs site, gh-init deploys docs, enables Pages, sets homepage."""
    (tmp_path / "mkdocs.yml").write_text("site_name: demo\n", encoding="utf-8")
    config = _make_config(tmp_path, push=True, setup_pages=True)
    monkeypatch.setattr(github_init, "git_push", MagicMock())
    deploy = MagicMock()
    monkeypatch.setattr(github_init, "deploy_docs", deploy)

    repo = MagicMock()
    repo.clone_url = "https://github.com/me/demo.git"
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    deploy.assert_called_once_with(tmp_path, token=client.token)
    client.enable_pages.assert_called_once_with(repo, "gh-pages")
    client.set_homepage.assert_called_once_with(repo, "https://me.github.io/demo")
    assert result.pages_configured is True
    assert result.homepage_set is True
    assert result.pages_branch == "gh-pages"


def test_init_repository_skips_pages_without_push(tmp_path, monkeypatch):
    """Pages setup is skipped when nothing was pushed (no remote branch to deploy)."""
    (tmp_path / "mkdocs.yml").write_text("site_name: demo\n", encoding="utf-8")
    config = _make_config(tmp_path, push=False, setup_pages=True)
    deploy = MagicMock()
    monkeypatch.setattr(github_init, "deploy_docs", deploy)

    repo = MagicMock()
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    deploy.assert_not_called()
    client.enable_pages.assert_not_called()
    assert result.pages_configured is False


def test_init_repository_skips_pages_without_docs(tmp_path, monkeypatch):
    """Pages setup is skipped when the project has no mkdocs.yml."""
    config = _make_config(tmp_path, push=True, setup_pages=True)
    monkeypatch.setattr(github_init, "git_push", MagicMock())
    deploy = MagicMock()
    monkeypatch.setattr(github_init, "deploy_docs", deploy)

    repo = MagicMock()
    repo.clone_url = "https://github.com/me/demo.git"
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    deploy.assert_not_called()
    client.enable_pages.assert_not_called()
    assert result.pages_configured is False


def test_init_repository_records_pages_error_without_aborting(tmp_path, monkeypatch):
    """A docs-deploy failure is recorded but does not abort the bootstrap."""
    (tmp_path / "mkdocs.yml").write_text("site_name: demo\n", encoding="utf-8")
    config = _make_config(tmp_path, push=True, setup_pages=True)
    monkeypatch.setattr(github_init, "git_push", MagicMock())
    deploy = MagicMock(side_effect=RuntimeError("mkdocs gh-deploy failed: boom"))
    monkeypatch.setattr(github_init, "deploy_docs", deploy)

    repo = MagicMock()
    repo.clone_url = "https://github.com/me/demo.git"
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    assert result.pages_configured is False
    assert "boom" in result.pages_error
    client.enable_pages.assert_not_called()


def test_protect_branch_calls_edit_protection():
    """protect_branch applies release-compatible rules (enforce_admins off)."""
    client = GhInitClient.__new__(GhInitClient)
    repo = MagicMock()
    branch = repo.get_branch.return_value

    client.protect_branch(repo, "master")

    repo.get_branch.assert_called_once_with("master")
    branch.edit_protection.assert_called_once_with(
        required_approving_review_count=1,
        enforce_admins=False,
        allow_force_pushes=False,
        allow_deletions=False,
    )


def test_init_repository_protects_branch_when_enabled(tmp_path, monkeypatch):
    """With push + protect_branch, the default branch is protected."""
    config = _make_config(tmp_path, push=True, setup_pages=False, protect_branch=True)
    monkeypatch.setattr(github_init, "git_push", MagicMock())

    repo = MagicMock()
    repo.clone_url = "https://github.com/me/demo.git"
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    client.protect_branch.assert_called_once_with(repo, "master")
    assert result.branch_protected is True


def test_init_repository_skips_protection_without_push(tmp_path):
    """Branch protection is skipped when nothing was pushed."""
    config = _make_config(tmp_path, push=False, protect_branch=True)

    repo = MagicMock()
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo

    result = init_repository(config, client)

    client.protect_branch.assert_not_called()
    assert result.branch_protected is False


def test_init_repository_records_protection_error_without_aborting(tmp_path, monkeypatch):
    """A protection failure (e.g. private repo on a free plan) is non-fatal."""
    config = _make_config(tmp_path, push=True, setup_pages=False, protect_branch=True)
    monkeypatch.setattr(github_init, "git_push", MagicMock())

    repo = MagicMock()
    repo.clone_url = "https://github.com/me/demo.git"
    repo.html_url = "https://github.com/me/demo"
    repo.name = "demo"
    repo.owner.login = "me"

    client = MagicMock(spec=GhInitClient)
    client.get_or_create_repo.return_value = repo
    client.protect_branch.side_effect = GithubException(
        status=403, data={"message": "Upgrade to GitHub Pro for private branch protection"}
    )

    result = init_repository(config, client)

    assert result.branch_protected is False
    assert "Upgrade" in result.protection_error


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


def test_cli_gh_init_no_pages_disables_pages(tmp_path, monkeypatch):
    """``--no-pages`` resolves a config with setup_pages disabled."""
    _write_pyproject(tmp_path / "pyproject.toml", name="demo")
    monkeypatch.setenv("GITHUB_TOKEN", "stub")
    captured = {}

    class StubClient:
        def __init__(self, token: str):
            pass

    def fake_init(config, client):
        captured["config"] = config
        return github_init.GhInitResult(
            html_url="https://github.com/me/demo",
            actions_url="https://github.com/me/demo/actions",
            pages_url="https://me.github.io/demo",
            skipped_secrets=[],
            pushed=False,
        )

    monkeypatch.setattr("repo_scaffold.cli.GhInitClient", StubClient)
    monkeypatch.setattr("repo_scaffold.cli.init_repository", fake_init)

    result = CliRunner().invoke(
        cli,
        ["gh-init", str(tmp_path), "--no-input", "--no-push", "--no-pages"],
    )

    assert result.exit_code == 0, result.output
    assert captured["config"].setup_pages is False


def test_cli_gh_init_protect_branch_flag(tmp_path, monkeypatch):
    """``--protect-branch`` resolves a config with protect_branch enabled."""
    _write_pyproject(tmp_path / "pyproject.toml", name="demo")
    monkeypatch.setenv("GITHUB_TOKEN", "stub")
    captured = {}

    class StubClient:
        def __init__(self, token: str):
            pass

    def fake_init(config, client):
        captured["config"] = config
        return github_init.GhInitResult(
            html_url="https://github.com/me/demo",
            actions_url="https://github.com/me/demo/actions",
            pages_url="https://me.github.io/demo",
            skipped_secrets=[],
            pushed=True,
            branch_protected=True,
        )

    monkeypatch.setattr("repo_scaffold.cli.GhInitClient", StubClient)
    monkeypatch.setattr("repo_scaffold.cli.init_repository", fake_init)

    result = CliRunner().invoke(
        cli,
        ["gh-init", str(tmp_path), "--no-input", "--no-push", "--protect-branch"],
    )

    assert result.exit_code == 0, result.output
    assert captured["config"].protect_branch is True
    assert "Protected branch" in result.output


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


def test_git_push_embeds_token_in_extraheader(tmp_path, monkeypatch):
    """With a token, git_push authenticates the push via a one-shot http.extraheader.

    The remote URL stays clean (no embedded creds, so the token never lands in
    .git/config); the PAT is sent as an Authorization: Basic header through
    `-c` on the push command itself.
    """
    calls = _record_calls(monkeypatch, head_exists=False)
    git_push(tmp_path, "https://github.com/me/demo.git", branch="master", force=False, token="test")

    expected_creds = base64.b64encode(b"x-access-token:test").decode()
    push_calls = [" ".join(c) for c in calls if "push" in c]
    assert any(f"http.extraheader=Authorization: Basic {expected_creds}" in c for c in push_calls)
    # Remote is added against the clean URL (token not embedded).
    assert any("remote add origin https://github.com/me/demo.git" in " ".join(c) for c in calls)
    assert any(c.endswith("push -u origin master") for c in push_calls)


def test_git_push_omits_extraheader_without_token(tmp_path, monkeypatch):
    """Without a token, git_push pushes plainly (lets SSH / credential helpers work)."""
    calls = _record_calls(monkeypatch, head_exists=False)
    git_push(tmp_path, "git@github.com:me/demo.git", branch="master", force=False)

    push_calls = [" ".join(c) for c in calls if "push" in c]
    assert any(c.endswith("push -u origin master") for c in push_calls)
    assert not any("extraheader" in c for c in push_calls)


# Constant under test, kept local to avoid importing internal name into tests.
INITIAL_COMMIT_MESSAGE = "chore: initial commit from repo-scaffold [skip ci]"
