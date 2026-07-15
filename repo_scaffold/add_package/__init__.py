"""Add-package helpers for ``repo-scaffold add-package``.

Three layers, split across this package:

- :mod:`repo_scaffold.add_package.config` — ``ProjectType`` enum,
  ``AddPackageConfig`` dataclass, and ``detect_project_type`` for
  auto-detecting the workspace type from manifest files.
- :mod:`repo_scaffold.add_package.workspace` — ``add_rust_package`` and
  ``add_uv_package`` implement the per-type skeleton creation, cog.toml
  update, and workspace verification.
- this module — ``add_package`` orchestrates detection and delegation.
"""

from __future__ import annotations

from pathlib import Path

from .config import AddPackageConfig
from .config import ProjectType
from .config import detect_project_type
from .workspace import add_rust_package
from .workspace import add_uv_package


__all__ = [
    "AddPackageConfig",
    "ProjectType",
    "add_package",
    "add_rust_package",
    "add_uv_package",
    "detect_project_type",
]


def add_package(project_path: Path, name: str) -> None:
    """Detect the project type and delegate to the appropriate add-package logic.

    Args:
        project_path: Root directory of the workspace project.
        name: Name of the new package/crate to add.

    Raises:
        click.ClickException: When no workspace is detected or the package
            directory already exists.
    """
    project_type = detect_project_type(project_path)
    config = AddPackageConfig(
        project_path=project_path,
        name=name,
        project_type=project_type,
    )
    if project_type == ProjectType.RUST_WORKSPACE:
        add_rust_package(config)
    else:
        add_uv_package(config)
