"""uv workspace-member provider preserving the existing library workflow."""

from __future__ import annotations

import subprocess

import click

from ..cog import register_cog_member
from ..models import WorkspaceMemberSpec


def add_uv_member(spec: WorkspaceMemberSpec) -> None:
    """Create a Python library member with uv's native generator."""
    if spec.member_type != "python-lib":
        raise click.ClickException(
            f"Unsupported uv member type '{spec.member_type}'. "
            "v1 supports python-lib."
        )
    if spec.member_path.exists():
        raise click.ClickException(
            f"❌ {spec.member_path.relative_to(spec.project_path)} already exists"
        )
    if spec.dry_run:
        click.echo(
            f"Would create uv python-lib: "
            f"{spec.member_path.relative_to(spec.project_path)}"
        )
        return

    subprocess.check_call(
        ["uv", "init", "--lib", "--name", spec.name, str(spec.member_path)],
        cwd=str(spec.project_path),
    )
    register_cog_member(spec)
    if not spec.no_install:
        subprocess.check_call(
            ["uv", "sync", "--all-packages", "--all-groups"],
            cwd=str(spec.project_path),
        )
    click.echo(f"✅ uv member '{spec.name}' added.")
