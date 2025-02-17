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
from typing import Dict

import click
from cookiecutter.main import cookiecutter


def get_package_path(relative_path: str) -> str:
    """Get absolute path to a resource in the package.

    Args:
        relative_path: Path relative to the package root

    Returns:
        str: Absolute path to the resource
    """  # noqa: W293
    # 使用 files() 获取包资源
    package_files = importlib.resources.files("repo_scaffold")
    resource_path = package_files.joinpath(relative_path)
    if not (resource_path.is_file() or resource_path.is_dir()):
        raise FileNotFoundError(f"Resource not found: {relative_path}")
    return str(resource_path)


def load_templates() -> Dict[str, Any]:
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
    with open(config_path, "r", encoding="utf-8") as f:
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
    """  # noqa: W293
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
def create(template: str, output_dir: Path):
    """Create a new project from a template.

    Creates a new project based on the specified template. If no template is specified,
    displays a list of available templates. The project generation process is interactive
    and will prompt for necessary configuration values.

    Args:
        template: Template name or title (e.g., 'template-python' or 'python')
        output_dir: Target directory where the project will be created

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
    """  # noqa: W293
    templates = load_templates()

    # 如果没有指定模板，让 cookiecutter 处理模板选择
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
        no_input=False,  # 启用交互式输入，让 cookiecutter 处理所有选项
    )


if __name__ == "__main__":
    cli()
