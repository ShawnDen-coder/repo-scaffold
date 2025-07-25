"""Unit tests for CLI module.

Tests the command line interface using pytest-click.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from repo_scaffold.cli import cli
from repo_scaffold.cli import components as list_components
from repo_scaffold.cli import create
from repo_scaffold.cli import list_templates
from repo_scaffold.cli import show_template


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_templates_dir():
    """Create a temporary directory with test templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_dir = Path(temp_dir)

        # Create python-library template
        python_library_config = {
            "name": "python-library",
            "display_name": "Python Library",
            "description": "Create a Python library project",
            "required_components": ["python_core"],
            "optional_components": {
                "cli_support": {
                    "prompt": "Add CLI support?",
                    "help": "Adds Click-based command line interface",
                    "default": False,
                },
                "docker": {
                    "prompt": "Add Docker support?",
                    "help": "Includes Dockerfile and docker-compose.yml",
                    "default": False,
                },
            },
            "base_cookiecutter_config": {
                "project_name": "My Python Library",
                "package_name": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
                "author_name": "Your Name",
                "version": "0.1.0",
            },
        }

        with open(templates_dir / "python-library.yaml", "w") as f:
            yaml.dump(python_library_config, f)

        # Create python-cli template
        python_cli_config = {
            "name": "python-cli",
            "display_name": "Python CLI Application",
            "description": "Create a Python CLI application",
            "required_components": ["python_core", "cli_support"],
            "optional_components": {
                "docker": {"prompt": "Add Docker support?", "help": "Includes Dockerfile", "default": False}
            },
            "base_cookiecutter_config": {
                "project_name": "My CLI App",
                "package_name": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
                "author_name": "Your Name",
                "version": "0.1.0",
            },
        }

        with open(templates_dir / "python-cli.yaml", "w") as f:
            yaml.dump(python_cli_config, f)

        yield templates_dir


@pytest.fixture
def temp_components_dir():
    """Create a temporary directory with test components."""
    with tempfile.TemporaryDirectory() as temp_dir:
        components_dir = Path(temp_dir)

        # Create python_core component
        python_core_dir = components_dir / "python_core"
        python_core_dir.mkdir()

        python_core_config = {
            "name": "python_core",
            "display_name": "Python Core",
            "description": "Core Python project structure",
            "category": "core",
        }

        with open(python_core_dir / "component.yaml", "w") as f:
            yaml.dump(python_core_config, f)

        # Create cli_support component
        cli_support_dir = components_dir / "cli_support"
        cli_support_dir.mkdir()

        cli_support_config = {
            "name": "cli_support",
            "display_name": "CLI Support",
            "description": "Command line interface support",
            "category": "feature",
        }

        with open(cli_support_dir / "component.yaml", "w") as f:
            yaml.dump(cli_support_config, f)

        yield components_dir


def test_cli_help(cli_runner):
    """Test CLI help command."""
    result = cli_runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "repo-scaffold" in result.output
    assert "create" in result.output
    assert "list" in result.output


def test_cli_version(cli_runner):
    """Test CLI version command."""
    result = cli_runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "version" in result.output.lower()


@patch("repo_scaffold.cli.load_template_configs")
def test_list_templates_command(mock_load_configs, cli_runner, temp_templates_dir):
    """Test list templates command."""
    # Mock template loading
    mock_load_configs.return_value = {
        "python-library": {
            "name": "python-library",
            "display_name": "Python Library",
            "description": "Create a Python library project",
        },
        "python-cli": {
            "name": "python-cli",
            "display_name": "Python CLI Application",
            "description": "Create a Python CLI application",
        },
    }

    result = cli_runner.invoke(list_templates)

    assert result.exit_code == 0
    assert "python-library" in result.output
    assert "Python Library" in result.output
    assert "python-cli" in result.output
    assert "Python CLI Application" in result.output


@patch("repo_scaffold.cli.load_template_configs")
def test_list_templates_empty(mock_load_configs, cli_runner):
    """Test list templates command with no templates."""
    mock_load_configs.return_value = {}

    result = cli_runner.invoke(list_templates)

    assert result.exit_code == 0
    assert "No templates found" in result.output


