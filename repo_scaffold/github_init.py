"""GitHub bootstrap helpers for `repo-scaffold gh-init`.

Three layers:

- ``GhInitConfig`` and ``build_config`` collect the repo metadata, secrets,
  and variables to apply.
- ``GhInitClient`` is a thin wrapper around PyGithub so tests can swap the
  whole client out without monkey-patching the SDK.
- ``init_repository`` orchestrates the calls and returns the URLs the CLI
  prints back to the user.

A ``git_push`` helper performs the optional initial commit + push via
subprocess, no extra dependency on GitPython.
"""

from __future__ import annotations

import os
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from github import Auth
from github import Github
from github import GithubException
from github.Repository import Repository


DEFAULT_SECRET_KEYS: tuple[str, ...] = (
    "PERSONAL_ACCESS_TOKEN",
    "PYPI_TOKEN",
    "PYPI_SERVER_USERNAME",
    "PYPI_SERVER_PASSWORD",
)

DEFAULT_VARIABLE_KEYS: tuple[str, ...] = ("PUBLISH_TO_PUBLIC_PYPI",)

# Branch the generated docs-deploy workflow (mkdocs gh-deploy) publishes to,
# and which GitHub Pages is configured to serve from.
PAGES_BRANCH = "gh-pages"

# GitHub Actions recognizes this marker in commit messages and skips
# workflows for the bootstrap push. Later user commits are not modified.
INITIAL_COMMIT_MESSAGE = "chore: initial commit from repo-scaffold [skip ci]"
INITIAL_COMMIT_USER = "repo-scaffold"
INITIAL_COMMIT_EMAIL = "repo-scaffold@users.noreply.github.com"


@dataclass
class GhInitConfig:
    """Resolved configuration for one ``gh-init`` invocation."""

    project_path: Path
    name: str
    description: str
    private: bool
    default_branch: str
    secrets: dict[str, str] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    owner: str | None = None
    push: bool = True
    force_push: bool = False
    allow_existing: bool = False
    setup_pages: bool = True


@dataclass
class GhInitResult:
    """Outputs surfaced to the CLI after a successful run."""

    html_url: str
    actions_url: str
    pages_url: str
    skipped_secrets: list[str]
    pushed: bool
    pages_configured: bool = False
    pages_branch: str = PAGES_BRANCH
    pages_error: str | None = None


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse a tiny subset of dotenv syntax: ``KEY=VALUE`` lines, ``#`` comments.

    Quoted values are unquoted. Anything more exotic (export, multiline, command
    substitution) is intentionally not supported — projects that need that should
    set real env vars before running gh-init.
    """
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def load_pyproject(project_path: Path) -> dict[str, Any]:
    """Return the ``[project]`` table from the project's ``pyproject.toml``."""
    pyproject = project_path / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}) or {}


