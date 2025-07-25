"""Tests for PyPI component."""

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
def pypi_component(component_manager):
    """Get the PyPI component."""
    components = component_manager._discover_components()
    return components.get("pypi")


def test_pypi_component_exists(pypi_component):
    """Test that PyPI component exists and has correct metadata."""
    assert pypi_component is not None
    assert pypi_component.name == "pypi"
    assert pypi_component.display_name == "PyPI Publishing"
    assert "PyPI publishing support" in pypi_component.description
    assert pypi_component.category == "packaging"


def test_pypi_dependencies(pypi_component):
    """Test that PyPI has correct dependencies."""
    expected_dependencies = {"github_actions", "task_automation"}
    assert set(pypi_component.dependencies) == expected_dependencies


def test_pypi_no_conflicts(pypi_component):
    """Test that PyPI has no conflicts."""
    assert pypi_component.conflicts == []


def test_pypi_cookiecutter_vars(pypi_component):
    """Test that PyPI sets correct cookiecutter variables."""
    expected_vars = {
        "use_pypi": True,
        "use_public_pypi": True,
        "use_private_pypi": False,
        "private_pypi_name": "homelab",
        "private_pypi_url": "https://pypiserver.example.com/simple/",
    }

    for key, expected_value in expected_vars.items():
        assert key in pypi_component.cookiecutter_vars
        assert pypi_component.cookiecutter_vars[key] == expected_value


def test_pypi_files(pypi_component):
    """Test that PyPI component has correct files."""
    expected_files = {".github/workflows/pypi-release.yaml"}

    actual_files = {file_config["dest"] for file_config in pypi_component.files}
    assert actual_files == expected_files


def test_pypi_release_workflow_content(components_dir):
    """Test PyPI release workflow content."""
    workflow_path = components_dir / "pypi" / "files" / "pypi-release.yaml.j2"
    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    # Check for proper triggers
    assert "push:" in content
    assert "tags:" in content
    assert "workflow_dispatch:" in content

    # Check for multiple jobs structure
    assert "build-and-test:" in content
    assert "publish-to-public-pypi:" in content
    assert "publish-to-private-pypi:" in content
    assert "create-github-release:" in content

    # Check for publishing strategy logic
    assert "determine-strategy" in content
    assert "should-publish-public" in content
    assert "should-publish-private" in content

    # Check for public PyPI support
    assert "pypa/gh-action-pypi-publish@release/v1" in content
    assert "use_public_pypi" in content

    # Check for private PyPI support
    assert "use_private_pypi" in content
    assert "UV_PUBLISH_USERNAME" in content
    assert "UV_PUBLISH_PASSWORD" in content

    # Check for GitHub release creation
    assert "softprops/action-gh-release@v2" in content
    assert "generate_release_notes: true" in content

    # Check for build and test steps
    assert "uv build" in content or "task build" in content
    assert "task test:all" in content or "pytest" in content

    # Check for artifact handling
    assert "upload-artifact@v4" in content
    assert "download-artifact@v4" in content
    assert "python-package-distributions" in content


def test_pypi_type_choices(pypi_component):
    """Test that PyPI type has correct choices."""
    pypi_type = pypi_component.cookiecutter_vars.get("pypi_type")
    assert pypi_type == ["public", "private"]


def test_component_yaml_syntax(components_dir):
    """Test that component.yaml has valid syntax."""
    component_yaml = components_dir / "pypi" / "component.yaml"
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
        # Files should be GitHub workflows
        dest = file_config["dest"]
        assert dest.startswith(".github/workflows/")


def test_file_templates_exist(components_dir):
    """Test that all referenced template files exist."""
    component_yaml = components_dir / "pypi" / "component.yaml"

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files_dir = components_dir / "pypi" / "files"

    for file_config in config["files"]:
        src_file = files_dir / file_config["src"]
        assert src_file.exists(), f"Template file not found: {src_file}"


def test_trusted_publishing_support(components_dir):
    """Test that workflow supports PyPI trusted publishing."""
    workflow_path = components_dir / "pypi" / "files" / "pypi-release.yaml.j2"
    content = workflow_path.read_text(encoding="utf-8")

    # Check for trusted publishing permissions
    assert "id-token: write" in content
    assert "print-hash: true" in content

    # Should not require PYPI_TOKEN for public PyPI
    assert "PYPI_TOKEN" not in content


def test_private_pypi_configuration(components_dir):
    """Test private PyPI configuration options."""
    workflow_path = components_dir / "pypi" / "files" / "pypi-release.yaml.j2"
    content = workflow_path.read_text(encoding="utf-8")

    # Check for private PyPI URL handling
    assert "private_pypi_url" in content
    assert "replace('/simple/', '/')" in content

    # Check for authentication
    assert "PYPI_SERVER_USERNAME" in content
    assert "PYPI_SERVER_PASSWORD" in content


def test_conditional_publishing(components_dir):
    """Test that publishing is conditional based on configuration."""
    workflow_path = components_dir / "pypi" / "files" / "pypi-release.yaml.j2"
    content = workflow_path.read_text(encoding="utf-8")

    # Should have conditional blocks
    assert 'use_public_pypi == "true"' in content
    assert 'use_private_pypi == "true"' in content

    # Should support both simultaneously
    public_block = "Publish to Public PyPI"
    private_block = "Publish to Private PyPI"
    assert public_block in content
    assert private_block in content


def test_publishing_strategy_logic(components_dir):
    """Test the publishing strategy determination logic."""
    workflow_path = components_dir / "pypi" / "files" / "pypi-release.yaml.j2"
    content = workflow_path.read_text(encoding="utf-8")

    # Should have strategy determination step
    assert "Determine publishing strategy" in content

    # Should have conditional logic for different scenarios
    # Public PyPI mode: publish to both public and private
    assert "公共 PyPI 模式：同时发布到公共和私有" in content  # noqa: RUF001

    # Private only mode: publish only to private
    assert "仅私有 PyPI 模式：只发布到私有" in content  # noqa: RUF001

    # Should set outputs for job dependencies
    assert "GITHUB_OUTPUT" in content


def test_job_dependencies(components_dir):
    """Test that jobs have correct dependencies."""
    workflow_path = components_dir / "pypi" / "files" / "pypi-release.yaml.j2"
    content = workflow_path.read_text(encoding="utf-8")

    # Public PyPI job should depend on build-and-test
    assert "needs: build-and-test" in content

    # GitHub release should depend on all jobs
    assert "needs: [build-and-test, publish-to-public-pypi, publish-to-private-pypi]" in content

    # Should use conditional execution
    assert "if: needs.build-and-test.outputs.should-publish-public" in content
    assert "if: needs.build-and-test.outputs.should-publish-private" in content

    # GitHub release should run even if publishing jobs are skipped
    assert "if: always() && needs.build-and-test.result" in content