@patch("repo_scaffold.cli.ComponentManager")
def test_list_components_command(mock_component_manager, cli_runner, temp_components_dir):
    """Test list components command."""
    # Mock component manager
    mock_manager = Mock()
    mock_component_manager.return_value = mock_manager

    # Mock components
    mock_python_core = Mock()
    mock_python_core.name = "python_core"
    mock_python_core.display_name = "Python Core"
    mock_python_core.description = "Core Python project structure"
    mock_python_core.category = "core"
    mock_python_core.dependencies = []  # Empty list, not Mock

    mock_cli_support = Mock()
    mock_cli_support.name = "cli_support"
    mock_cli_support.display_name = "CLI Support"
    mock_cli_support.description = "Command line interface support"
    mock_cli_support.category = "feature"
    mock_cli_support.dependencies = ["python_core"]  # Real list, not Mock

    mock_manager.components = {"python_core": mock_python_core, "cli_support": mock_cli_support}

    # Mock the list_components method
    mock_manager.list_components.return_value = [mock_python_core, mock_cli_support]

    result = cli_runner.invoke(list_components)

    assert result.exit_code == 0
    assert "python_core" in result.output
    assert "Python Core" in result.output
    assert "cli_support" in result.output
    assert "CLI Support" in result.output


@patch("repo_scaffold.cli.load_template_config")
def test_show_template_command(mock_load_config, cli_runner):
    """Test show template command."""
    # Mock template config
    mock_config = {
        "name": "python-library",
        "display_name": "Python Library",
        "description": "Create a Python library project",
        "required_components": ["python_core"],
        "optional_components": {"cli_support": {"prompt": "Add CLI support?", "default": False}},
    }

    mock_load_config.return_value = mock_config

    result = cli_runner.invoke(show_template, ["python-library"])

    assert result.exit_code == 0
    assert "python-library" in result.output
    assert "Python Library" in result.output
    assert "python_core" in result.output
    assert "cli_support" in result.output


