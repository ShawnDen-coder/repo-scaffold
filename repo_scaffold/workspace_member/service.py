"""Build and dispatch workspace-member generation requests."""

from __future__ import annotations

from pathlib import Path

import click

from .detector import detect_workspace_ecosystem
from .models import WorkspaceEcosystem
from .models import WorkspaceMemberSpec
from .models import validate_member_name
from .models import validate_scope
from .providers.cargo import add_cargo_member
from .providers.pnpm import add_pnpm_member
from .providers.uv import add_uv_member


_DEFAULT_TYPE = {
    WorkspaceEcosystem.PNPM: "ts-lib",
    WorkspaceEcosystem.UV: "python-lib",
    WorkspaceEcosystem.CARGO: "rust-lib",
}

_APPLICATION_TYPES = {
    "node-service",
    "react-app",
    "vue-app",
    "electron-app",
}


def build_member_spec(
    *,
    project_path: Path,
    name: str,
    ecosystem: WorkspaceEcosystem | None = None,
    member_type: str | None = None,
    location: str | None = None,
    scope: str | None = None,
    private: bool | None = None,
    public_api: bool = False,
    depends_on: tuple[str, ...] = (),
    no_install: bool = False,
    no_verify: bool = False,
    dry_run: bool = False,
) -> WorkspaceMemberSpec:
    """Resolve CLI input into one validated member specification."""
    project_path = project_path.resolve()
    resolved_ecosystem = ecosystem or detect_workspace_ecosystem(project_path)
    resolved_type = member_type or _DEFAULT_TYPE[resolved_ecosystem]
    resolved_location = location or (
        "apps" if resolved_type in _APPLICATION_TYPES else "packages"
    )

    validate_member_name(name)
    validate_scope(scope)
    if resolved_location not in {"apps", "packages"}:
        raise click.ClickException("Location must be either 'apps' or 'packages'.")

    if resolved_ecosystem is not WorkspaceEcosystem.PNPM:
        if scope is not None:
            raise click.ClickException("--scope is only supported by pnpm members.")
        if depends_on:
            raise click.ClickException(
                "--depends-on is currently only supported by pnpm members."
            )
        if private is not None:
            raise click.ClickException(
                "--private/--public is currently only supported by pnpm members."
            )
        if resolved_location != "packages":
            raise click.ClickException(
                "uv and Cargo members currently support only --location packages."
            )

    return WorkspaceMemberSpec(
        project_path=project_path,
        name=name,
        ecosystem=resolved_ecosystem,
        member_type=resolved_type,
        location=resolved_location,
        scope=scope,
        private=True if private is None else private,
        public_api=public_api,
        depends_on=depends_on,
        no_install=no_install,
        no_verify=no_verify,
        dry_run=dry_run,
    )


def add_member(spec: WorkspaceMemberSpec) -> None:
    """Dispatch a validated member request to its ecosystem provider."""
    if spec.ecosystem is WorkspaceEcosystem.PNPM:
        add_pnpm_member(spec)
    elif spec.ecosystem is WorkspaceEcosystem.UV:
        add_uv_member(spec)
    else:
        add_cargo_member(spec)
