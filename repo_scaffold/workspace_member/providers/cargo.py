"""Cargo workspace-member provider preserving the existing library workflow."""

from __future__ import annotations

import subprocess

import click

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

    spec.member_path.mkdir(parents=True)
    (spec.member_path / "src").mkdir()
    (spec.member_path / "Cargo.toml").write_text(
        (
            "[package]\n"
            f'name = "{spec.name}"\n'
            "version.workspace = true\n"
            "edition.workspace = true\n"
            "license.workspace = true\n"
            "authors.workspace = true\n"
            'description = ""\n\n'
            "[dependencies]\n"
        ),
        encoding="utf-8",
    )
    (spec.member_path / "src" / "lib.rs").write_text(
        f"// {spec.name} crate\n", encoding="utf-8"
    )
    (spec.member_path / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## {spec.name}\n", encoding="utf-8"
    )
    register_cog_member(spec)
    if not spec.no_verify:
        subprocess.check_call(
            ["cargo", "check", "-p", spec.name],
            cwd=str(spec.project_path),
        )
    click.echo(f"✅ Cargo member '{spec.name}' added.")