@patch("repo_scaffold.cli.load_template_config")
def test_show_template_not_found(mock_load_config, cli_runner):
    """Test show template command with non-existent template."""
    mock_load_config.side_effect = FileNotFoundError("Template not found")

    result = cli_runner.invoke(show_template, ["nonexistent"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


@patch("repo_scaffold.cli.interactive_component_selection")
@patch("repo_scaffold.cli.TemplateComposer")
@patch("repo_scaffold.cli.CookiecutterRunner")
@patch("repo_scaffold.cli.load_template_config")
def test_create_command_with_template(mock_load_config, mock_runner, mock_composer, mock_selection, cli_runner):
    """Test create command with specified template and interactive input."""
    # Mock template config
    mock_config = {
        "name": "python-library",
        "display_name": "Python Library",
        "optional_components": {"cli_support": {"prompt": "Add CLI?", "default": False}},
    }
    mock_load_config.return_value = mock_config

    # Mock component selection
    mock_selection.return_value = ["python_core", "cli_support"]

    # Mock template composition
    mock_composer_instance = Mock()
    mock_composer.return_value = mock_composer_instance
    mock_composer_instance.compose_template.return_value = Path("/tmp/template")

    # Mock cookiecutter runner
    mock_runner_instance = Mock()
    mock_runner.return_value = mock_runner_instance
    mock_runner_instance.run_cookiecutter.return_value = Path("/tmp/output/project")

    result = cli_runner.invoke(create, ["--template", "python-library", "--input"])

    assert result.exit_code == 0
    mock_load_config.assert_called_once()
    mock_selection.assert_called_once()
    mock_composer_instance.compose_template.assert_called_once()
    mock_runner_instance.run_cookiecutter.assert_called_once()


@patch("repo_scaffold.cli.interactive_template_selection")
@patch("repo_scaffold.cli.interactive_component_selection")
@patch("repo_scaffold.cli.TemplateComposer")
@patch("repo_scaffold.cli.CookiecutterRunner")
def test_create_command_interactive(mock_runner, mock_composer, mock_comp_selection, mock_temp_selection, cli_runner):
    """Test create command with interactive template and component selection."""
    # Mock template selection
    mock_temp_selection.return_value = ("python-library", {"name": "python-library", "optional_components": {}})

    # Mock component selection
    mock_comp_selection.return_value = ["python_core"]

    # Mock template composition
    mock_composer_instance = Mock()
    mock_composer.return_value = mock_composer_instance
    mock_composer_instance.compose_template.return_value = Path("/tmp/template")

    # Mock cookiecutter runner
    mock_runner_instance = Mock()
    mock_runner.return_value = mock_runner_instance
    mock_runner_instance.run_cookiecutter.return_value = Path("/tmp/output/project")

    result = cli_runner.invoke(create, ["--input"])

    assert result.exit_code == 0
    mock_temp_selection.assert_called_once()
    mock_comp_selection.assert_called_once()


@patch("repo_scaffold.cli.TemplateComposer")
@patch("repo_scaffold.cli.CookiecutterRunner")
@patch("repo_scaffold.cli.load_template_config")
def test_create_command_default_no_input(mock_load_config, mock_runner, mock_composer, cli_runner):
    """Test create command with default no-input behavior."""
    # Mock template config
    mock_config = {
        "name": "python-library",
        "display_name": "Python Library",
        "required_components": ["python_core", "task_automation"],
    }
    mock_load_config.return_value = mock_config

    # Mock template composition
    mock_composer_instance = Mock()
    mock_composer.return_value = mock_composer_instance
    mock_composer_instance.compose_template.return_value = Path("/tmp/template")

    # Mock cookiecutter runner
    mock_runner_instance = Mock()
    mock_runner.return_value = mock_runner_instance
    mock_runner_instance.run_cookiecutter.return_value = Path("/tmp/output/project")

    # Test default behavior (should not prompt)
    result = cli_runner.invoke(create)

    assert result.exit_code == 0
    # Should load default python-library template
    mock_load_config.assert_called_once_with("python-library")
    # Should use no_input=True (not prompt)
    mock_runner_instance.run_cookiecutter.assert_called_once()
    call_args = mock_runner_instance.run_cookiecutter.call_args
    assert call_args[1]["no_input"] is True


@patch("repo_scaffold.cli.TemplateComposer")
@patch("repo_scaffold.cli.CookiecutterRunner")
@patch("repo_scaffold.cli.load_template_config")
def test_create_command_with_template_no_input(mock_load_config, mock_runner, mock_composer, cli_runner):
    """Test create command with specified template and default no-input behavior."""
    # Mock template config
    mock_config = {
        "name": "python-library",
        "display_name": "Python Library",
        "required_components": ["python_core", "task_automation"],
    }
    mock_load_config.return_value = mock_config

    # Mock template composition
    mock_composer_instance = Mock()
    mock_composer.return_value = mock_composer_instance
    mock_composer_instance.compose_template.return_value = Path("/tmp/template")

    # Mock cookiecutter runner
    mock_runner_instance = Mock()
    mock_runner.return_value = mock_runner_instance
    mock_runner_instance.run_cookiecutter.return_value = Path("/tmp/output/project")

    # Test with specified template (should not prompt by default)
    result = cli_runner.invoke(create, ["--template", "python-library"])

    assert result.exit_code == 0
    # Should load specified template
    mock_load_config.assert_called_once_with("python-library")
    # Should use no_input=True (not prompt)
    mock_runner_instance.run_cookiecutter.assert_called_once()
    call_args = mock_runner_instance.run_cookiecutter.call_args
    assert call_args[1]["no_input"] is True


@patch("repo_scaffold.cli.load_template_config")
def test_create_command_invalid_template(mock_load_config, cli_runner):
    """Test create command with invalid template."""
    mock_load_config.side_effect = FileNotFoundError("Template not found")

    result = cli_runner.invoke(create, ["--template", "invalid"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


@patch("repo_scaffold.cli.TemplateComposer")
def test_create_command_composition_error(mock_composer, cli_runner):
    """Test create command when template composition fails."""
    mock_composer_instance = Mock()
    mock_composer.return_value = mock_composer_instance
    mock_composer_instance.compose_template.side_effect = Exception("Composition failed")

    with patch("repo_scaffold.cli.load_template_config") as mock_load_config:
        mock_load_config.return_value = {"name": "test", "optional_components": {}}

        with patch("repo_scaffold.cli.interactive_component_selection") as mock_selection:
            mock_selection.return_value = ["python_core"]

            result = cli_runner.invoke(create, ["--template", "test"])

            assert result.exit_code != 0
            assert "error" in result.output.lower()


def test_create_command_help(cli_runner):
    """Test create command help."""
    result = cli_runner.invoke(create, ["--help"])

    assert result.exit_code == 0
    assert "template" in result.output
    assert "output" in result.output
