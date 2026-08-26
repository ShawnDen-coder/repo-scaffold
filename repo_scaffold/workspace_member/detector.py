"""Workspace ecosystem detection."""

from __future__ import annotations

import tomllib
from pathlib import Path

import click

from .models import WorkspaceEcosystem


def detect_workspace_ecosystem(project_path: Path) -> WorkspaceEcosystem:
    """Detect Cargo, uv, or pnpm from the workspace root manifests."""
    project_path = project_path.resolve()

    cargo_toml = project_path / "Cargo.toml"
    if cargo_toml.is_file():
        with cargo_toml.open("rb") as file:
            if "workspace" in tomllib.load(file):
                return WorkspaceEcosystem.CARGO

    pyproject_toml = project_path / "pyproject.toml"
    if pyproject_toml.is_file():
        with pyproject_toml.open("rb") as file:
            data = tomllib.load(file)
        if "uv" in data.get("tool", {}) and "workspace" in data["tool"]["uv"]:
            return WorkspaceEcosystem.UV

    if (project_path / "pnpm-workspace.yaml").is_file():
        return WorkspaceEcosystem.PNPM

    raise click.ClickException(
        "No workspace detected. Expected Cargo.toml with [workspace], "
        "pyproject.toml with [tool.uv.workspace], or pnpm-workspace.yaml."
    )
