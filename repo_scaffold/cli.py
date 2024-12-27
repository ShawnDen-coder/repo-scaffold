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
    """Repository scaffolding CLI tool.

    A tool for creating new projects from templates.
    """
    ...


@cli.command()
@click.option(
    "--template",
    "-t",
    default="https://github.com/ShawnDen-coder/repo-scaffold.git",
    help="Cookiecutter template URL or path",
)
@click.option("--output-dir", "-o", default=".", help="Where to output the generated project dir")
@click.option("--local", "-l", is_flag=True, help="Use local template in ./template-python")
def create(template, output_dir, local):
    r"""Create a new project from template.

    \b
    Usage:
        repo-scaffold create [OPTIONS]

    \b
    Examples:
        $ repo-scaffold create
        $ repo-scaffold create --local
        $ repo-scaffold create -o ./my-projects
        $ repo-scaffold create -t https://github.com/user/custom-template.git
        $ repo-scaffold create -t ../path/to/local/template
        $ repo-scaffold create -t gh:user/template-name
    """
    if local:
        template = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    cookiecutter(template=template, output_dir=output_dir, no_input=False)


if __name__ == "__main__":
    cli()
