"""Cocogitto registration for generated workspace members."""

from __future__ import annotations

import click

from .models import WorkspaceEcosystem
from .models import WorkspaceMemberSpec


_VERSION_PLACEHOLDER = "{{version}}"


def register_cog_member(spec: WorkspaceMemberSpec) -> None:
    """Append one idempotent Cocogitto package section when cog.toml exists."""
    cog_path = spec.project_path / "cog.toml"
    if not cog_path.is_file():
        click.echo("No cog.toml found; skipping release registration.")
        return

    content = cog_path.read_text(encoding="utf-8")
    section = f"[packages.{spec.name}]"
    if section in content:
        raise click.ClickException(f"{section} already exists in cog.toml.")

    hook = _pre_bump_hook(spec)
    public_api = str(spec.public_api).lower()
    relative_path = f"{spec.location}/{spec.name}"
    addition = (
        f"\n{section}\n"
        f'path = "{relative_path}"\n'
        f"public_api = {public_api}\n"
        f'changelog_path = "{relative_path}/CHANGELOG.md"\n'
        "pre_bump_hooks = [\n"
        f'    "{hook}",\n'
        "]\n"
    )
    cog_path.write_text(content.rstrip() + "\n" + addition, encoding="utf-8")


def _pre_bump_hook(spec: WorkspaceMemberSpec) -> str:
    if spec.ecosystem is WorkspaceEcosystem.PNPM:
        return (
            f"pnpm --filter {spec.package_name} version "
            f"{_VERSION_PLACEHOLDER} --no-git-tag-version"
        )
    if spec.ecosystem is WorkspaceEcosystem.UV:
        return f"uv version --package {spec.name} {_VERSION_PLACEHOLDER}"
    return (
        "cargo workspaces version --all --force '*' --no-git-commit "
        f"{_VERSION_PLACEHOLDER}"
    )
