"""Command Line Interface module for project scaffolding.

This module provides the CLI commands for creating new projects using cookiecutter
templates. It serves as the main entry point for the repo_scaffold tool and handles
all command-line interactions.

Typical usage example:

    from repo_scaffold.cli import cli

    if __name__ == '__main__':
        cli()

Attributes:
    cli: The main Click command group that serves as the entry point.
"""

import os

import click
from cookiecutter.main import cookiecutter


@click.group()
def cli():
    """CLI tool for project creation.

    This function serves as the main command group for the CLI application.
    It groups all subcommands and provides the base entry point for the tool.
    """
    ...


@cli.command()
@click.option(
    "--template",
    "-t",
    default="https://github.com/ShawnDen-coder/repo-template.git",
    help="Cookiecutter template URL or path",
)
@click.option("--output-dir", "-o", default=".", help="Where to output the generated project dir")
@click.option("--local", "-l", is_flag=True, help="Use local template in ./template-python")
def create(template, output_dir, local):
    """Create a new project from a Cookiecutter template.

    Args:
        template (str): URL or path to the cookiecutter template.
        output_dir (str): Directory where the generated project will be created.
        local (bool): Flag to use local template instead of remote.

    Returns:
        None

    Example:
        $ repo_scaffold create --template https://github.com/user/template.git
        $ repo_scaffold create --local --output-dir ./projects
    """
    if local:
        template = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    cookiecutter(template=template, output_dir=output_dir, no_input=False)


if __name__ == "__main__":
    cli()
