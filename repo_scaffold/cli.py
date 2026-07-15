"""Repository scaffolding CLI tool.

This module provides a command-line interface for creating new projects from templates.
It serves as the main entry point for the repo-scaffold tool.

Example:
    To use this module as a CLI tool:

    ```bash
    # List available templates
    $ repo-scaffold list

    # Create a new project
    $ repo-scaffold create python
    ```

    To use this module in your code:

    ```python
    from repo_scaffold.cli import cli

    if __name__ == '__main__':
        cli()
    ```
"""

import importlib.resources
import json
import os
from pathlib import Path
from typing import Any

import click
from cookiecutter.main import cookiecutter

from repo_scaffold.github_init import GhInitClient
from repo_scaffold.github_init import build_config
from repo_scaffold.github_init import init_repository


def get_package_path(relative_path: str) -> str:
    """Get absolute path to a resource in the package.

    Args:
        relative_path: Path relative to the package root

    Returns:
        str: Absolute path to the resource
    """
    # 使用 files() 获取包资源
    package_files = importlib.resources.files("repo_scaffold")
    resource_path = package_files.joinpath(relative_path)
    if not (resource_path.is_file() or resource_path.is_dir()):
        raise FileNotFoundError(f"Resource not found: {relative_path}")
    return str(resource_path)


def load_templates() -> dict[str, Any]:
    """Load available project templates configuration.

    Reads template configurations from the cookiecutter.json file in the templates directory.
    Each template contains information about its name, path, title, and description.

    Returns:
        Dict[str, Any]: Template configuration dictionary where keys are template names
            and values are template information:
            {
                "template-name": {
                    "path": "relative/path",
                    "title": "Template Title",
                    "description": "Template description"
                }
            }

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        json.JSONDecodeError: If the configuration file is not valid JSON
    """
    config_path = get_package_path("templates/cookiecutter.json")
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    return config["templates"]


@click.group()
def cli():
    """Modern project scaffolding tool.

    Provides multiple project templates for quick project initialization.
    Use `repo-scaffold list` to view available templates,
    or `repo-scaffold create <template>` to create a new project.
    """


@cli.command()
def list():
    """List all available project templates.

    Displays the title and description of each template to help users
    choose the appropriate template for their needs.

    Example:
        ```bash
        $ repo-scaffold list
        Available templates:

        python - template-python
          Description: template for python project
        ```
    """
    templates = load_templates()
    click.echo("\nAvailable templates:")
    for name, info in templates.items():
        click.echo(f"\n{info['title']} - {name}")
        click.echo(f"  Description: {info['description']}")


@cli.command()
@click.argument("template", required=False)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory where the project will be created",
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json file content",
)
@click.option(
    "--no-install",
    is_flag=True,
    help="Generate the project without running post-generation dependency installation",
)
@click.option(
    "--no-git",
    is_flag=True,
    help="Generate the project without initializing a git repository (default branch: master)",
)
def create(template: str, output_dir: Path, no_input: bool, no_install: bool, no_git: bool):
    """Create a new project from a template.

    Creates a new project based on the specified template. If no template is specified,
    displays a list of available templates. The project generation process is interactive
    and will prompt for necessary configuration values.

    Args:
        template: Template name or title (e.g., 'template-python' or 'python')
        output_dir: Target directory where the project will be created
        no_input: Do not prompt for parameters and only use cookiecutter defaults
        no_install: Skip post-generation dependency installation
        no_git: Skip git repository initialization (otherwise inits on branch master)

    Example:
        Create a Python project:
            ```bash
            $ repo-scaffold create python
            ```

        Specify output directory:
            ```bash
            $ repo-scaffold create python -o ./projects
            ```

        View available templates:
            ```bash
            $ repo-scaffold list
            ```
    """
    templates = load_templates()

    # 如果没有指定模板,让 cookiecutter 处理模板选择
    if not template:
        click.echo("Please select a template to use:")
        for name, info in templates.items():
            click.echo(f"  {info['title']} - {name}")
            click.echo(f"    {info['description']}")
        return

    # 查找模板配置
    template_info = None
    for name, info in templates.items():
        if name == template or info["title"] == template:
            template_info = info
            break

    if not template_info:
        click.echo(f"Error: Template '{template}' not found")
        click.echo("\nAvailable templates:")
        for name, info in templates.items():
            click.echo(f"  {info['title']} - {name}")
        return

    # 使用模板创建项目
    template_path = get_package_path(os.path.join("templates", template_info["path"]))
    cookiecutter(
        template=template_path,
        output_dir=str(output_dir),
        no_input=no_input,  # 根据用户选择决定是否启用交互式输入
        extra_context={
            "install_after_generate": "no" if no_install else "yes",
            "init_git": "no" if no_git else "yes",
        },
    )


