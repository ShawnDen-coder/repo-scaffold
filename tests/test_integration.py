"""Integration tests for the repo-scaffold system.

Tests the complete workflow from component selection to project generation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from repo_scaffold.core.component_manager import ComponentManager
from repo_scaffold.core.cookiecutter_runner import CookiecutterRunner
from repo_scaffold.core.template_composer import TemplateComposer


@pytest.fixture
def integration_test_setup():
    """Set up a complete test environment with components and templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)

        # Create components directory
        components_dir = base_dir / "components"
        components_dir.mkdir()

        # Create python_core component
        python_core_dir = components_dir / "python_core"
        python_core_dir.mkdir()
        python_core_files_dir = python_core_dir / "files"
        python_core_files_dir.mkdir()

        python_core_config = {
            "name": "python_core",
            "display_name": "Python Core",
            "description": "Core Python project structure",
            "category": "core",
            "dependencies": [],
            "conflicts": [],
            "cookiecutter_vars": {"use_python": True, "python_version": "3.12"},
            "files": [
                {"src": "pyproject.toml.j2", "dest": "pyproject.toml"},
                {"src": "src/__init__.py.j2", "dest": "src/{{cookiecutter.package_name}}/__init__.py"},
            ],
            "hooks": {"post_gen": ["setup_python_env"]},
        }

        with open(python_core_dir / "component.yaml", "w") as f:
            yaml.dump(python_core_config, f)

        # Create component files
        pyproject_template = """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{cookiecutter.package_name}}"
version = "{{cookiecutter.version}}"
description = "{{cookiecutter.description}}"
authors = [{name = "{{cookiecutter.author_name}}", email = "{{cookiecutter.author_email}}"}]
"""

        with open(python_core_files_dir / "pyproject.toml.j2", "w") as f:
            f.write(pyproject_template)

        # Create src subdirectory for the init template
        src_dir = python_core_files_dir / "src"
        src_dir.mkdir()

        init_template = '"""{{cookiecutter.description}}"""\n\n__version__ = "{{cookiecutter.version}}"\n'

        with open(src_dir / "__init__.py.j2", "w") as f:
            f.write(init_template)

        # Create cli_support component
        cli_support_dir = components_dir / "cli_support"
        cli_support_dir.mkdir()
        cli_support_files_dir = cli_support_dir / "files"
        cli_support_files_dir.mkdir()

        cli_support_config = {
            "name": "cli_support",
            "display_name": "CLI Support",
            "description": "Command line interface support",
            "category": "feature",
            "dependencies": ["python_core"],
            "conflicts": [],
            "cookiecutter_vars": {"use_cli": True, "cli_framework": "click"},
            "files": [{"src": "cli.py.j2", "dest": "src/{{cookiecutter.package_name}}/cli.py"}],
            "hooks": {"post_gen": ["setup_cli_entry_point"]},
        }

        with open(cli_support_dir / "component.yaml", "w") as f:
            yaml.dump(cli_support_config, f)

        cli_template = """import click

@click.command()
def main():
    \"\"\"{{cookiecutter.description}}\"\"\"
    click.echo("Hello from {{cookiecutter.project_name}}!")

if __name__ == "__main__":
    main()
"""

        with open(cli_support_files_dir / "cli.py.j2", "w") as f:
            f.write(cli_template)

        # Create templates directory
        templates_dir = base_dir / "templates"
        templates_dir.mkdir()

        # Create template config
        template_config = {
            "name": "python-library",
            "display_name": "Python Library",
            "description": "Create a Python library project",
            "required_components": ["python_core"],
            "optional_components": {
                "cli_support": {
                    "prompt": "Add CLI support?",
                    "help": "Adds Click-based command line interface",
                    "default": False,
                }
            },
            "base_cookiecutter_config": {
                "project_name": "My Python Library",
                "package_name": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
                "author_name": "Your Name",
                "author_email": "your.email@example.com",
                "version": "0.1.0",
                "description": "A short description of the project",
                "license": ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"],
                "python_version": "3.12",
            },
        }

        with open(templates_dir / "python-library.yaml", "w") as f:
            yaml.dump(template_config, f)

        yield {
            "base_dir": base_dir,
            "components_dir": components_dir,
            "templates_dir": templates_dir,
            "template_config": template_config,
        }


def test_component_manager_integration(integration_test_setup):
    """Test ComponentManager with real component files."""
    setup = integration_test_setup

    manager = ComponentManager(setup["components_dir"])

    # Test component discovery
    assert len(manager.components) == 2
    assert "python_core" in manager.components
    assert "cli_support" in manager.components

    # Test component properties
    python_core = manager.components["python_core"]
    assert python_core.name == "python_core"
    assert python_core.display_name == "Python Core"
    assert python_core.dependencies == []

    cli_support = manager.components["cli_support"]
    assert cli_support.name == "cli_support"
    assert cli_support.dependencies == ["python_core"]

    # Test dependency resolution
    resolved = manager.resolve_dependencies(["cli_support"])
    assert set(resolved) == {"python_core", "cli_support"}

    # Test validation
    conflicts = manager.validate_selection(["python_core", "cli_support"])
    assert conflicts == []


