"""Command line interface for repo-scaffold.

This module provides the main CLI commands for creating projects from templates.
"""

from pathlib import Path
from typing import Any

import click
import yaml

from repo_scaffold.core.component_manager import ComponentManager
from repo_scaffold.core.cookiecutter_runner import CookiecutterRunner
from repo_scaffold.core.template_composer import TemplateComposer


# Default paths - can be overridden by environment variables or config
DEFAULT_COMPONENTS_DIR = Path(__file__).parent / "components"
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"


@click.group()
@click.version_option()
def cli():
    """repo-scaffold: A modern project scaffolding tool with component-based architecture."""
    pass


@cli.command()
@click.option("--template", "-t", help="Template name to use for project creation")
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Output directory for the generated project",
)
@click.option(
    "--no-input",
    is_flag=True,
    default=True,
    help="Do not prompt for parameters and only use cookiecutter.json file content (default: True)",
)
@click.option(
    "--input",
    "prompt_input",
    is_flag=True,
    help="Prompt for parameters interactively (overrides --no-input)",
)
def create(template: str | None, output: Path, no_input: bool, prompt_input: bool):
    """Create a new project from a template.

    By default, uses template defaults without prompting (--no-input).
    Use --input to enable interactive prompts for customization.
    """
    try:
        # Determine if we should prompt for input
        # --input flag overrides the default --no-input behavior
        should_prompt = prompt_input or not no_input

        if template:
            # Use specified template
            template_config = load_template_config(template)
            template_name = template
        else:
            # Interactive template selection (only if prompting is enabled)
            if should_prompt:
                template_name, template_config = interactive_template_selection()
            else:
                # Use default template when no input is requested
                template_name = "python-library"
                template_config = load_template_config(template_name)

        # Component selection
        if should_prompt:
            # Interactive component selection
            selected_components = interactive_component_selection(template_config)
        else:
            # Use all required components when no input is requested
            selected_components = template_config.get("required_components", [])

        # Initialize core components
        component_manager = ComponentManager(DEFAULT_COMPONENTS_DIR)
        composer = TemplateComposer(component_manager)
        runner = CookiecutterRunner()

        # Validate component selection
        conflicts = component_manager.validate_selection(selected_components)
        if conflicts:
            click.echo("❌ Component conflicts detected:")
            for conflict in conflicts:
                click.echo(f"  - {conflict}")
            raise click.Abort()

        # Compose template
        click.echo("🔧 Composing template...")
        temp_template_dir = composer.compose_template(template_config, selected_components)

        try:
            # Run cookiecutter
            click.echo("🚀 Generating project...")
            project_path = runner.run_cookiecutter(temp_template_dir, output, no_input=not should_prompt)

            click.echo(f"✅ Project created successfully at: {project_path}")

        finally:
            # Clean up temporary template
            runner.cleanup_temp_template(temp_template_dir)

    except FileNotFoundError as e:
        click.echo(f"❌ Template not found: {e}")
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"❌ Error creating project: {e}")
        raise click.Abort() from e


@cli.command("list")
def list_templates():
    """List available templates."""
    try:
        templates = load_template_configs()

        if not templates:
            click.echo("No templates found.")
            return

        click.echo("Available templates:")
        click.echo()

        for template_name, config in templates.items():
            display_name = config.get("display_name", template_name)
            description = config.get("description", "No description available")
            click.echo(f"  {template_name}")
            click.echo(f"    {display_name}")
            click.echo(f"    {description}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error listing templates: {e}")
        raise click.Abort() from e


@cli.command()
def components():
    """List available components."""
    try:
        component_manager = ComponentManager(DEFAULT_COMPONENTS_DIR)
        components_list = component_manager.list_components()

        if not components_list:
            click.echo("No components found.")
            return

        click.echo("Available components:")
        click.echo()

        # Group by category
        by_category = {}
        for component in components_list:
            category = component.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(component)

        for category, comps in by_category.items():
            click.echo(f"📁 {category.title()}:")
            for component in comps:
                click.echo(f"  {component.name}")
                click.echo(f"    {component.display_name}")
                click.echo(f"    {component.description}")
                if component.dependencies:
                    click.echo(f"    Dependencies: {', '.join(component.dependencies)}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ Error listing components: {e}")
        raise click.Abort() from e


@cli.command("show")
@click.argument("template_name")
def show_template(template_name: str):
    """Show detailed information about a template."""
    try:
        template_config = load_template_config(template_name)

        click.echo(f"Template: {template_name}")
        click.echo(f"Display Name: {template_config.get('display_name', 'N/A')}")
        click.echo(f"Description: {template_config.get('description', 'N/A')}")
        click.echo()

        # Required components
        required = template_config.get("required_components", [])
        if required:
            click.echo("Required components:")
            for comp in required:
                click.echo(f"  - {comp}")
            click.echo()

        # Optional components
        optional = template_config.get("optional_components", {})
        if optional:
            click.echo("Optional components:")
            for comp_name, comp_config in optional.items():
                click.echo(f"  - {comp_name}")
                click.echo(f"    {comp_config.get('help', 'No description')}")
                click.echo(f"    Default: {comp_config.get('default', False)}")
            click.echo()

    except FileNotFoundError:
        click.echo(f"❌ Template '{template_name}' not found.")
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"❌ Error showing template: {e}")
        raise click.Abort() from e


def load_template_configs() -> dict[str, dict[str, Any]]:
    """Load all available template configurations."""
    templates = {}

    if not DEFAULT_TEMPLATES_DIR.exists():
        return templates

    for template_file in DEFAULT_TEMPLATES_DIR.glob("*.yaml"):
        try:
            with open(template_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            template_name = template_file.stem
            templates[template_name] = config

        except (OSError, yaml.YAMLError):
            # Skip invalid template files
            continue

    return templates


def load_template_config(template_name: str) -> dict[str, Any]:
    """Load a specific template configuration."""
    template_file = DEFAULT_TEMPLATES_DIR / f"{template_name}.yaml"

    if not template_file.exists():
        raise FileNotFoundError(f"Template '{template_name}' not found")

    with open(template_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def interactive_template_selection() -> tuple[str, dict[str, Any]]:
    """Interactive template selection."""
    templates = load_template_configs()

    if not templates:
        raise click.ClickException("No templates available")

    click.echo("Available templates:")
    template_list = list(templates.items())

    for i, (name, config) in enumerate(template_list, 1):
        display_name = config.get("display_name", name)
        description = config.get("description", "No description")
        click.echo(f"  {i}. {display_name}")
        click.echo(f"     {description}")

    while True:
        try:
            choice = click.prompt("Select a template", type=int)
            if 1 <= choice <= len(template_list):
                template_name, template_config = template_list[choice - 1]
                return template_name, template_config
            else:
                click.echo("Invalid choice. Please try again.")
        except click.Abort:
            raise
        except Exception:
            click.echo("Invalid input. Please enter a number.")


def interactive_component_selection(template_config: dict[str, Any]) -> list[str]:
    """Interactive component selection based on template configuration."""
    selected = []

    # Add required components
    required = template_config.get("required_components", [])
    selected.extend(required)

    # Interactive selection for optional components
    optional = template_config.get("optional_components", {})

    if optional:
        click.echo("\nOptional components:")

        for comp_name, comp_config in optional.items():
            prompt = comp_config.get("prompt", f"Include {comp_name}?")
            help_text = comp_config.get("help", "")
            default = comp_config.get("default", False)

            if help_text:
                click.echo(f"  {help_text}")

            if click.confirm(prompt, default=default):
                selected.append(comp_name)

    return selected


if __name__ == "__main__":
    cli()
