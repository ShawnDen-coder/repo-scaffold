"""Cargo workspace-member provider preserving the existing library workflow."""

from __future__ import annotations

import importlib.resources
import subprocess

import click
from cookiecutter.main import cookiecutter

from ..cog import register_cog_member
from ..models import WorkspaceMemberSpec


def add_cargo_member(spec: WorkspaceMemberSpec) -> None:
    """Create a Rust library member with a workspace-aware manifest."""
    if spec.member_type != "rust-lib":
        raise click.ClickException(
            f"Unsupported Cargo member type '{spec.member_type}'. "
            "v1 supports rust-lib."
        )
    if spec.member_path.exists():
        raise click.ClickException(
            f"❌ {spec.member_path.relative_to(spec.project_path)} already exists"
        )
    if spec.dry_run:
        click.echo(
            f"Would create Cargo rust-lib: "
            f"{spec.member_path.relative_to(spec.project_path)}"
        )
        return

    cookiecutter(
        template=str(importlib.resources.files("repo_scaffold").joinpath(
            "templates", "workspace_members", "cargo", "rust-lib"
        )),
        output_dir=str(spec.member_path.parent),
        no_input=True,
        extra_context={"member_name": spec.name},
    )
    register_cog_member(spec)
    if not spec.no_verify:
        subprocess.check_call(
            ["cargo", "check", "-p", spec.name],
            cwd=str(spec.project_path),
        )
    click.echo(f"✅ Cargo member '{spec.name}' added.")