def detect_default_branch(project_path: Path) -> str | None:
    """Return the current local git branch name, or ``None`` if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "branch", "--show-current"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    branch = result.stdout.strip()
    return branch or None


def build_config(
    project_path: Path,
    *,
    owner: str | None = None,
    name: str | None = None,
    description: str | None = None,
    private: bool = False,
    default_branch: str | None = None,
    push: bool = True,
    force_push: bool = False,
    allow_existing: bool = False,
    setup_pages: bool = True,
    extra_env: dict[str, str] | None = None,
    prompter: Callable[[str, str | None], str] | None = None,
) -> GhInitConfig:
    """Resolve a ``GhInitConfig`` from CLI args, environment, ``.env``, and pyproject.

    Precedence per key (highest first): explicit kwarg, ``extra_env`` (used for
    secrets/variables and for pulling values from ``os.environ`` at the call
    site), then the project's ``.env`` file, then ``pyproject.toml`` defaults,
    then ``prompter`` if provided.

    ``prompter`` receives ``(key, default)`` and returns the user's answer, or
    an empty string to skip. When ``prompter`` is ``None`` (i.e. ``--no-input``)
    missing optional values are simply dropped.
    """
    project_path = project_path.resolve()
    pyproject = load_pyproject(project_path)
    dotenv_path = project_path / ".env"
    dotenv = parse_dotenv(dotenv_path.read_text(encoding="utf-8")) if dotenv_path.is_file() else {}
    env = extra_env if extra_env is not None else dict(os.environ)

    def from_env(key: str) -> str:
        return env.get(key) or dotenv.get(key) or ""

    resolved_name = name or pyproject.get("name") or project_path.name
    resolved_description = description if description is not None else pyproject.get("description") or ""
    resolved_branch = default_branch or detect_default_branch(project_path) or "master"

    secrets: dict[str, str] = {}
    skipped: list[str] = []
    for key in DEFAULT_SECRET_KEYS:
        value = from_env(key)
        if not value and prompter is not None:
            value = prompter(key, None)
        if value:
            secrets[key] = value
        else:
            skipped.append(key)

    variables: dict[str, str] = {}
    for key in DEFAULT_VARIABLE_KEYS:
        value = from_env(key)
        if not value and prompter is not None:
            value = prompter(key, "false")
        if value:
            variables[key] = value

    config = GhInitConfig(
        project_path=project_path,
        name=resolved_name,
        description=resolved_description,
        private=private,
        default_branch=resolved_branch,
        secrets=secrets,
        variables=variables,
        owner=owner,
        push=push,
        force_push=force_push,
        allow_existing=allow_existing,
        setup_pages=setup_pages,
    )
    config._skipped_secrets = skipped  # type: ignore[attr-defined]
    return config


class GhInitClient:
    """Tiny PyGithub wrapper that orchestrator and tests both consume."""

    def __init__(self, token: str):
        """Construct a client backed by the given personal access token."""
        self._gh = Github(auth=Auth.Token(token))
        self._user_login: str | None = None

    def authenticated_login(self) -> str:
        """Return the login of the token's user. Raises on a bad token."""
        if self._user_login is None:
            self._user_login = self._gh.get_user().login
        return self._user_login

    def get_or_create_repo(
        self,
        owner: str | None,
        name: str,
        *,
        description: str,
        private: bool,
        allow_existing: bool,
    ) -> Repository:
        """Create the repo on the right account, or look it up if already there."""
        login = self.authenticated_login()
        target_owner = owner or login
        try:
            if not owner or owner == login:
                user = self._gh.get_user()
                return user.create_repo(
                    name=name,
                    description=description or "",
                    private=private,
                    auto_init=False,
                )
            org = self._gh.get_organization(owner)
            return org.create_repo(
                name=name,
                description=description or "",
                private=private,
                auto_init=False,
            )
        except GithubException as exc:
            if exc.status == 422 and allow_existing:
                return self._gh.get_repo(f"{target_owner}/{name}")
            raise

    def set_secret(self, repo: Repository, name: str, value: str) -> None:
        """Create or replace an Actions secret. ``create_secret`` is PUT-based."""
        repo.create_secret(name, value)

    def set_variable(self, repo: Repository, name: str, value: str) -> None:
        """Create an Actions variable, falling back to ``edit`` if it exists."""
        try:
            repo.create_variable(name, value)
        except GithubException as exc:
            if exc.status in (409, 422):
                repo.get_variable(name).edit(value=value)
                return
            raise

    def ensure_branch(self, repo: Repository, branch: str, base_branch: str) -> bool:
        """Create ``branch`` from ``base_branch``'s head if it doesn't exist yet.

        Returns ``True`` when a new branch was created, ``False`` when it was
        already present. Requires ``base_branch`` to exist on the remote (i.e.
        the initial commit has been pushed).
        """
        try:
            repo.get_branch(branch)
            return False
        except GithubException as exc:
            if exc.status != 404:
                raise

        base_sha = repo.get_branch(base_branch).commit.sha
        repo.create_git_ref(f"refs/heads/{branch}", base_sha)
        return True

    def enable_pages(self, repo: Repository, branch: str, path: str = "/") -> None:
        """Configure GitHub Pages to deploy from ``branch``/``path``.

        PyGithub 2.x has no Pages helper, so this calls the REST API directly:
        ``POST .../pages`` to create the site, falling back to ``PUT`` to update
        the source when a site already exists.
        """
        source = {"branch": branch, "path": path}
        try:
            repo.requester.requestJsonAndCheck("POST", f"{repo.url}/pages", input={"source": source})
        except GithubException as exc:
            if exc.status in (409, 422):
                repo.requester.requestJsonAndCheck("PUT", f"{repo.url}/pages", input={"source": source})
                return
            raise


