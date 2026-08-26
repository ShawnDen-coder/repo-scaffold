"""Tests for the v1 workspace-member command and pnpm ts-lib provider."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from repo_scaffold.cli import cli
from repo_scaffold.workspace_member import WorkspaceEcosystem
from repo_scaffold.workspace_member import add_member
from repo_scaffold.workspace_member import build_member_spec
from repo_scaffold.workspace_member.providers import pnpm as pnpm_provider


def _write_pnpm_workspace(path: Path) -> None:
    (path / "pnpm-workspace.yaml").write_text(
        "packages:\n  - packages/*\n", encoding="utf-8"
    )
    (path / "package.json").write_text(
        json.dumps({"devDependencies": {"typescript": "^5.6.3"}}),
        encoding="utf-8",
    )
    (path / "cog.toml").write_text(
        'ignore_merge_commits = true\n\n[changelog]\npath = "CHANGELOG.md"\n',
        encoding="utf-8",
    )


def test_add_pnpm_ts_lib_renders_member_and_registers_cog(tmp_path: Path):
    """Render a scoped pnpm library and add it to Cocogitto."""
    _write_pnpm_workspace(tmp_path)
    spec = build_member_spec(
        project_path=tmp_path,
        name="agent-core",
        ecosystem=WorkspaceEcosystem.PNPM,
        member_type="ts-lib",
        scope="@fastpma",
        depends_on=("@fastpma/shared",),
        no_install=True,
        no_verify=True,
    )

    add_member(spec)

    package_dir = tmp_path / "packages" / "agent-core"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "@fastpma/agent-core"
    assert manifest["private"] is True
    assert manifest["dependencies"] == {"@fastpma/shared": "workspace:*"}
    assert (package_dir / "src" / "index.ts").is_file()
    assert not (package_dir / "CHANGELOG.md").exists()

    assert manifest["scripts"]["test"] == "vitest run"
    assert "vitest" in manifest["devDependencies"]
    assert (package_dir / "tests" / "index.test.ts").is_file()
    assert manifest["scripts"]["check"] == "biome check ."
    assert manifest["scripts"]["format"] == "biome format --write ."
    assert (package_dir / "biome.json").is_file()
    cog = (tmp_path / "cog.toml").read_text(encoding="utf-8")
    assert "[packages.agent-core]" in cog
    assert 'path = "packages/agent-core"' in cog
    assert "pnpm --filter @fastpma/agent-core version {{version}}" in cog


def test_add_pnpm_member_adds_missing_apps_workspace_glob(tmp_path: Path):
    """Register a missing apps workspace glob before generation."""
    _write_pnpm_workspace(tmp_path)
    spec = build_member_spec(
        project_path=tmp_path,
        name="agent-core",
        ecosystem=WorkspaceEcosystem.PNPM,
        member_type="ts-lib",
        location="apps",
        no_install=True,
        no_verify=True,
    )

    add_member(spec)

    workspace = (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8")
    assert "apps/*" in workspace
    assert (tmp_path / "apps" / "agent-core" / "package.json").is_file()


def test_dry_run_does_not_write_member_or_workspace(tmp_path: Path):
    """Avoid all filesystem mutations when previewing a member."""
    _write_pnpm_workspace(tmp_path)
    spec = build_member_spec(
        project_path=tmp_path,
        name="agent-core",
        ecosystem=WorkspaceEcosystem.PNPM,
        member_type="ts-lib",
        location="apps",
        dry_run=True,
    )

    add_member(spec)

    assert not (tmp_path / "apps" / "agent-core").exists()
    workspace = (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8")
    assert "apps/*" not in workspace


def test_non_pnpm_scope_is_rejected(tmp_path: Path):
    """Reject pnpm-only scope configuration for uv workspaces."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["packages/*"]\n',
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="--scope is only supported"):
        build_member_spec(
            project_path=tmp_path,
            name="python-core",
            ecosystem=WorkspaceEcosystem.UV,
            scope="@fastpma",
        )


def test_cli_add_member_dry_run(tmp_path: Path):
    """Expose a side-effect-free CLI preview."""
    _write_pnpm_workspace(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "add-member",
            "agent-core",
            "--type",
            "ts-lib",
            "--scope",
            "@fastpma",
            "--project-path",
            str(tmp_path),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Would create pnpm ts-lib" in result.output
    assert not (tmp_path / "packages" / "agent-core").exists()


def test_non_pnpm_private_flag_is_rejected(tmp_path: Path):
    """Reject an explicitly supplied pnpm visibility flag for uv."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["packages/*"]\n',
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="--private/--public is currently only supported"):
        build_member_spec(
            project_path=tmp_path,
            name="python-core",
            ecosystem=WorkspaceEcosystem.UV,
            private=False,
        )


def test_legacy_command_does_not_accept_v1_flags(tmp_path: Path):
    """Keep v1-only flags outside the legacy command contract."""
    _write_pnpm_workspace(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "add-package",
            "agent-core",
            "--scope",
            "@fastpma",
            "--project-path",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "No such option '--scope'" in result.output


def test_cli_add_member_generates_scoped_pnpm_library(tmp_path: Path):
    """Run the v1 CLI through rendering, dependency wiring, and Cog registration."""
    _write_pnpm_workspace(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "add-member",
            "agent-core",
            "--type",
            "ts-lib",
            "--scope",
            "@fastpma",
            "--depends-on",
            "@fastpma/shared",
            "--project-path",
            str(tmp_path),
            "--no-install",
            "--no-verify",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "pnpm member '@fastpma/agent-core' added" in result.output

    manifest_path = tmp_path / "packages" / "agent-core" / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "@fastpma/agent-core"
    assert manifest["dependencies"] == {"@fastpma/shared": "workspace:*"}

    cog = (tmp_path / "cog.toml").read_text(encoding="utf-8")
    assert "[packages.agent-core]" in cog


def test_cli_add_member_generates_ts_cli(tmp_path: Path):
    """Render the Vite/Biome/Vitest CLI member through the public CLI command."""
    _write_pnpm_workspace(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "add-member",
            "release-tool",
            "--type",
            "ts-cli",
            "--project-path",
            str(tmp_path),
            "--no-install",
            "--no-verify",
        ],
    )

    assert result.exit_code == 0, result.output
    package_dir = tmp_path / "packages" / "release-tool"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    assert manifest["bin"] == {"release-tool": "./dist/index.cjs"}
    assert manifest["scripts"]["test"] == "vitest run"
    assert manifest["scripts"]["check"] == "biome check ."
    assert (package_dir / "biome.json").is_file()
    assert (package_dir / "tests" / "program.test.ts").is_file()


def test_cli_ts_cli_dry_run_names_the_selected_member_type(tmp_path: Path):
    """Report the selected type in a side-effect-free preview."""
    _write_pnpm_workspace(tmp_path)

    result = CliRunner().invoke(
        cli,
        ["add-member", "release-tool", "--type", "ts-cli", "-p", str(tmp_path), "--dry-run"],
    )

    assert result.exit_code == 0, result.output
    assert "Would create pnpm ts-cli" in result.output


def test_cli_add_member_generates_react_app(tmp_path: Path):
    """Render a React/Tailwind app through the public CLI entry point."""
    _write_pnpm_workspace(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["add-member", "dashboard", "--type", "react-app", "-p", str(tmp_path), "--no-install", "--no-verify"],
    )

    assert result.exit_code == 0, result.output
    package_dir = tmp_path / "apps" / "dashboard"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    assert manifest["scripts"]["dev"] == "vite"
    assert "tailwindcss" in manifest["dependencies"]
    assert "@biomejs/biome" in manifest["devDependencies"]
    assert (package_dir / "src" / "App.tsx").is_file()
    assert (package_dir / "src" / "index.css").read_text(encoding="utf-8") == '@import "tailwindcss";\n'
    assert (package_dir / "tests" / "app.test.tsx").is_file()


def test_cli_add_member_generates_vue_app(tmp_path: Path):
    """Render a Vue/Tailwind app through the public CLI entry point."""
    _write_pnpm_workspace(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["add-member", "portal", "--type", "vue-app", "-p", str(tmp_path), "--no-install", "--no-verify"],
    )

    assert result.exit_code == 0, result.output
    package_dir = tmp_path / "apps" / "portal"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    assert manifest["scripts"]["build"] == "vue-tsc -b && vite build"
    assert "tailwindcss" in manifest["dependencies"]
    assert "vue-tsc" in manifest["devDependencies"]
    assert (package_dir / "src" / "App.vue").is_file()
    assert (package_dir / "biome.json").is_file()
    assert (package_dir / "tests" / "app.test.ts").is_file()


def test_cli_add_member_generates_react_lib_and_node_service(tmp_path: Path):
    """Render the React library and Express service member types."""
    _write_pnpm_workspace(tmp_path)

    for name, member_type in (("ui-kit", "react-lib"), ("api", "node-service")):
        result = CliRunner().invoke(
            cli,
            ["add-member", name, "--type", member_type, "-p", str(tmp_path), "--no-install", "--no-verify"],
        )
        assert result.exit_code == 0, result.output

    react_dir = tmp_path / "packages" / "ui-kit"
    react_manifest = json.loads((react_dir / "package.json").read_text(encoding="utf-8"))
    assert "react" in react_manifest["peerDependencies"]
    assert (react_dir / "src" / "index.tsx").is_file()
    assert (react_dir / "tests" / "index.test.tsx").is_file()

    service_dir = tmp_path / "apps" / "api"
    service_manifest = json.loads((service_dir / "package.json").read_text(encoding="utf-8"))
    assert service_manifest["dependencies"]["express"] == "^5.1.0"
    assert service_manifest["scripts"]["dev"] == "tsx watch src/server.ts"
    assert (service_dir / "src" / "app.ts").is_file()
    assert (service_dir / "tests" / "app.test.ts").is_file()


def test_cli_add_member_generates_electron_app(tmp_path: Path):
    """Render an Electron desktop app under the workspace apps directory."""
    _write_pnpm_workspace(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["add-member", "desktop", "--type", "electron-app", "-p", str(tmp_path), "--no-install", "--no-verify"],
    )

    assert result.exit_code == 0, result.output
    app_dir = tmp_path / "apps" / "desktop"
    manifest = json.loads((app_dir / "package.json").read_text(encoding="utf-8"))
    assert manifest["main"] == "main.cjs"
    assert manifest["scripts"]["build"] == "node --check main.cjs"
    assert manifest["devDependencies"]["electron"] == "^33.4.11"
    assert (app_dir / "main.cjs").is_file()
    assert (app_dir / "tests" / "main.test.cjs").is_file()

def test_pnpm_member_rolls_back_on_verification_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Restore workspace metadata and remove the member when verification fails."""
    _write_pnpm_workspace(tmp_path)
    workspace_before = (tmp_path / "pnpm-workspace.yaml").read_bytes()
    cog_before = (tmp_path / "cog.toml").read_bytes()
    spec = build_member_spec(
        project_path=tmp_path,
        name="broken-member",
        ecosystem=WorkspaceEcosystem.PNPM,
        member_type="ts-lib",
        no_install=True,
        no_verify=False,
    )

    def fail_verification(_spec):
        raise RuntimeError("verification failed")

    monkeypatch.setattr(pnpm_provider, "_verify", fail_verification)
    with pytest.raises(RuntimeError, match="verification failed"):
        add_member(spec)

    assert not (tmp_path / "packages" / "broken-member").exists()
    assert (tmp_path / "pnpm-workspace.yaml").read_bytes() == workspace_before
    assert (tmp_path / "cog.toml").read_bytes() == cog_before


def test_generated_member_contracts_include_runtime_test_requirements(tmp_path: Path):
    """Keep browser test environments and library build entries self-contained."""
    _write_pnpm_workspace(tmp_path)
    for name, member_type in (("react", "react-app"), ("vue", "vue-app"), ("ui", "react-lib")):
        spec = build_member_spec(
            project_path=tmp_path,
            name=name,
            ecosystem=WorkspaceEcosystem.PNPM,
            member_type=member_type,
            no_install=True,
            no_verify=True,
        )
        add_member(spec)

    react_manifest = json.loads((tmp_path / "apps/react/package.json").read_text(encoding="utf-8"))
    vue_manifest = json.loads((tmp_path / "apps/vue/package.json").read_text(encoding="utf-8"))
    assert "jsdom" in react_manifest["devDependencies"]
    assert "happy-dom" in vue_manifest["devDependencies"]
    assert 'src/index.tsx' in (tmp_path / "packages/ui/vite.config.ts").read_text(encoding="utf-8")
