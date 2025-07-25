"""Tests for Python Library template."""

from pathlib import Path

import pytest
import yaml

from repo_scaffold.core.component_manager import ComponentManager


@pytest.fixture
def templates_dir():
    """Get the templates directory."""
    return Path(__file__).parent.parent.parent / "repo_scaffold" / "templates"


@pytest.fixture
def components_dir():
    """Get the components directory."""
    return Path(__file__).parent.parent.parent / "repo_scaffold" / "components"


@pytest.fixture
def component_manager(components_dir):
    """Create a component manager instance."""
    return ComponentManager(components_dir)


@pytest.fixture
def python_library_config(templates_dir):
    """Load the python-library template configuration."""
    config_path = templates_dir / "python-library.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_python_library_template_exists(templates_dir):
    """Test that python-library template file exists."""
    template_path = templates_dir / "python-library.yaml"
    assert template_path.exists()


def test_python_library_basic_config(python_library_config):
    """Test python-library template basic configuration."""
    assert python_library_config["name"] == "python-library"
    assert python_library_config["display_name"] == "Python Library"
    assert "uv package management" in python_library_config["description"]


def test_python_library_required_components(python_library_config):
    """Test python-library template required components."""
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
    assert len(required_components) == len(expected_required)  # No duplicates


def test_python_library_no_optional_components(python_library_config):
    """Test that python-library template has no optional components."""
    optional_components = python_library_config.get("optional_components", [])
    assert optional_components == []


def test_python_library_base_config(python_library_config):
    """Test python-library template base cookiecutter configuration."""
    base_config = python_library_config.get("base_cookiecutter_config", {})

    # Check required fields
    required_fields = [
        "project_name",
        "package_name",
        "project_slug",
        "author_name",
        "author_email",
        "github_username",
        "version",
        "description",
        "python_min_version",
        "python_max_version",
        "license",
    ]

    for field in required_fields:
        assert field in base_config

    # Check default values
    assert base_config["project_name"] == "My Python Library"
    assert base_config["python_min_version"] == "3.10"
    assert base_config["python_max_version"] == "3.12"
    assert base_config["version"] == "0.1.0"

    # Check license options
    license_options = base_config["license"]
    assert isinstance(license_options, list)
    assert "MIT" in license_options
    assert "Apache-2.0" in license_options


def test_python_library_cookiecutter_variables(python_library_config):
    """Test that template uses proper cookiecutter variable syntax."""
    base_config = python_library_config.get("base_cookiecutter_config", {})

    # Check for proper Jinja2 syntax
    package_name = base_config.get("package_name", "")
    assert "{{" in package_name and "}}" in package_name

    project_slug = base_config.get("project_slug", "")
    assert "{{" in project_slug and "}}" in project_slug

    github_username = base_config.get("github_username", "")
    assert "{{" in github_username and "}}" in github_username


def test_all_required_components_exist(python_library_config, component_manager):
    """Test that all required components actually exist."""
    required_components = python_library_config.get("required_components", [])
    available_components = component_manager._discover_components()

    for comp_name in required_components:
        assert comp_name in available_components, f"Required component '{comp_name}' not found"


def test_dependency_resolution_works(python_library_config, component_manager):
    """Test that dependency resolution works for the template."""
    required_components = python_library_config.get("required_components", [])
    resolved = component_manager.resolve_dependencies(required_components)

    # All required components should be in resolved list
    for comp in required_components:
        assert comp in resolved

    # Should not have duplicates
    assert len(resolved) == len(set(resolved))


def test_no_conflicts_in_template(python_library_config, component_manager):
    """Test that template components have no conflicts."""
    required_components = python_library_config.get("required_components", [])
    resolved = component_manager.resolve_dependencies(required_components)
    conflicts = component_manager.validate_selection(resolved)

    # Should have no conflicts
    assert conflicts == [], f"Template has conflicts: {conflicts}"


def test_template_yaml_syntax(templates_dir):
    """Test that template YAML has valid syntax."""
    template_path = templates_dir / "python-library.yaml"

    with open(template_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Should be a valid dictionary
    assert isinstance(config, dict)

    # Should have required top-level keys
    required_keys = ["name", "display_name", "description", "required_components", "base_cookiecutter_config"]
    for key in required_keys:
        assert key in config


def test_template_for_serious_service(python_library_config):
    """Test that template is suitable for a serious service with containers."""
    required_components = python_library_config.get("required_components", [])

    # Should include containerization
    assert "podman" in required_components

    # Should include CI/CD
    assert "github_actions" in required_components

    # Should include documentation
    assert "mkdocs" in required_components

    # Should include code quality
    assert "pre_commit" in required_components

    # Should include task automation
    assert "task_automation" in required_components

    # Should include PyPI publishing support
    assert "pypi" in required_components


def test_template_description_accuracy(python_library_config):
    """Test that template description accurately reflects its purpose."""
    description = python_library_config.get("description", "")

    # Should mention key technologies
    assert "GitHub" in description
    assert "uv" in description
    assert "python library" in description.lower()


def test_base_config_github_focus(python_library_config):
    """Test that base config is focused on GitHub."""
    base_config = python_library_config.get("base_cookiecutter_config", {})

    # Should have GitHub username field
    assert "github_username" in base_config

    # GitHub username should be derived from author name
    github_username = base_config.get("github_username", "")
    assert "author_name" in github_username


def test_modern_python_defaults(python_library_config):
    """Test that template uses modern Python defaults."""
    base_config = python_library_config.get("base_cookiecutter_config", {})

    # Should use modern Python version range
    python_min_version = base_config.get("python_min_version", "")
    python_max_version = base_config.get("python_max_version", "")
    assert python_min_version == "3.10"
    assert python_max_version == "3.12"

    # Should use semantic versioning
    version = base_config.get("version", "")
    assert version == "0.1.0"
