"""Unit tests for the add-package pipeline."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from repo_scaffold.add_package import AddPackageConfig
from repo_scaffold.add_package import ProjectType
from repo_scaffold.add_package import add_package
from repo_scaffold.add_package import detect_project_type
from repo_scaffold.add_package.workspace import _COG_VERSION_PLACEHOLDER
from repo_scaffold.add_package.workspace import _PNPM_COG_SECTION_TEMPLATE
from repo_scaffold.add_package.workspace import _RUST_COG_SECTION_TEMPLATE
from repo_scaffold.add_package.workspace import _UV_COG_SECTION_TEMPLATE
from repo_scaffold.add_package.workspace import add_pnpm_package
from repo_scaffold.add_package.workspace import add_rust_package
from repo_scaffold.add_package.workspace import add_uv_package
from repo_scaffold.cli import cli


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_cargo_workspace(path: Path) -> None:
    """Write a minimal Cargo.toml with [workspace] section."""
    (path / "Cargo.toml").write_text(
        "[workspace]\nmembers = ['packages/*']\nresolver = '2'\n\n"
        "[workspace.package]\nversion = '0.1.0'\nedition = '2021'\n",
        encoding="utf-8",
    )


def _write_cargo_non_workspace(path: Path) -> None:
    """Write a Cargo.toml without [workspace] section."""
    (path / "Cargo.toml").write_text(
        '[package]\nname = "standalone"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )


def _write_uv_workspace(path: Path) -> None:
    """Write a minimal pyproject.toml with [tool.uv.workspace] section."""
    (path / "pyproject.toml").write_text(
        '[project]\nname = "ws"\n\n[tool.uv.workspace]\nmembers = ["packages/*"]\n',
        encoding="utf-8",
    )


def _write_cog_toml(path: Path) -> None:
    """Write a minimal cog.toml."""
    (path / "cog.toml").write_text(
        'ignore_merge_commits = true\n\n[changelog]\npath = "CHANGELOG.md"\n',
        encoding="utf-8",
    )


def _write_pnpm_workspace(path: Path) -> None:
    """Write a minimal pnpm-workspace.yaml."""
    (path / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'packages/*'\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


def test_detect_rust_workspace(tmp_path: Path):
    """Cargo.toml with [workspace] → RUST_WORKSPACE."""
    _write_cargo_workspace(tmp_path)
    assert detect_project_type(tmp_path) == ProjectType.RUST_WORKSPACE


def test_detect_uv_workspace(tmp_path: Path):
    """pyproject.toml with [tool.uv.workspace] → UV_WORKSPACE."""
    _write_uv_workspace(tmp_path)
    assert detect_project_type(tmp_path) == ProjectType.UV_WORKSPACE


def test_detect_rust_takes_precedence_over_uv(tmp_path: Path):
    """When both manifests exist, Cargo.toml [workspace] wins."""
    _write_cargo_workspace(tmp_path)
    _write_uv_workspace(tmp_path)
    assert detect_project_type(tmp_path) == ProjectType.RUST_WORKSPACE


def test_detect_no_workspace_raises(tmp_path: Path):
    """No manifest files → ClickException."""
    with pytest.raises(click.ClickException, match="No workspace detected"):
        detect_project_type(tmp_path)


def test_detect_non_workspace_cargo_toml_raises(tmp_path: Path):
    """Cargo.toml without [workspace] → ClickException."""
    _write_cargo_non_workspace(tmp_path)
    with pytest.raises(click.ClickException, match="No workspace detected"):
        detect_project_type(tmp_path)


def test_detect_pyproject_without_uv_workspace_raises(tmp_path: Path):
    """pyproject.toml without [tool.uv.workspace] → ClickException."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "standalone"\n',
        encoding="utf-8",
    )
    with pytest.raises(click.ClickException, match="No workspace detected"):
        detect_project_type(tmp_path)


