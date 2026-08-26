"""Models and validation shared by workspace-member providers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import click


class WorkspaceEcosystem(StrEnum):
    """Supported workspace package managers."""

    PNPM = "pnpm"
    UV = "uv"
    CARGO = "cargo"


_MEMBER_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_NPM_SCOPE = re.compile(r"^@[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class WorkspaceMemberSpec:
    """One member to add to an existing workspace."""

    project_path: Path
    name: str
    ecosystem: WorkspaceEcosystem
    member_type: str
    location: str
    scope: str | None
    private: bool
    public_api: bool
    depends_on: tuple[str, ...]
    no_install: bool
    no_verify: bool
    dry_run: bool

    @property
    def member_path(self) -> Path:
        """Return the absolute destination directory."""
        return self.project_path / self.location / self.name

    @property
    def package_name(self) -> str:
        """Return the package-manager-facing name for pnpm members."""
        return f"{self.scope}/{self.name}" if self.scope else self.name


def validate_member_name(name: str) -> None:
    """Reject names that could escape a workspace member directory."""
    if not _MEMBER_NAME.fullmatch(name):
        raise click.ClickException(
            "Member name must be lowercase kebab-case (letters, digits, and hyphens only)."
        )


def validate_scope(scope: str | None) -> None:
    """Validate an optional npm scope."""
    if scope is not None and not _NPM_SCOPE.fullmatch(scope):
        raise click.ClickException("Scope must be an npm scope such as '@fastpma'.")
