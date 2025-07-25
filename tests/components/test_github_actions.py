"""Tests for GitHub Actions component."""

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
def github_actions_component(component_manager):
    """Get the GitHub Actions component."""
    components = component_manager._discover_components()
    return components.get("github_actions")


def test_github_actions_component_exists(github_actions_component):
    """Test that GitHub Actions component exists and has correct metadata."""
    assert github_actions_component is not None
    assert github_actions_component.name == "github_actions"
    assert github_actions_component.display_name == "GitHub Actions"
    assert github_actions_component.category == "ci_cd"


def test_github_actions_dependencies(github_actions_component):
    """Test that GitHub Actions has correct dependencies."""
    expected_dependencies = {"task_automation"}
    assert set(github_actions_component.dependencies) == expected_dependencies


def test_github_actions_no_conflicts(github_actions_component):
    """Test that GitHub Actions has no conflicts."""
    assert github_actions_component.conflicts == []


def test_github_actions_cookiecutter_vars(github_actions_component):
    """Test that GitHub Actions sets correct cookiecutter variables."""
    expected_vars = {"use_github_actions": True}

    for key, expected_value in expected_vars.items():
        assert key in github_actions_component.cookiecutter_vars
        assert github_actions_component.cookiecutter_vars[key] == expected_value


def test_github_actions_files(github_actions_component):
    """Test that GitHub Actions component has correct files."""
    expected_files = {
        ".github/workflows/ci-tests.yaml",
        ".github/workflows/version-bump.yaml",
    }

    actual_files = {file_config["dest"] for file_config in github_actions_component.files}
    assert actual_files == expected_files


def test_ci_tests_workflow_content(components_dir):
    """Test CI tests workflow content."""
    workflow_path = components_dir / "github_actions" / "files" / ".github" / "workflows" / "ci-tests.yaml.j2"
    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    # Check for uv usage
    assert "astral-sh/setup-uv@v5" in content
    assert "uv sync" in content or "task init" in content
    assert "uv run pytest" in content or "task test:all" in content
    assert "uv run ruff" in content or "task lint" in content

    # Check for conditional container build test
    assert "use_podman" in content
    assert "container-build-test:" in content
    assert "./container/Containerfile" in content
    assert "redhat-actions/buildah-build@v2" in content

    # Should not contain the old airflow_docker variable
    assert "use_airflow_docker" not in content
    assert "./docker/Dockerfile" not in content


def test_version_bump_workflow_content(components_dir):
    """Test version bump workflow content."""
    workflow_path = components_dir / "github_actions" / "files" / ".github" / "workflows" / "version-bump.yaml.j2"
    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    # Check for commitizen usage
    assert "commitizen-tools/commitizen-action@master" in content
    assert "workflow_dispatch" in content


def test_workflow_yaml_syntax(components_dir):
    """Test that all workflow files have valid YAML syntax."""
    workflows_dir = components_dir / "github_actions" / "files" / ".github" / "workflows"

    for workflow_file in workflows_dir.glob("*.yaml.j2"):
        content = workflow_file.read_text(encoding="utf-8")

        # Basic YAML structure checks
        assert "name:" in content
        assert "on:" in content
        assert "jobs:" in content


def test_component_yaml_syntax(components_dir):
    """Test that component.yaml has valid syntax."""
    component_yaml = components_dir / "github_actions" / "component.yaml"
    assert component_yaml.exists()

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required_fields = ["name", "display_name", "description", "category", "files"]
    for field in required_fields:
        assert field in config

    # Validate files structure
    for file_config in config["files"]:
        assert "src" in file_config
        assert "dest" in file_config
        assert file_config["dest"].startswith(".github/workflows/")


def test_all_workflow_files_exist(components_dir):
    """Test that all referenced workflow files exist."""
    component_yaml = components_dir / "github_actions" / "component.yaml"

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files_dir = components_dir / "github_actions" / "files"

    for file_config in config["files"]:
        src_file = files_dir / file_config["src"]
        assert src_file.exists(), f"Workflow file not found: {src_file}"
