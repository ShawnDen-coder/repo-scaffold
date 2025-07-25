"""Integration tests for template composition and generation."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from repo_scaffold.core.component_manager import ComponentManager
from repo_scaffold.core.template_composer import TemplateComposer


@pytest.fixture
def components_dir():
    """Get the components directory."""
    return Path(__file__).parent.parent.parent / "repo_scaffold" / "components"


@pytest.fixture
def templates_dir():
    """Get the templates directory."""
    return Path(__file__).parent.parent.parent / "repo_scaffold" / "templates"


@pytest.fixture
def component_manager(components_dir):
    """Create a component manager instance."""
    return ComponentManager(components_dir)


@pytest.fixture
def template_composer(component_manager):
    """Create a template composer instance."""
    return TemplateComposer(component_manager)


@pytest.fixture
def python_library_config(templates_dir):
    """Load the python-library template configuration."""
    config_path = templates_dir / "python-library.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_component_discovery(component_manager):
    """Test that all expected components are discovered."""
    components = component_manager._discover_components()

    expected_components = {
        "python_core",
        "mkdocs",
        "pre_commit",
        "task_automation",
        "podman",
        "github_actions",
        "pypi",
    }

    assert len(components) >= len(expected_components)
    for comp_name in expected_components:
        assert comp_name in components
        assert hasattr(components[comp_name], "display_name")
        assert hasattr(components[comp_name], "description")


def test_python_library_template_config(python_library_config):
    """Test python-library template configuration."""
    assert python_library_config["name"] == "python-library"
    assert python_library_config["display_name"] == "Python Library"

    required_components = python_library_config.get("required_components", [])
    expected_required = [
        "python_core",
        "mkdocs",
        "pre_commit",
        "task_automation",
        "podman",
        "github_actions",
        "pypi",
    ]

    assert set(required_components) == set(expected_required)
    assert python_library_config.get("optional_components") == []


def test_dependency_resolution(component_manager, python_library_config):
    """Test dependency resolution for python-library template."""
    required_components = python_library_config.get("required_components", [])
    resolved = component_manager.resolve_dependencies(required_components)

    # All required components should be in resolved list
    for comp in required_components:
        assert comp in resolved

    # Should not have duplicates
    assert len(resolved) == len(set(resolved))


def test_conflict_validation(component_manager, python_library_config):
    """Test conflict validation for python-library template."""
    required_components = python_library_config.get("required_components", [])
    resolved = component_manager.resolve_dependencies(required_components)
    conflicts = component_manager.validate_selection(resolved)

    # Should have no conflicts
    assert conflicts == []

    def test_template_composition(self, template_composer, python_library_config):
        """Test template composition creates all expected files."""
        required_components = python_library_config.get("required_components", [])

        composed_template = template_composer.compose_template(python_library_config, required_components)

        # Check cookiecutter.json exists
        cookiecutter_json = composed_template / "cookiecutter.json"
        assert cookiecutter_json.exists()

        # Load and validate cookiecutter config
        with open(cookiecutter_json, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Check base config is present
        base_config = python_library_config.get("base_cookiecutter_config", {})
        for key in base_config:
            assert key in config

    def test_component_files_included(self, template_composer, python_library_config):
        """Test that all component files are included in composed template."""
        required_components = python_library_config.get("required_components", [])

        composed_template = template_composer.compose_template(python_library_config, required_components)

        template_root = composed_template / "{{cookiecutter.package_name}}"

        # Check python_core files
        assert (template_root / "pyproject.toml").exists()
        assert (template_root / "README.md").exists()
        assert (template_root / ".gitignore").exists()
        assert (template_root / ".ruff.toml").exists()

        # Check podman files
        assert (template_root / "container" / "Containerfile").exists()
        assert (template_root / "container" / "compose.yml").exists()
        assert (template_root / "container" / ".containerignore").exists()

        # Check github_actions files
        workflows_dir = template_root / ".github" / "workflows"
        assert (workflows_dir / "ci-tests.yaml").exists()
        assert (workflows_dir / "container-release.yaml").exists()
        assert (workflows_dir / "package-release.yaml").exists()

        # Check mkdocs files
        assert (template_root / "mkdocs.yml").exists()
        assert (template_root / "docs" / "index.md").exists()

        # Check task_automation files
        assert (template_root / "Taskfile.yml").exists()

    def test_template_syntax_validation(self, template_composer, python_library_config):
        """Test that composed template has valid Jinja2 syntax."""
        required_components = python_library_config.get("required_components", [])

        composed_template = template_composer.compose_template(python_library_config, required_components)

        # Try to render a simple template to check syntax
        from jinja2 import Environment
        from jinja2 import FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(composed_template)))

        # Test key template files
        template_files = [
            "{{cookiecutter.package_name}}/pyproject.toml",
            "{{cookiecutter.package_name}}/container/Containerfile",
            "{{cookiecutter.package_name}}/Taskfile.yml",
        ]

        for template_file in template_files:
            try:
                template = env.get_template(template_file)
                # Just getting the template should validate syntax
                assert template is not None
            except Exception as e:
                pytest.fail(f"Template syntax error in {template_file}: {e}")

    @patch("cookiecutter.main.cookiecutter")
    def test_end_to_end_generation(self, mock_cookiecutter, template_composer, python_library_config):
        """Test end-to-end project generation."""
        required_components = python_library_config.get("required_components", [])

        # Compose template
        composed_template = template_composer.compose_template(python_library_config, required_components)

        # Mock cookiecutter call
        mock_cookiecutter.return_value = "/fake/output/path"

        # Simulate cookiecutter call
        from cookiecutter.main import cookiecutter

        test_context = {
            "project_name": "Test Service",
            "package_name": "test_service",
            "project_slug": "test-service",
            "author_name": "Test User",
            "author_email": "test@example.com",
            "github_username": "testuser",
            "version": "0.1.0",
            "description": "A test service",
            "python_version": "3.12",
            "license": "MIT",
        }

        result = cookiecutter(str(composed_template), no_input=True, extra_context=test_context, output_dir="/tmp")

        # Verify cookiecutter was called
        mock_cookiecutter.assert_called_once()
        assert result == "/fake/output/path"

    def test_component_conflicts(self, component_manager):
        """Test that conflicting components are properly detected."""
        # Test podman conflicts with docker (if docker component exists)
        components = component_manager._discover_components()

        if "podman" in components:
            podman_component = components["podman"]
            conflicts = getattr(podman_component, "conflicts", [])

            # Podman should conflict with docker and airflow_docker
            expected_conflicts = {"docker", "airflow_docker"}
            assert set(conflicts) == expected_conflicts

    def test_cookiecutter_variables(self, template_composer, python_library_config):
        """Test that all component cookiecutter variables are included."""
        required_components = python_library_config.get("required_components", [])

        composed_template = template_composer.compose_template(python_library_config, required_components)

        cookiecutter_json = composed_template / "cookiecutter.json"
        with open(cookiecutter_json, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Check that component-specific variables are present
        expected_vars = {
            "use_podman",
            "use_containers",
            "container_runtime",
            "use_github_actions",
            "use_private_pypi",
            "use_task",
            "use_uv",
        }

        for var in expected_vars:
            assert var in config, f"Missing cookiecutter variable: {var}"
