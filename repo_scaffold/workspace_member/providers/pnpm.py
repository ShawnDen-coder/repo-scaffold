"""pnpm workspace-member provider."""

from __future__ import annotations

import importlib.resources
import json
import shutil
import subprocess

import click
from cookiecutter.main import cookiecutter

from ..cog import register_cog_member
from ..models import WorkspaceMemberSpec


def add_pnpm_member(spec: WorkspaceMemberSpec) -> None:
    """Create a pnpm member from a supported workspace-member template."""
    if spec.member_type not in {"node-service", "react-app", "react-lib", "ts-cli", "ts-lib", "vue-app"}:
        raise click.ClickException(
            f"Unsupported pnpm member type '{spec.member_type}'. "
            "Supported types: ts-lib, ts-cli, react-app, vue-app, react-lib, node-service."
        )
    if spec.member_path.exists():
        raise click.ClickException(
            f"❌ {spec.member_path.relative_to(spec.project_path)} already exists"
        )

    workspace_file = spec.project_path / "pnpm-workspace.yaml"
    cog_file = spec.project_path / "cog.toml"
    workspace_backup = workspace_file.read_bytes()
    cog_backup = cog_file.read_bytes() if cog_file.exists() else None
    _ensure_workspace_glob(spec)
    if spec.dry_run:
        click.echo(
            f"Would create pnpm {spec.member_type}: "
            f"{spec.member_path.relative_to(spec.project_path)}"
        )
        click.echo(f"Would register package: {spec.package_name}")
        return

    spec.member_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cookiecutter(
            template=str(_template_path(spec.member_type)),
            output_dir=str(spec.member_path.parent),
            no_input=True,
            extra_context=_template_context(spec),
        )
        _add_workspace_dependencies(spec)
        register_cog_member(spec)
        if not spec.no_install:
            subprocess.check_call(["pnpm", "install"], cwd=str(spec.project_path))
        if not spec.no_verify:
            _verify(spec)
    except Exception:
        if spec.member_path.exists():
            shutil.rmtree(spec.member_path)
        workspace_file.write_bytes(workspace_backup)
        if cog_backup is None:
            if cog_file.exists():
                cog_file.unlink()
        else:
            cog_file.write_bytes(cog_backup)
        raise
    click.echo(f"✅ pnpm member '{spec.package_name}' added.")


def _template_path(member_type: str):
    return importlib.resources.files("repo_scaffold").joinpath(
        "templates", "workspace_members", "pnpm", member_type
    )


def _template_context(spec: WorkspaceMemberSpec) -> dict[str, str | bool]:
    root_manifest = spec.project_path / "package.json"
    typescript_version = "~5.9.3"
    if root_manifest.is_file():
        data = json.loads(root_manifest.read_text(encoding="utf-8"))
        typescript_version = data.get("devDependencies", {}).get(
            "typescript", typescript_version
        )
    return {
        "member_name": spec.name,
        "package_name": spec.package_name,
        "private": spec.private,
        "typescript_version": typescript_version,
    }


def _ensure_workspace_glob(spec: WorkspaceMemberSpec) -> None:
    workspace_file = spec.project_path / "pnpm-workspace.yaml"
    content = workspace_file.read_text(encoding="utf-8")
    glob = f"{spec.location}/*"
    if glob in content:
        return
    if "packages:" not in content:
        raise click.ClickException("pnpm-workspace.yaml has no packages list.")
    if spec.dry_run:
        click.echo(f"Would add '{glob}' to pnpm-workspace.yaml")
        return
    workspace_file.write_text(content.rstrip() + f"\n  - {glob}\n", encoding="utf-8")


def _add_workspace_dependencies(spec: WorkspaceMemberSpec) -> None:
    if not spec.depends_on:
        return
    manifest_path = spec.member_path / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dependencies = manifest.setdefault("dependencies", {})
    for dependency in spec.depends_on:
        dependencies[dependency] = "workspace:*"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _verify(spec: WorkspaceMemberSpec) -> None:
    for script in ("typecheck", "test", "build"):
        subprocess.check_call(
            ["pnpm", "--filter", spec.package_name, script],
            cwd=str(spec.project_path),
        )