def test_template_composer_integration(integration_test_setup):
    """Test TemplateComposer with real components."""
    setup = integration_test_setup

    manager = ComponentManager(setup["components_dir"])
    composer = TemplateComposer(manager)

    # Test template composition
    selected_components = ["cli_support"]  # This should include python_core via dependency

    with patch("tempfile.mkdtemp") as mock_mkdtemp:
        temp_template_dir = setup["base_dir"] / "temp_template"
        temp_template_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_template_dir)

        result = composer.compose_template(setup["template_config"], selected_components)

        assert result == temp_template_dir

        # Check that cookiecutter.json was created
        cookiecutter_json_path = temp_template_dir / "cookiecutter.json"
        assert cookiecutter_json_path.exists()

        with open(cookiecutter_json_path) as f:
            cookiecutter_config = json.load(f)

        # Check base configuration
        assert cookiecutter_config["project_name"] == "My Python Library"
        assert cookiecutter_config["author_name"] == "Your Name"

        # Check component variables
        assert cookiecutter_config["use_python"] is True
        assert cookiecutter_config["python_version"] == "3.12"
        assert cookiecutter_config["use_cli"] is True
        assert cookiecutter_config["cli_framework"] == "click"


def test_cookiecutter_config_building(integration_test_setup):
    """Test cookiecutter configuration building with real components."""
    setup = integration_test_setup

    manager = ComponentManager(setup["components_dir"])
    composer = TemplateComposer(manager)

    components = ["python_core", "cli_support"]
    config = composer._build_cookiecutter_config(setup["template_config"], components)

    # Check that all variables are properly merged
    expected_vars = {
        "project_name": "My Python Library",
        "author_name": "Your Name",
        "author_email": "your.email@example.com",
        "version": "0.1.0",
        "use_python": True,
        "python_version": "3.12",
        "use_cli": True,
        "cli_framework": "click",
    }

    for key, value in expected_vars.items():
        assert config[key] == value


@patch("repo_scaffold.core.cookiecutter_runner.cookiecutter")
def test_full_workflow_integration(mock_cookiecutter, integration_test_setup):
    """Test the complete workflow from component selection to project generation."""
    setup = integration_test_setup

    # Initialize components
    manager = ComponentManager(setup["components_dir"])
    composer = TemplateComposer(manager)
    runner = CookiecutterRunner()

    # Select components (including dependency resolution)
    selected_components = ["cli_support"]
    resolved_components = manager.resolve_dependencies(selected_components)

    # Validate selection
    conflicts = manager.validate_selection(resolved_components)
    assert conflicts == []

    # Compose template
    with patch("tempfile.mkdtemp") as mock_mkdtemp:
        temp_template_dir = setup["base_dir"] / "temp_template"
        temp_template_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_template_dir)

        template_dir = composer.compose_template(setup["template_config"], selected_components)

        # Mock cookiecutter execution
        output_dir = setup["base_dir"] / "output"
        output_dir.mkdir()
        project_path = output_dir / "my_python_library"

        mock_cookiecutter.return_value = str(project_path)

        # Run cookiecutter
        result = runner.run_cookiecutter(template_dir, output_dir, no_input=True)

        # Verify the workflow
        assert result == project_path
        mock_cookiecutter.assert_called_once_with(str(template_dir), output_dir=str(output_dir), no_input=True)

        # Clean up
        runner.cleanup_temp_template(template_dir)


def test_error_handling_integration(integration_test_setup):
    """Test error handling in the integrated workflow."""
    setup = integration_test_setup

    manager = ComponentManager(setup["components_dir"])
    composer = TemplateComposer(manager)

    # Test missing component
    with pytest.raises(KeyError):
        manager.resolve_dependencies(["nonexistent_component"])

    # Test invalid template config - this should fail when resolving dependencies
    invalid_config = setup["template_config"].copy()
    invalid_config["required_components"] = ["nonexistent_component"]

    with pytest.raises(KeyError):
        # This should fail because required_components includes nonexistent_component
        composer.compose_template(invalid_config, [])


def test_component_file_merging_integration(integration_test_setup):
    """Test that component files are properly merged."""
    setup = integration_test_setup

    manager = ComponentManager(setup["components_dir"])
    composer = TemplateComposer(manager)

    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir) / "target"
        target_dir.mkdir()

        components = ["python_core", "cli_support"]
        composer._merge_component_files(components, target_dir)

        # Check that files were copied
        expected_files = [
            target_dir / "pyproject.toml",
            target_dir / "src" / "{{cookiecutter.package_name}}" / "__init__.py",
            target_dir / "src" / "{{cookiecutter.package_name}}" / "cli.py",
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected file {file_path} was not created"
            assert file_path.stat().st_size > 0, f"File {file_path} is empty"


def test_hooks_integration(integration_test_setup):
    """Test that hooks are properly created and combined."""
    setup = integration_test_setup

    manager = ComponentManager(setup["components_dir"])
    composer = TemplateComposer(manager)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_template_dir = Path(temp_dir)

        components = ["python_core", "cli_support"]
        composer._create_hooks(components, temp_template_dir)

        # Check that hooks directory was created
        hooks_dir = temp_template_dir / "hooks"
        assert hooks_dir.exists()

        # Check that post_gen_project.py was created
        post_gen_hook = hooks_dir / "post_gen_project.py"
        assert post_gen_hook.exists()

        # Check that hook content includes both components' hooks
        hook_content = post_gen_hook.read_text()
        assert "setup_python_env" in hook_content
        assert "setup_cli_entry_point" in hook_content
