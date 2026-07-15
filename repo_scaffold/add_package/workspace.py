"""Workspace-specific add-package implementations.

Two functions, one per workspace type, that create the package skeleton,
update ``cog.toml`` for cocogitto tracking, and verify the workspace
compiles/syncs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

from .config import AddPackageConfig


# cocogitto uses {{version}} as a template variable in pre_bump_hooks;
# build the literal string at runtime.
_COG_VERSION_PLACEHOLDER = "{" + "{version}" + "}"

# ---------------------------------------------------------------------------
# Rust workspace
# ---------------------------------------------------------------------------

_CARGO_TOML_TEMPLATE = """\
[package]
name = "{name}"
version.workspace = true
edition.workspace = true
license.workspace = true
authors.workspace = true
description = ""

[dependencies]
"""

_LIB_RS_TEMPLATE = """\
// {name} crate
"""

_RUST_COG_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "cargo workspaces version --all --force '*' --no-git-commit {version_placeholder}",
]
"""


def add_rust_package(config: AddPackageConfig) -> None:
    """Add a new crate to a cargo workspace.

    Steps:
      1. Validate ``packages/<name>`` does not already exist.
      2. Create ``packages/<name>/Cargo.toml`` and ``src/lib.rs``.
      3. Append a ``[packages.<name>]`` section to ``cog.toml``.
      4. Run ``cargo check`` to verify the workspace compiles.
    """
    name = config.name
    project_path = config.project_path
    pkg_dir = project_path / "packages" / name

    if pkg_dir.exists():
        raise click.ClickException(f"❌ {pkg_dir.relative_to(project_path)} already exists")

    # 1. Create package skeleton
    click.echo(f"Creating crate '{name}' …")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    src_dir = pkg_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # Write Cargo.toml
    cargo_toml = pkg_dir / "Cargo.toml"
    cargo_toml.write_text(_CARGO_TOML_TEMPLATE.format(name=name), encoding="utf-8")

    # Write src/lib.rs
    lib_rs = src_dir / "lib.rs"
    lib_rs.write_text(_LIB_RS_TEMPLATE.format(name=name), encoding="utf-8")

    # 2. Append cog.toml section
    _append_cog_section(project_path, name, _RUST_COG_SECTION_TEMPLATE)

    # 3. Verify workspace compiles
    click.echo("Checking workspace …")
    result = subprocess.run(
        ["cargo", "check"],
        cwd=str(project_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"⚠️  cargo check failed:\n{result.stderr}")
    else:
        click.echo(f"✅ Crate '{name}' added.")

    click.echo("\nNext steps:")
    click.echo(f"  1. Add dependencies to packages/{name}/Cargo.toml")
    click.echo(f"  2. Implement your domain in packages/{name}/src/")
    click.echo("  3. Register routes in packages/api-server/src/app.rs")


# ---------------------------------------------------------------------------
# uv workspace
# ---------------------------------------------------------------------------

_UV_COG_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "uv version --package {name} {version_placeholder}",
]
"""


def add_uv_package(config: AddPackageConfig) -> None:
    """Add a new package to a uv workspace.

    Steps:
      1. Validate ``packages/<name>`` does not already exist.
      2. Run ``uv init --lib`` to create the package skeleton.
      3. Append a ``[packages.<name>]`` section to ``cog.toml``.
      4. Run ``uv sync --all-packages --all-groups`` to update the lockfile.
    """
    name = config.name
    project_path = config.project_path
    pkg_dir = project_path / "packages" / name

    if pkg_dir.exists():
        raise click.ClickException(f"❌ {pkg_dir.relative_to(project_path)} already exists")

    # 1. Create package skeleton via uv
    click.echo(f"Creating package '{name}' …")
    subprocess.check_call(
        ["uv", "init", "--lib", "--name", name, str(pkg_dir)],
        cwd=str(project_path),
    )

    # 2. Append cog.toml section
    _append_cog_section(project_path, name, _UV_COG_SECTION_TEMPLATE)

    # 3. Sync workspace
    click.echo("Syncing workspace …")
    subprocess.check_call(
        ["uv", "sync", "--all-packages", "--all-groups"],
        cwd=str(project_path),
    )

    module = name.replace("-", "_")
    click.echo(f"✅ Package '{name}' added. Module import name: {module}")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _append_cog_section(
    project_path: Path,
    name: str,
    template: str,
) -> None:
    """Append a ``[packages.<name>]`` section to ``cog.toml``."""
    cog_path = project_path / "cog.toml"
    section = template.format(name=name, version_placeholder=_COG_VERSION_PLACEHOLDER)
    with cog_path.open("a", encoding="utf-8") as f:
        f.write(section)
    click.echo(f"Appended [packages.{name}] to cog.toml")
