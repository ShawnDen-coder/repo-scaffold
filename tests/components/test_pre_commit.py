"""Tests for Pre-commit component."""

from pathlib import Path

import pytest
import yaml

from repo_scaffold.core.component_manager import ComponentManager


@pytest.fixture
def components_dir():
    """Get the components directory."""
    return Path(__file__).parent.parent.parent / "repo_scaffold" / "components"


@pytest.fixture
def component_manager(components_dir):
    """Create a component manager instance."""
    return ComponentManager(components_dir)


@pytest.fixture
def pre_commit_component(component_manager):
    """Get the Pre-commit component."""
    components = component_manager._discover_components()
    return components.get("pre_commit")


def test_pre_commit_component_exists(pre_commit_component):
    """Test that Pre-commit component exists and has correct metadata."""
    assert pre_commit_component is not None
    assert pre_commit_component.name == "pre_commit"
    assert pre_commit_component.display_name == "Pre-commit Hooks"
    assert "Pre-commit hooks" in pre_commit_component.description
    assert pre_commit_component.category == "quality"


def test_pre_commit_dependencies(pre_commit_component):
    """Test that Pre-commit has correct dependencies."""
    expected_dependencies = {"task_automation", "github_actions"}
    assert set(pre_commit_component.dependencies) == expected_dependencies


def test_pre_commit_no_conflicts(pre_commit_component):
    """Test that Pre-commit has no conflicts."""
    assert pre_commit_component.conflicts == []


def test_pre_commit_cookiecutter_vars(pre_commit_component):
    """Test that Pre-commit sets correct cookiecutter variables."""
    expected_vars = {"use_pre_commit": True}

    for key, expected_value in expected_vars.items():
        assert key in pre_commit_component.cookiecutter_vars
        assert pre_commit_component.cookiecutter_vars[key] == expected_value


def test_pre_commit_files(pre_commit_component):
    """Test that Pre-commit component has correct files."""
    expected_files = {".pre-commit-config.yaml"}

    actual_files = {file_config["dest"] for file_config in pre_commit_component.files}
    assert actual_files == expected_files


def test_pre_commit_config_content(components_dir):
    """Test pre-commit config content."""
    config_path = components_dir / "pre_commit" / "files" / ".pre-commit-config.yaml.j2"
    assert config_path.exists()

    content = config_path.read_text(encoding="utf-8")

    # Check for conditional uv usage
    assert "use_uv" in content
    assert "uv-pre-commit" in content
    assert "uv-lock" in content

    # Check for conditional GitHub Actions integration
    assert "use_github_actions" in content
    assert "check-github-workflows" in content
    assert "actionlint" in content

    # Check for YAML formatting
    assert "yamlfmt" in content


def test_component_yaml_syntax(components_dir):
    """Test that component.yaml has valid syntax."""
    component_yaml = components_dir / "pre_commit" / "component.yaml"
    assert component_yaml.exists()

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required_fields = ["name", "display_name", "description", "category", "dependencies", "files"]
    for field in required_fields:
        assert field in config

    # Validate dependencies
    assert "task_automation" in config["dependencies"]
    assert "github_actions" in config["dependencies"]

    # Validate files structure
    for file_config in config["files"]:
        assert "src" in file_config
        assert "dest" in file_config


def test_file_templates_exist(components_dir):
    """Test that all referenced template files exist."""
    component_yaml = components_dir / "pre_commit" / "component.yaml"

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files_dir = components_dir / "pre_commit" / "files"

    for file_config in config["files"]:
        src_file = files_dir / file_config["src"]
        assert src_file.exists(), f"Template file not found: {src_file}"


def test_uv_integration(components_dir):
    """Test that pre-commit config integrates with uv."""
    config_path = components_dir / "pre_commit" / "files" / ".pre-commit-config.yaml.j2"
    content = config_path.read_text(encoding="utf-8")

    # Should include uv-specific hooks
    assert "uv-pre-commit" in content
    assert "uv-lock" in content


def test_conditional_uv_usage(components_dir):
    """Test conditional uv usage in pre-commit hooks."""
    config_path = components_dir / "pre_commit" / "files" / ".pre-commit-config.yaml.j2"
    content = config_path.read_text(encoding="utf-8")

    # Should have conditional blocks for uv
    assert "if cookiecutter.use_uv" in content
    assert "uv-lock" in content

    # Should have conditional ending
    assert "endif" in content


def test_github_actions_integration(components_dir):
    """Test GitHub Actions integration in pre-commit config."""
    config_path = components_dir / "pre_commit" / "files" / ".pre-commit-config.yaml.j2"
    content = config_path.read_text(encoding="utf-8")

    # Should have conditional GitHub Actions specific hooks
    assert "if cookiecutter.use_github_actions" in content
    assert "check-github-workflows" in content
    assert "actionlint" in content


def test_yamlfmt_integration(components_dir):
    """Test YAML formatting integration."""
    config_path = components_dir / "pre_commit" / "files" / ".pre-commit-config.yaml.j2"
    content = config_path.read_text(encoding="utf-8")

    # Should include yamlfmt for YAML formatting
    assert "yamlfmt" in content
    assert "google/yamlfmt" in content


def test_actionlint_integration(components_dir):
    """Test GitHub Actions linting integration."""
    config_path = components_dir / "pre_commit" / "files" / ".pre-commit-config.yaml.j2"
    content = config_path.read_text(encoding="utf-8")

    # Should include actionlint for GitHub Actions validation
    assert "actionlint" in content
    assert "rhysd/actionlint" in content
