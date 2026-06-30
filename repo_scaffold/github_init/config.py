"""Configuration resolution for ``gh-init``.

Collects repo metadata, secrets, and variables into a ``GhInitConfig`` from
CLI args, the environment, a ``.env`` file, ``pyproject.toml``, and an
optional interactive prompter. Kept separate from the PyGithub client and the
orchestrator so the resolution logic can be unit-tested in isolation.
"""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


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
    protect_branch: bool = False


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
    homepage_set: bool = False
    branch_protected: bool = False
    protection_error: str | None = None


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


def _github_owner_from_url(url: str) -> str | None:
    """Extract ``owner`` from a ``github.com/<owner>/<repo>`` URL, else ``None``."""
    match = re.search(r"github\.com[/:]([^/]+)/", url)
    return match.group(1) if match else None


def detect_owner(project_path: Path) -> tuple[str | None, str | None]:
    """Best-effort GitHub owner for the project and the source it came from.

    Resolution order: a ``github.com/<owner>/...`` URL in ``pyproject.toml``'s
    ``[project.urls]``, then the Cocogitto ``[changelog].owner`` field in
    ``cog.toml``. Returns ``(None, None)`` when no owner can be determined, in
    which case the caller falls back to the authenticated user.
    """
    pyproject = project_path / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        urls = (data.get("project", {}) or {}).get("urls", {}) or {}
        for value in urls.values():
            owner = _github_owner_from_url(str(value))
            if owner:
                return owner, "pyproject"

    cog = project_path / "cog.toml"
    if cog.is_file():
        with cog.open("rb") as f:
            data = tomllib.load(f)
        owner = (data.get("changelog", {}) or {}).get("owner")
        if owner:
            return str(owner), "cog.toml"

    return None, None


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
    protect_branch: bool = False,
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

    # Owner precedence: explicit flag, then a GitHub owner detected from the
    # project (pyproject URLs, then cog.toml), else None -> authenticated user.
    if owner:
        resolved_owner: str | None = owner
        owner_source: str | None = "flag"
    else:
        resolved_owner, owner_source = detect_owner(project_path)

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
        owner=resolved_owner,
        push=push,
        force_push=force_push,
        allow_existing=allow_existing,
        setup_pages=setup_pages,
        protect_branch=protect_branch,
    )
    config._skipped_secrets = skipped  # type: ignore[attr-defined]
    config._owner_source = owner_source  # type: ignore[attr-defined]
    return config
