"""GitHub bootstrap helpers for `repo-scaffold gh-init`.

Three layers, split across this package:

- :mod:`repo_scaffold.github_init.config` — ``GhInitConfig``/``GhInitResult``
  and ``build_config`` collect the repo metadata, secrets, and variables to
  apply.
- :mod:`repo_scaffold.github_init.client` — ``GhInitClient``, a thin wrapper
  around PyGithub so tests can swap the whole client out without monkey-patching
  the SDK.
- this module — ``init_repository`` orchestrates the calls and returns the URLs
  the CLI prints back to the user, plus the ``git_push``/``deploy_docs``
  subprocess helpers.

``git_push`` performs the optional initial commit + push via subprocess, with no
extra dependency on GitPython.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from github import GithubException

from .client import GhInitClient
from .config import DEFAULT_SECRET_KEYS
from .config import DEFAULT_VARIABLE_KEYS
from .config import PAGES_BRANCH
from .config import GhInitConfig
from .config import GhInitResult
from .config import build_config
from .config import detect_default_branch
from .config import detect_owner
from .config import load_pyproject
from .config import parse_dotenv


# GitHub Actions recognizes this marker in commit messages and skips
# workflows for the bootstrap push. Later user commits are not modified.
INITIAL_COMMIT_MESSAGE = "chore: initial commit from repo-scaffold [skip ci]"
INITIAL_COMMIT_USER = "repo-scaffold"
INITIAL_COMMIT_EMAIL = "repo-scaffold@users.noreply.github.com"

__all__ = [
    "DEFAULT_SECRET_KEYS",
    "DEFAULT_VARIABLE_KEYS",
    "INITIAL_COMMIT_EMAIL",
    "INITIAL_COMMIT_MESSAGE",
    "INITIAL_COMMIT_USER",
    "PAGES_BRANCH",
    "GhInitClient",
    "GhInitConfig",
    "GhInitResult",
    "build_config",
    "deploy_docs",
    "detect_default_branch",
    "detect_owner",
    "git_push",
    "init_repository",
    "load_pyproject",
    "parse_dotenv",
]


def _github_error_message(exc: GithubException) -> str:
    """Best-effort human-readable message from a GithubException."""
    data = getattr(exc, "data", None)
    return str(data["message"]) if isinstance(data, dict) and "message" in data else str(exc)


def deploy_docs(project_path: Path) -> None:
    """Build the MkDocs site and push it to the ``gh-pages`` branch.

    Runs the project's ``deploy-gh-pages`` just recipe (``mkdocs gh-deploy
    --force``), which builds with the right docs dependency group/extra, writes
    ``.nojekyll``, and pushes to ``origin``. Raises ``RuntimeError`` on failure
    so the orchestrator can surface it without aborting the whole bootstrap.
    """
    cmd = ["uvx", "--from", "rust-just", "just", "deploy-gh-pages"]
    try:
        subprocess.run(cmd, cwd=str(project_path), check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("`uvx` was not found on PATH; install uv before running gh-init.") from exc
    except subprocess.CalledProcessError as exc:
        tail = "\n".join((exc.stderr or exc.stdout or "").strip().splitlines()[-5:])
        raise RuntimeError(f"`mkdocs gh-deploy` failed:\n{tail}") from exc


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

    owner_login = repo.owner.login
    html_url = repo.html_url
    actions_url = f"{html_url}/actions"
    pages_url = f"https://{owner_login}.github.io/{repo.name}"

    # Build and publish the docs with `mkdocs gh-deploy` (which creates the
    # gh-pages branch with the real styled site + .nojekyll), then enable Pages
    # on it and point the repo's Website at the docs URL. Needs the push to have
    # happened and the project to actually have docs (mkdocs.yml). Any failure
    # is surfaced but never aborts a bootstrap that already created and pushed.
    pages_configured = False
    homepage_set = False
    pages_error: str | None = None
    has_docs = (config.project_path / "mkdocs.yml").is_file()
    if config.setup_pages and pushed and has_docs:
        try:
            deploy_docs(config.project_path)
            client.enable_pages(repo, PAGES_BRANCH)
            pages_configured = True
            client.set_homepage(repo, pages_url)
            homepage_set = True
        except (GithubException, RuntimeError) as exc:
            pages_error = _github_error_message(exc) if isinstance(exc, GithubException) else str(exc)

    # Branch protection also needs the branch to exist on the remote. Like
    # Pages, a failure (e.g. private repo on a free plan, or a token without
    # admin rights) is reported but never aborts the bootstrap.
    branch_protected = False
    protection_error: str | None = None
    if config.protect_branch and pushed:
        try:
            client.protect_branch(repo, config.default_branch)
            branch_protected = True
        except GithubException as exc:
            protection_error = _github_error_message(exc)

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
        homepage_set=homepage_set,
        branch_protected=branch_protected,
        protection_error=protection_error,
    )
