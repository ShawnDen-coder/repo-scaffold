"""Tests for Podman component."""

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
def podman_component(component_manager):
    """Get the Podman component."""
    components = component_manager._discover_components()
    return components.get("podman")


def test_podman_component_exists(podman_component):
    """Test that Podman component exists and has correct metadata."""
    assert podman_component is not None
    assert podman_component.name == "podman"
    assert podman_component.display_name == "Podman Support"
    assert "containerization" in podman_component.description.lower()
    assert podman_component.category == "containerization"


def test_podman_conflicts(podman_component):
    """Test that Podman has correct conflicts."""
    expected_conflicts = {"docker"}
    assert set(podman_component.conflicts) == expected_conflicts


def test_podman_cookiecutter_vars(podman_component):
    """Test that Podman sets correct cookiecutter variables."""
    expected_vars = {
        "use_podman": True,
        "use_containers": True,
        "container_runtime": "podman",
        "podman_compose_version": "1.0.6",
    }

    for key, expected_value in expected_vars.items():
        assert key in podman_component.cookiecutter_vars
        assert podman_component.cookiecutter_vars[key] == expected_value


def test_podman_files(podman_component):
    """Test that Podman component has correct files."""
    expected_files = {
        "container/Containerfile",
        "container/.containerignore",
        "container/compose.yml",
        ".github/workflows/container-release.yaml",
    }

    actual_files = {file_config["dest"] for file_config in podman_component.files}
    assert actual_files == expected_files


def test_containerfile_content(components_dir):
    """Test Containerfile template content."""
    containerfile_path = components_dir / "podman" / "files" / "Containerfile.j2"
    assert containerfile_path.exists()

    content = containerfile_path.read_text(encoding="utf-8")

    # Check for uv best practices
    assert "ghcr.io/astral-sh/uv:latest" in content
    assert "uv sync --frozen --no-cache" in content
    assert 'ENV PATH="/app/.venv/bin:$PATH"' in content

    # Check for proper file copying
    assert "COPY ../uv.lock ../pyproject.toml ./" in content
    assert "COPY ../{{cookiecutter.project_slug}}" in content


def test_compose_yml_content(components_dir):
    """Test compose.yml template content."""
    compose_path = components_dir / "podman" / "files" / "compose.yml.j2"
    assert compose_path.exists()

    content = compose_path.read_text(encoding="utf-8")

    # Check for Podman-specific features
    assert "userns_mode: keep-id" in content
    assert "PODMAN_USERNS=keep-id" in content
    assert ":Z,U" in content  # SELinux labels
    assert "no-new-privileges:true" in content

    # Check build context
    assert "context: .." in content
    assert "dockerfile: container/Containerfile" in content


def test_containerignore_content(components_dir):
    """Test .containerignore content."""
    ignore_path = components_dir / "podman" / "files" / ".containerignore"
    assert ignore_path.exists()

    content = ignore_path.read_text(encoding="utf-8")

    # Check for common ignore patterns
    assert "__pycache__/" in content
    assert ".venv/" in content
    assert ".git/" in content
    assert "compose.yml" in content


def test_component_yaml_syntax(components_dir):
    """Test that component.yaml has valid syntax."""
    component_yaml = components_dir / "podman" / "component.yaml"
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
        # Files should be either in container/ or .github/workflows/
        dest = file_config["dest"]
        assert dest.startswith("container/") or dest.startswith(".github/workflows/")


def test_container_release_workflow_content(components_dir):
    """Test container release workflow content."""
    workflow_path = components_dir / "podman" / "files" / "container-release.yaml.j2"
    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    # Check for proper triggers
    assert "release:" in content
    assert "workflow_dispatch:" in content
    assert "push:" in content
    assert "container/**" in content

    # Check for Podman/Buildah usage
    assert "redhat-actions/podman-login@v1" in content
    assert "redhat-actions/buildah-build@v2" in content
    assert "redhat-actions/push-to-registry@v2" in content

    # Check for correct container file path
    assert "./container/Containerfile" in content


def test_file_templates_exist(components_dir):
    """Test that all referenced template files exist."""
    component_yaml = components_dir / "podman" / "component.yaml"

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files_dir = components_dir / "podman" / "files"

    for file_config in config["files"]:
        src_file = files_dir / file_config["src"]
        assert src_file.exists(), f"Template file not found: {src_file}"
