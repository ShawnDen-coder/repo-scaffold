import os

import click
from cookiecutter.main import cookiecutter


@click.group()
def cli():
    """CLI tool for project creation"""
    ...


@cli.command()
@click.option('--template', '-t', default='https://github.com/your-template-repo.git',
              help='Cookiecutter template URL or path')
@click.option('--output-dir', '-o', default='.', help='Where to output the generated project dir')
@click.option('--local', '-l', is_flag=True, help='Use local template in ./template-python')
def create(template, output_dir, local):
    """Create a new project from a Cookiecutter template"""
    if local:
        template = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    cookiecutter(
        template=template,
        output_dir=output_dir,
        no_input=False
    )


if __name__ == '__main__':
    cli()