def test_detect_pnpm_workspace(tmp_path: Path):
    """pnpm-workspace.yaml → PNPM_WORKSPACE."""
    _write_pnpm_workspace(tmp_path)
    assert detect_project_type(tmp_path) == ProjectType.PNPM_WORKSPACE


# ---------------------------------------------------------------------------
# Rust workspace add-package tests
# ---------------------------------------------------------------------------


def test_add_rust_package_creates_skeleton(tmp_path: Path):
    """add_rust_package creates Cargo.toml + src/lib.rs and appends to cog.toml."""
    _write_cargo_workspace(tmp_path)
    _write_cog_toml(tmp_path)
    config = AddPackageConfig(
        project_path=tmp_path,
        name="my-crate",
        project_type=ProjectType.RUST_WORKSPACE,
    )

    with patch("repo_scaffold.add_package.workspace.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(["cargo", "check"], 0, stdout="", stderr="")
        add_rust_package(config)

    # Verify Cargo.toml
    cargo_toml = tmp_path / "packages" / "my-crate" / "Cargo.toml"
    assert cargo_toml.is_file()
    content = cargo_toml.read_text(encoding="utf-8")
    assert 'name = "my-crate"' in content
    assert "version.workspace = true" in content

    # Verify src/lib.rs
    lib_rs = tmp_path / "packages" / "my-crate" / "src" / "lib.rs"
    assert lib_rs.is_file()
    assert "my-crate crate" in lib_rs.read_text(encoding="utf-8")

    # Verify cog.toml section
    cog = tmp_path / "cog.toml"
    cog_content = cog.read_text(encoding="utf-8")
    assert "[packages.my-crate]" in cog_content
    assert 'path = "packages/my-crate"' in cog_content
    assert "cargo workspaces version" in cog_content


def test_add_rust_package_rejects_existing_dir(tmp_path: Path):
    """add_rust_package raises when the package directory already exists."""
    _write_cargo_workspace(tmp_path)
    pkg_dir = tmp_path / "packages" / "existing-crate"
    pkg_dir.mkdir(parents=True)

    config = AddPackageConfig(
        project_path=tmp_path,
        name="existing-crate",
        project_type=ProjectType.RUST_WORKSPACE,
    )

    with pytest.raises(click.ClickException, match="already exists"):
        add_rust_package(config)


def test_add_rust_package_cargo_check_failure(tmp_path: Path):
    """add_rust_package warns but does not raise when cargo check fails."""
    _write_cargo_workspace(tmp_path)
    _write_cog_toml(tmp_path)
    config = AddPackageConfig(
        project_path=tmp_path,
        name="my-crate",
        project_type=ProjectType.RUST_WORKSPACE,
    )

    with patch("repo_scaffold.add_package.workspace.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            ["cargo", "check"], 1, stdout="", stderr="error: could not compile"
        )
        # Should not raise, just warn
        add_rust_package(config)

    # Files should still be created
    assert (tmp_path / "packages" / "my-crate" / "Cargo.toml").is_file()


# ---------------------------------------------------------------------------
# uv workspace add-package tests
# ---------------------------------------------------------------------------


def test_add_uv_package_creates_skeleton(tmp_path: Path):
    """add_uv_package calls uv init and appends to cog.toml."""
    _write_uv_workspace(tmp_path)
    _write_cog_toml(tmp_path)
    config = AddPackageConfig(
        project_path=tmp_path,
        name="my-lib",
        project_type=ProjectType.UV_WORKSPACE,
    )

    with patch("repo_scaffold.add_package.workspace.subprocess.check_call") as mock_call:
        add_uv_package(config)

    # Verify uv init was called
    calls = mock_call.call_args_list
    assert any("uv" in str(c) and "init" in str(c) for c in calls)
    assert any("uv" in str(c) and "sync" in str(c) for c in calls)

    # Verify cog.toml section
    cog = tmp_path / "cog.toml"
    cog_content = cog.read_text(encoding="utf-8")
    assert "[packages.my-lib]" in cog_content
    assert 'path = "packages/my-lib"' in cog_content
    assert "uv version --package my-lib" in cog_content


def test_add_uv_package_rejects_existing_dir(tmp_path: Path):
    """add_uv_package raises when the package directory already exists."""
    _write_uv_workspace(tmp_path)
    pkg_dir = tmp_path / "packages" / "existing-lib"
    pkg_dir.mkdir(parents=True)

    config = AddPackageConfig(
        project_path=tmp_path,
        name="existing-lib",
        project_type=ProjectType.UV_WORKSPACE,
    )

    with pytest.raises(click.ClickException, match="already exists"):
        add_uv_package(config)


# ---------------------------------------------------------------------------
# pnpm workspace add-package tests
# ---------------------------------------------------------------------------


def test_add_pnpm_package_creates_skeleton(tmp_path: Path):
    """add_pnpm_package creates package.json + vite.config.ts + src/index.ts and appends to cog.toml."""
    _write_pnpm_workspace(tmp_path)
    _write_cog_toml(tmp_path)
    config = AddPackageConfig(
        project_path=tmp_path,
        name="my-lib",
        project_type=ProjectType.PNPM_WORKSPACE,
    )

    with patch("repo_scaffold.add_package.workspace.subprocess.check_call"):
        add_pnpm_package(config)

    # Verify package.json
    package_json = tmp_path / "packages" / "my-lib" / "package.json"
    assert package_json.is_file()
    content = package_json.read_text(encoding="utf-8")
    assert '"my-lib"' in content

    # Verify vite.config.ts
    vite_config = tmp_path / "packages" / "my-lib" / "vite.config.ts"
    assert vite_config.is_file()

    # Verify src/index.ts
    index_ts = tmp_path / "packages" / "my-lib" / "src" / "index.ts"
    assert index_ts.is_file()

    # Verify cog.toml section
    cog = tmp_path / "cog.toml"
    cog_content = cog.read_text(encoding="utf-8")
    assert "[packages.my-lib]" in cog_content
    assert 'path = "packages/my-lib"' in cog_content
    assert "pnpm --filter my-lib version" in cog_content


def test_add_pnpm_package_rejects_existing_dir(tmp_path: Path):
    """add_pnpm_package raises when the package directory already exists."""
    _write_pnpm_workspace(tmp_path)
    pkg_dir = tmp_path / "packages" / "existing-lib"
    pkg_dir.mkdir(parents=True)

    config = AddPackageConfig(
        project_path=tmp_path,
        name="existing-lib",
        project_type=ProjectType.PNPM_WORKSPACE,
    )

    with pytest.raises(click.ClickException, match="already exists"):
        add_pnpm_package(config)


# ---------------------------------------------------------------------------
# cog.toml section content tests
# ---------------------------------------------------------------------------


def test_cog_toml_section_rust_has_correct_hooks():
    """Rust cog.toml section uses cargo workspaces version hook with {{version}} placeholder."""
    section = _RUST_COG_SECTION_TEMPLATE.format(name="test-crate", version_placeholder=_COG_VERSION_PLACEHOLDER)
    assert "[packages.test-crate]" in section
    assert 'path = "packages/test-crate"' in section
    assert "public_api = true" in section
    assert "cargo workspaces version --all --force '*' --no-git-commit {{version}}" in section
    # The {{version}} must be the literal cocogitto placeholder
    assert "{{version}}" in section


def test_cog_toml_section_uv_has_correct_hooks():
    """Uv cog.toml section uses uv version --package hook with {{version}} placeholder."""
    section = _UV_COG_SECTION_TEMPLATE.format(name="test-lib", version_placeholder=_COG_VERSION_PLACEHOLDER)
    assert "[packages.test-lib]" in section
    assert 'path = "packages/test-lib"' in section
    assert "public_api = true" in section
    assert "uv version --package test-lib {{version}}" in section
    # The {{version}} must be the literal cocogitto placeholder
    assert "{{version}}" in section


def test_cog_toml_section_pnpm_has_correct_hooks():
    """Pnpm cog.toml section uses pnpm --filter version hook with {{version}} placeholder."""
    section = _PNPM_COG_SECTION_TEMPLATE.format(name="test-lib", version_placeholder=_COG_VERSION_PLACEHOLDER)
    assert "[packages.test-lib]" in section
    assert 'path = "packages/test-lib"' in section
    assert "public_api = true" in section
    assert "pnpm --filter test-lib version {{version}}" in section
    # The {{version}} must be the literal cocogitto placeholder
    assert "{{version}}" in section


def test_cog_version_placeholder_is_double_braces():
    """The {{version}} placeholder is the literal cocogitto template variable."""
    assert _COG_VERSION_PLACEHOLDER == "{{version}}"


# ---------------------------------------------------------------------------
# Orchestrator tests
# ---------------------------------------------------------------------------


def test_add_package_delegates_to_rust(tmp_path: Path):
    """add_package delegates to add_rust_package for a Rust workspace."""
    _write_cargo_workspace(tmp_path)
    _write_cog_toml(tmp_path)

    with patch("repo_scaffold.add_package.add_rust_package") as mock_rust:
        add_package(tmp_path, "my-crate")
        mock_rust.assert_called_once()
        config = mock_rust.call_args[0][0]
        assert config.name == "my-crate"
        assert config.project_type == ProjectType.RUST_WORKSPACE


def test_add_package_delegates_to_uv(tmp_path: Path):
    """add_package delegates to add_uv_package for a uv workspace."""
    _write_uv_workspace(tmp_path)
    _write_cog_toml(tmp_path)

    with patch("repo_scaffold.add_package.add_uv_package") as mock_uv:
        add_package(tmp_path, "my-lib")
        mock_uv.assert_called_once()
        config = mock_uv.call_args[0][0]
        assert config.name == "my-lib"
        assert config.project_type == ProjectType.UV_WORKSPACE


# ---------------------------------------------------------------------------
# CLI wiring tests
# ---------------------------------------------------------------------------


def test_cli_add_package_help():
    """add-package --help shows usage information."""
    result = CliRunner().invoke(cli, ["add-package", "--help"])
    assert result.exit_code == 0
    assert "add-package" in result.output.lower() or "Add a new package" in result.output


def test_cli_add_package_no_workspace_errors(tmp_path: Path):
    """Running add-package in a non-workspace directory gives a clear error."""
    result = CliRunner().invoke(cli, ["add-package", "my-lib", "-p", str(tmp_path)])
    assert result.exit_code != 0
    assert "No workspace detected" in result.output


def test_cli_add_package_rust_workspace(tmp_path: Path):
    """CLI delegates to add_rust_package for a Rust workspace."""
    _write_cargo_workspace(tmp_path)
    _write_cog_toml(tmp_path)

    with patch("repo_scaffold.add_package.add_rust_package") as mock_rust:
        result = CliRunner().invoke(cli, ["add-package", "my-crate", "-p", str(tmp_path)])
        assert result.exit_code == 0
        mock_rust.assert_called_once()


def test_cli_add_package_uv_workspace(tmp_path: Path):
    """CLI delegates to add_uv_package for a uv workspace."""
    _write_uv_workspace(tmp_path)
    _write_cog_toml(tmp_path)

    with patch("repo_scaffold.add_package.add_uv_package") as mock_uv:
        result = CliRunner().invoke(cli, ["add-package", "my-lib", "-p", str(tmp_path)])
        assert result.exit_code == 0
        mock_uv.assert_called_once()


def test_cli_add_package_pnpm_workspace(tmp_path: Path):
    """CLI delegates to add_pnpm_package for a pnpm workspace."""
    _write_pnpm_workspace(tmp_path)
    _write_cog_toml(tmp_path)

    with patch("repo_scaffold.add_package.add_pnpm_package") as mock_pnpm:
        result = CliRunner().invoke(cli, ["add-package", "my-lib", "-p", str(tmp_path)])
        assert result.exit_code == 0
        mock_pnpm.assert_called_once()