@cli.command("gh-init")
@click.argument(
    "project_path",
    type=click.Path(file_okay=False, dir_okay=True, exists=True, path_type=Path),
)
@click.option("--owner", help="GitHub user or org (default: authenticated user).")
@click.option("--name", help="Repository name (default: from pyproject.toml).")
@click.option(
    "--description",
    help="Repository description (default: from pyproject.toml).",
)
@click.option(
    "--private/--public",
    default=False,
    help="Repository visibility (default: public).",
)
@click.option(
    "--default-branch",
    "default_branch",
    help="Default branch name (default: current local git branch or 'master').",
)
@click.option(
    "--allow-existing",
    is_flag=True,
    help="Don't fail if the repository already exists; refresh secrets/variables.",
)
@click.option("--no-push", is_flag=True, help="Skip git init and push.")
@click.option(
    "--no-pages",
    is_flag=True,
    help="Skip creating the gh-pages branch and configuring GitHub Pages.",
)
@click.option(
    "--protect-branch",
    is_flag=True,
    help="Protect the default branch (require PR review; admins can still push for releases).",
)
@click.option(
    "--force-push",
    is_flag=True,
    help="Use --force when pushing the initial commit.",
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Don't prompt; missing optional secrets are skipped.",
)
def gh_init(
    project_path: Path,
    owner: str | None,
    name: str | None,
    description: str | None,
    private: bool,
    default_branch: str | None,
    allow_existing: bool,
    no_push: bool,
    no_pages: bool,
    protect_branch: bool,
    force_push: bool,
    no_input: bool,
):
    """Initialize a GitHub repository for an already-generated project.

    Creates the repository on GitHub, sets the CI secrets and variables that
    the generated workflows expect, and (unless --no-push is given) pushes the
    project's initial commit to the new repo.

    Authentication: reads the ``GITHUB_TOKEN`` environment variable. The token
    must have ``repo`` scope for private repos, ``public_repo`` for public
    ones.
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise click.ClickException(
            "GITHUB_TOKEN environment variable is required. "
            "Generate a personal access token with `repo` scope at "
            "https://github.com/settings/tokens and export it before running gh-init."
        )

    prompter = None
    if not no_input:

        def prompter(key: str, default: str | None) -> str:
            hide = key.endswith(("_TOKEN", "_PASSWORD"))
            return click.prompt(
                f"{key} (Enter to skip)" if default is None else key,
                default=default if default is not None else "",
                hide_input=hide,
                show_default=default is not None,
            )

    config = build_config(
        project_path=project_path,
        owner=owner,
        name=name,
        description=description,
        private=private,
        default_branch=default_branch,
        push=not no_push,
        force_push=force_push,
        allow_existing=allow_existing,
        setup_pages=not no_pages,
        protect_branch=protect_branch,
        prompter=prompter,
    )

    click.echo("")
    click.echo("Will create or update repository:")
    owner_source = getattr(config, "_owner_source", None)
    owner_suffix = f"  (owner <- {owner_source})" if owner_source and owner_source != "flag" else ""
    click.echo(f"  Repo:        {config.owner or '<authenticated user>'}/{config.name}{owner_suffix}")
    click.echo(f"  Visibility:  {'private' if config.private else 'public'}")
    click.echo(f"  Description: {config.description or '(none)'}")
    click.echo(f"  Branch:      {config.default_branch}")
    secrets_listed = ", ".join(config.secrets) or "(none)"
    variables_listed = ", ".join(f"{k}={v}" for k, v in config.variables.items()) or "(none)"
    click.echo(f"  Secrets:     {secrets_listed}")
    click.echo(f"  Variables:   {variables_listed}")
    click.echo(f"  Push:        {'yes' if config.push else 'no'}{' (force)' if config.force_push else ''}")
    has_docs = (config.project_path / "mkdocs.yml").is_file()
    if config.setup_pages and config.push and has_docs:
        pages_plan = "yes (mkdocs gh-deploy -> Pages source + repo website)"
    elif config.setup_pages and config.push and not has_docs:
        pages_plan = "no (no mkdocs.yml in project)"
    else:
        pages_plan = "no"
    click.echo(f"  Pages:       {pages_plan}")
    protect_plan = "yes (require PR review)" if (config.protect_branch and config.push) else "no"
    click.echo(f"  Protection:  {protect_plan} -> {config.default_branch}")
    click.echo("")

    if not no_input:
        click.confirm("Proceed?", default=True, abort=True)

    result = init_repository(config, GhInitClient(token))

    click.echo("")
    click.echo("✓ Repository ready")
    click.echo(f"  URL:     {result.html_url}")
    click.echo(f"  Actions: {result.actions_url}")
    if result.pages_configured:
        click.echo(f"  Pages:   {result.pages_url}")
    else:
        click.echo(f"  Pages:   {result.pages_url} (after first docs-deploy run)")
    if result.skipped_secrets:
        click.echo(f"  Skipped secrets (set later in repo Settings): {', '.join(result.skipped_secrets)}")
    if result.pushed:
        click.echo(f"  Pushed initial commit to {config.default_branch}")
    if result.pages_configured:
        click.echo(f"  Built & deployed docs to '{result.pages_branch}' and enabled GitHub Pages")
        if result.homepage_set:
            click.echo(f"  Set repository website to {result.pages_url}")
    elif result.pages_error:
        click.echo(f"  ⚠️  Could not deploy docs / configure Pages automatically: {result.pages_error}")
    if result.branch_protected:
        click.echo(f"  Protected branch '{config.default_branch}' (PR review required)")
    elif result.protection_error:
        click.echo(f"  ⚠️  Could not protect '{config.default_branch}': {result.protection_error}")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Watch the first CI run on the Actions page above.")
    if result.pages_configured:
        click.echo(f"  2. Your docs are live at {result.pages_url}")
        click.echo("     (re-published automatically by docs-deploy on each version tag).")
    elif result.pages_error:
        click.echo("  2. Docs deploy failed above — fix it, then run `just deploy-gh-pages`")
        click.echo("     and set Settings → Pages source to gh-pages / (root) if needed.")
    else:
        click.echo("  2. After the first docs-deploy tag run, in repo Settings → Pages set")
        click.echo("     'Source: Deploy from a branch' to gh-pages / (root).")


@cli.command("add-package")
@click.argument("name")
@click.option(
    "--project-path",
    "-p",
    default=".",
    type=click.Path(file_okay=False, dir_okay=True, exists=True, path_type=Path),
    help="Path to the workspace project root (default: current directory)",
)
def add_package_cmd(name: str, project_path: Path):
    """Add a new package to a workspace project.

    Detects the project type (Rust cargo workspace or uv workspace) and creates
    the package skeleton, updates cog.toml, and verifies the workspace compiles.

    Run this inside a generated workspace project directory, or specify --project-path.
    """
    from repo_scaffold.add_package import add_package

    add_package(project_path, name)


if __name__ == "__main__":
    cli()
