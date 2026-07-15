"""Project-type detection and configuration for ``add-package``.

Detects whether the target directory is a Rust cargo workspace or a uv
workspace by inspecting ``Cargo.toml`` / ``pyproject.toml``, and collects
the resolved configuration into an ``AddPackageConfig`` dataclass.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import click


class ProjectType(Enum):
    """Supported workspace project types."""

    RUST_WORKSPACE = "rust"
    UV_WORKSPACE = "uv"


@dataclass
class AddPackageConfig:
    """Resolved configuration for one ``add-package`` invocation."""

    project_path: Path
    name: str
    project_type: ProjectType


def detect_project_type(project_path: Path) -> ProjectType:
    """Detect the workspace type from manifest files.

    Resolution order:
      1. ``Cargo.toml`` with a ``[workspace]`` section → ``RUST_WORKSPACE``
      2. ``pyproject.toml`` with a ``[tool.uv.workspace]`` section → ``UV_WORKSPACE``
      3. Neither → raise ``click.ClickException``

    Args:
        project_path: Root directory of the workspace project.

    Returns:
        The detected ``ProjectType``.

    Raises:
        click.ClickException: When no recognised workspace manifest is found.
    """
    project_path = project_path.resolve()

    cargo_toml = project_path / "Cargo.toml"
    if cargo_toml.is_file():
        with cargo_toml.open("rb") as f:
            data = tomllib.load(f)
        if "workspace" in data:
            return ProjectType.RUST_WORKSPACE

    pyproject_toml = project_path / "pyproject.toml"
    if pyproject_toml.is_file():
        with pyproject_toml.open("rb") as f:
            data = tomllib.load(f)
        if "uv" in data.get("tool", {}) and "workspace" in data["tool"]["uv"]:
            return ProjectType.UV_WORKSPACE

    raise click.ClickException(
        "No workspace detected. Expected a Cargo.toml with [workspace] or a pyproject.toml with [tool.uv.workspace]."
    )
