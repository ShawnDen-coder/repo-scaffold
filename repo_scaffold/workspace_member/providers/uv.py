"""uv workspace-member provider preserving the existing library workflow."""

from __future__ import annotations

import importlib.resources
import subprocess
import tomllib

import click
from cookiecutter.main import cookiecutter

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

    cookiecutter(
        template=str(importlib.resources.files("repo_scaffold").joinpath(
            "templates", "workspace_members", "uv", "python-lib"
        )),
        output_dir=str(spec.member_path.parent),
        no_input=True,
        extra_context=_template_context(spec),
    )
    register_cog_member(spec)
    if not spec.no_install:
        subprocess.check_call(
            ["uv", "sync", "--all-packages", "--all-groups"],
            cwd=str(spec.project_path),
        )
    click.echo(f"✅ uv member '{spec.name}' added.")


def _template_context(spec: WorkspaceMemberSpec) -> dict[str, str]:
    """Reuse project metadata when the workspace root exposes it."""
    context = {
        "member_name": spec.name,
        "package_name": spec.name,
        "package_module": spec.name.replace("-", "_"),
    }
    pyproject_path = spec.project_path / "pyproject.toml"
    if not pyproject_path.is_file():
        return context

    with pyproject_path.open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file).get("project", {})
    context.update(
        {
            "description": project.get("description", ""),
            "requires_python": project.get("requires-python", ">=3.12"),
        }
    )
    authors = project.get("authors", [{}])
    if authors:
        context["full_name"] = authors[0].get("name", "Your Name")
        context["email"] = authors[0].get("email", "you@example.com")
    return context
