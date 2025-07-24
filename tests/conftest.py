"""
Pytest configuration and shared fixtures for repo-scaffold tests.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock

from repo_scaffold.core.component_manager import Component


@pytest.fixture(scope="session")
def sample_component_configs():
    """Sample component configurations for testing."""
    return {
        "python_core": {
            "name": "python_core",
            "display_name": "Python Core",
            "description": "Core Python project structure",
            "category": "core",
            "dependencies": [],
            "conflicts": [],
            "cookiecutter_vars": {
                "use_python": True,
                "python_version": "3.12"
            },
            "files": [
                {"src": "pyproject.toml.j2", "dest": "pyproject.toml"},
                {"src": "src/__init__.py.j2", "dest": "src/{{cookiecutter.package_name}}/__init__.py"}
            ],
            "hooks": {
                "post_gen": ["setup_python_env"]
            }
        },
        "cli_support": {
            "name": "cli_support",
            "display_name": "CLI Support",
            "description": "Command line interface support",
            "category": "feature",
            "dependencies": ["python_core"],
            "conflicts": [],
            "cookiecutter_vars": {
                "use_cli": True,
                "cli_framework": "click"
            },
            "files": [
                {"src": "cli.py.j2", "dest": "src/{{cookiecutter.package_name}}/cli.py"}
            ],
            "hooks": {
                "post_gen": ["setup_cli_entry_point"]
            }
        },
        "docker": {
            "name": "docker",
            "display_name": "Docker Support",
            "description": "Docker containerization support",
            "category": "containerization",
            "dependencies": [],
            "conflicts": ["podman"],
            "cookiecutter_vars": {
                "use_docker": True
            },
            "files": [
                {"src": "Dockerfile.j2", "dest": "Dockerfile"},
                {"src": "docker-compose.yml.j2", "dest": "docker-compose.yml"}
            ],
            "hooks": {}
        },
        "github_actions": {
            "name": "github_actions",
            "display_name": "GitHub Actions",
            "description": "GitHub Actions CI/CD workflows",
            "category": "ci_cd",
            "dependencies": [],
            "conflicts": [],
            "cookiecutter_vars": {
                "use_github_actions": True
            },
            "files": [
                {"src": "test.yml.j2", "dest": ".github/workflows/test.yml"},
                {"src": "release.yml.j2", "dest": ".github/workflows/release.yml"}
            ],
            "hooks": {
                "post_gen": ["validate_workflows"]
            }
        }
    }


@pytest.fixture(scope="session")
def sample_template_configs():
    """Sample template configurations for testing."""
    return {
        "python-library": {
            "name": "python-library",
            "display_name": "Python Library",
            "description": "Create a Python library project",
            "required_components": ["python_core"],
            "optional_components": {
                "cli_support": {
                    "prompt": "Add CLI support?",
                    "help": "Adds Click-based command line interface",
                    "default": False
                },
                "docker": {
                    "prompt": "Add Docker support?",
                    "help": "Includes Dockerfile and docker-compose.yml",
                    "default": False
                },
                "github_actions": {
                    "prompt": "Add GitHub Actions CI/CD?",
                    "help": "Automated testing and release workflows",
                    "default": True
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
                "python_version": "3.12"
            }
        },
        "python-cli": {
            "name": "python-cli",
            "display_name": "Python CLI Application",
            "description": "Create a Python CLI application",
            "required_components": ["python_core", "cli_support"],
            "optional_components": {
                "docker": {
                    "prompt": "Add Docker support?",
                    "help": "Includes Dockerfile",
                    "default": False
                },
                "github_actions": {
                    "prompt": "Add GitHub Actions CI/CD?",
                    "help": "Automated testing and release workflows",
                    "default": True
                }
            },
            "base_cookiecutter_config": {
                "project_name": "My CLI App",
                "package_name": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
                "author_name": "Your Name",
                "author_email": "your.email@example.com",
                "version": "0.1.0",
                "description": "A command line application",
                "license": ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"],
                "python_version": "3.12"
            }
        }
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
    """Helper function to create component files for testing."""
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