def init_repository(config: GhInitConfig, client: GhInitClient) -> GhInitResult:
    """Apply the config to GitHub and (optionally) push the initial commit."""
    client.authenticated_login()
    repo = client.get_or_create_repo(
        config.owner,
        config.name,
        description=config.description,
        private=config.private,
        allow_existing=config.allow_existing,
    )
    for secret_name, value in config.secrets.items():
        client.set_secret(repo, secret_name, value)
    for variable_name, value in config.variables.items():
        client.set_variable(repo, variable_name, value)

    pushed = False
    if config.push:
        git_push(
            project_path=config.project_path,
            remote_url=repo.clone_url,
            branch=config.default_branch,
            force=config.force_push,
        )
        pushed = True

    # Pages needs the default branch to exist on the remote, so only attempt
    # this once the initial commit has been pushed. Failures here are surfaced
    # but never abort a bootstrap that already created the repo and pushed code.
    pages_configured = False
    pages_error: str | None = None
    if config.setup_pages and pushed:
        try:
            client.ensure_branch(repo, PAGES_BRANCH, config.default_branch)
            client.enable_pages(repo, PAGES_BRANCH)
            pages_configured = True
        except GithubException as exc:
            data = getattr(exc, "data", None)
            pages_error = str(data["message"]) if isinstance(data, dict) and "message" in data else str(exc)

    owner_login = repo.owner.login
    html_url = repo.html_url
    actions_url = f"{html_url}/actions"
    pages_url = f"https://{owner_login}.github.io/{repo.name}"
    skipped = list(getattr(config, "_skipped_secrets", []))
    return GhInitResult(
        html_url=html_url,
        actions_url=actions_url,
        pages_url=pages_url,
        skipped_secrets=skipped,
        pushed=pushed,
        pages_configured=pages_configured,
        pages_branch=PAGES_BRANCH,
        pages_error=pages_error,
    )


def _git(project_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def git_push(project_path: Path, remote_url: str, branch: str, force: bool) -> None:
    """Initialize git in ``project_path`` if needed, commit, and push to origin.

    Steps:
      1. ``git init`` if no ``.git`` directory exists.
      2. Stage everything and create an initial commit (only when there is no
         existing HEAD — re-runs against an already-initialized repo skip this).
      3. Rename the current branch to ``branch``.
      4. (Re-)add ``origin`` pointing at ``remote_url``.
      5. Push ``branch`` to ``origin`` with ``-u`` (and optionally ``--force``).
    """
    try:
        if not (project_path / ".git").exists():
            subprocess.run(["git", "init", str(project_path)], check=True, capture_output=True, text=True)

        head_exists = (
            subprocess.run(
                ["git", "-C", str(project_path), "rev-parse", "--verify", "HEAD"],
                check=False,
                capture_output=True,
                text=True,
            ).returncode
            == 0
        )

        if not head_exists:
            _git(project_path, "add", "-A")
            _git(
                project_path,
                "-c",
                f"user.name={INITIAL_COMMIT_USER}",
                "-c",
                f"user.email={INITIAL_COMMIT_EMAIL}",
                "commit",
                "-m",
                INITIAL_COMMIT_MESSAGE,
            )

        _git(project_path, "branch", "-M", branch)

        # Best-effort: drop any pre-existing origin so `remote add` always works.
        subprocess.run(
            ["git", "-C", str(project_path), "remote", "remove", "origin"],
            check=False,
            capture_output=True,
            text=True,
        )
        _git(project_path, "remote", "add", "origin", remote_url)

        push_args = ["push", "-u"]
        if force:
            push_args.append("--force")
        push_args += ["origin", branch]
        _git(project_path, *push_args)
    except FileNotFoundError as exc:
        raise RuntimeError("`git` was not found on PATH; install git before running gh-init.") from exc
