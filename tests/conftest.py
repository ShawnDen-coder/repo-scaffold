"""
Pytest configuration and shared fixtures for repo-scaffold tests.

This module provides shared fixtures and configuration for all tests.
The fixtures load test data from YAML files in tests/fixtures/ directory.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock

from repo_scaffold.core.component_manager import Component


# Path to test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_yaml(fixture_path: str) -> dict:
    """
    Load a YAML fixture file.

    Args:
        fixture_path: Path relative to fixtures directory (e.g., "components/python_core.yaml")

    Returns:
        Parsed YAML content as dictionary
    """
    full_path = FIXTURES_DIR / fixture_path
    with open(full_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def sample_component_configs():
    """
    Sample component configurations for testing.

    Loads component configurations from YAML files in tests/fixtures/components/
    Each YAML file contains comments indicating which tests use that component.
    """
    return {
        "python_core": load_fixture_yaml("components/python_core.yaml"),
        "cli_support": load_fixture_yaml("components/cli_support.yaml"),
        "docker": load_fixture_yaml("components/docker.yaml"),
        "podman": load_fixture_yaml("components/podman.yaml"),
        "github_actions": load_fixture_yaml("components/github_actions.yaml"),
    }


@pytest.fixture(scope="session")
def sample_template_configs():
    """
    Sample template configurations for testing.

    Loads template configurations from YAML files in tests/fixtures/templates/
    Each YAML file contains comments indicating which tests use that template.
    """
    return {
        "python-library": load_fixture_yaml("templates/python-library.yaml"),
        "python-cli": load_fixture_yaml("templates/python-cli.yaml"),
    }


@pytest.fixture
def mock_component():
    """Create a mock Component for testing."""
    component = Mock(spec=Component)
    component.name = "test_component"
    component.display_name = "Test Component"
    component.description = "A test component"
    component.category = "test"
    component.dependencies = []
    component.conflicts = []
    component.cookiecutter_vars = {"test_var": True}
    component.files = [{"src": "test.j2", "dest": "test.txt"}]
    component.hooks = {"post_gen": ["test_hook"]}
    return component


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        
        # Create standard directories
        (workspace / "components").mkdir()
        (workspace / "templates").mkdir()
        (workspace / "output").mkdir()
        
        yield workspace


def create_component_files(component_dir: Path, config: dict, files_content: dict = None):
    """
    Helper function to create component files for testing.

    Used by:
    - test_integration.py::integration_test_setup fixture
    - Any test that needs real component files on disk
    """
    component_dir.mkdir(exist_ok=True)

    # Create component.yaml
    with open(component_dir / "component.yaml", "w") as f:
        yaml.dump(config, f)

    # Create files directory
    files_dir = component_dir / "files"
    files_dir.mkdir(exist_ok=True)

    # Create component files if content provided
    if files_content:
        for filename, content in files_content.items():
            with open(files_dir / filename, "w") as f:
                f.write(content)

    # Create hooks directory
    hooks_dir = component_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)


def create_component_from_fixture(component_dir: Path, component_name: str):
    """
    Create a component directory structure from a fixture YAML file.

    Args:
        component_dir: Directory where component should be created
        component_name: Name of component (matches YAML filename)

    Used by:
    - Integration tests that need real component files
    - Tests that verify file merging functionality
    """
    config = load_fixture_yaml(f"components/{component_name}.yaml")

    # Create component directory
    comp_dir = component_dir / component_name
    comp_dir.mkdir(parents=True, exist_ok=True)

    # Create component.yaml
    with open(comp_dir / "component.yaml", "w") as f:
        yaml.dump(config, f)

    # Create files directory
    files_dir = comp_dir / "files"
    files_dir.mkdir(exist_ok=True)

    # Copy template files from fixtures
    for file_info in config.get("files", []):
        src_filename = file_info["src"]
        try:
            # Try to load the template file from fixtures
            template_content = (FIXTURES_DIR / "component_files" / src_filename).read_text()
            with open(files_dir / src_filename, "w") as f:
                f.write(template_content)
        except FileNotFoundError:
            # Create a placeholder file if template doesn't exist
            with open(files_dir / src_filename, "w") as f:
                f.write(f"# Template file for {src_filename}\n# Component: {component_name}\n")

    # Create hooks directory
    hooks_dir = comp_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)


def create_template_file(template_path: Path, config: dict):
    """Helper function to create template configuration files."""
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(template_path, "w") as f:
        yaml.dump(config, f)


# Pytest markers for different test categories
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "cli: mark test as a CLI test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Custom pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "test_cli" in item.nodeid:
            item.add_marker(pytest.mark.cli)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "slow" in item.name.lower() or "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
