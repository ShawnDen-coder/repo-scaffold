"""
Unit tests for TemplateComposer class.

Tests the template composition, file merging, and Cookiecutter configuration generation.
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from repo_scaffold.core.template_composer import TemplateComposer
from repo_scaffold.core.component_manager import ComponentManager, Component


@pytest.fixture
def mock_component_manager():
    """Create a mock ComponentManager for testing."""
    manager = Mock(spec=ComponentManager)
    
    # Create mock components
    python_core = Mock(spec=Component)
    python_core.name = "python_core"
    python_core.cookiecutter_vars = {"use_python": True, "python_version": "3.12"}
    python_core.files = [
        {"src": "pyproject.toml.j2", "dest": "pyproject.toml"},
        {"src": "src/__init__.py.j2", "dest": "src/{{cookiecutter.package_name}}/__init__.py"}
    ]
    python_core.hooks = {"post_gen": ["setup_python_env"]}
    
    cli_support = Mock(spec=Component)
    cli_support.name = "cli_support"
    cli_support.cookiecutter_vars = {"use_cli": True, "cli_framework": "click"}
    cli_support.files = [
        {"src": "cli.py.j2", "dest": "src/{{cookiecutter.package_name}}/cli.py"}
    ]
    cli_support.hooks = {"post_gen": ["setup_cli_entry_point"]}
    
    docker = Mock(spec=Component)
    docker.name = "docker"
    docker.cookiecutter_vars = {"use_docker": True}
    docker.files = [
        {"src": "Dockerfile.j2", "dest": "Dockerfile"},
        {"src": "docker-compose.yml.j2", "dest": "docker-compose.yml"}
    ]
    docker.hooks = {}
    
    manager.components = {
        "python_core": python_core,
        "cli_support": cli_support,
        "docker": docker
    }

    # Set up get_component method to return the correct component
    def get_component(name):
        return manager.components.get(name)

    manager.get_component = get_component
    manager.components_dir = Path("/mock/components")

    return manager


@pytest.fixture
def template_composer(mock_component_manager):
    """Create a TemplateComposer instance with mock ComponentManager."""
    return TemplateComposer(mock_component_manager)


@pytest.fixture
def sample_template_config():
    """Sample template configuration for testing."""
    return {
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
    }


def test_template_composer_initialization(mock_component_manager):
    """Test TemplateComposer initialization."""
    composer = TemplateComposer(mock_component_manager)
    assert composer.component_manager == mock_component_manager


@patch('tempfile.mkdtemp')
def test_compose_template_basic(mock_mkdtemp, template_composer, sample_template_config, mock_component_manager):
    """Test basic template composition."""
    # Setup mock temporary directory
    temp_dir = Path("/tmp/test_template")
    mock_mkdtemp.return_value = str(temp_dir)
    
    # Mock dependency resolution
    mock_component_manager.resolve_dependencies.return_value = ["python_core", "cli_support"]
    
    with patch('pathlib.Path.mkdir'), \
         patch('builtins.open', create=True) as mock_open, \
         patch('json.dump') as mock_json_dump, \
         patch.object(template_composer, '_merge_component_files') as mock_merge, \
         patch.object(template_composer, '_create_hooks') as mock_hooks:
        
        result = template_composer.compose_template(sample_template_config, ["cli_support"])
        
        # Verify dependency resolution was called with required + selected components
        # sample_template_config has required_components: ["python_core"]
        # Order is required + selected (excluding duplicates)
        mock_component_manager.resolve_dependencies.assert_called_once_with(["python_core", "cli_support"])
        
        # Verify temporary directory creation
        assert result == temp_dir
        
        # Verify cookiecutter.json was created
        mock_json_dump.assert_called_once()
        
        # Verify file merging and hooks creation were called
        mock_merge.assert_called_once_with(["python_core", "cli_support"], temp_dir / "{{cookiecutter.package_name}}")
        mock_hooks.assert_called_once_with(["python_core", "cli_support"], temp_dir)


def test_build_cookiecutter_config(template_composer, sample_template_config, mock_component_manager):
    """Test cookiecutter configuration building."""
    components = ["python_core", "cli_support"]
    
    config = template_composer._build_cookiecutter_config(sample_template_config, components)
    
    # Check base configuration is preserved
    assert config["project_name"] == "My Python Library"
    assert config["author_name"] == "Your Name"
    
    # Check component variables are merged
    assert config["use_python"] is True
    assert config["python_version"] == "3.12"
    assert config["use_cli"] is True
    assert config["cli_framework"] == "click"


def test_build_cookiecutter_config_variable_override(template_composer, sample_template_config, mock_component_manager):
    """Test that component variables can override base configuration."""
    # Modify mock component to override a base variable
    mock_component_manager.components["python_core"].cookiecutter_vars = {
        "use_python": True,
        "python_version": "3.11"  # Override the base config
    }
    
    components = ["python_core"]
    config = template_composer._build_cookiecutter_config(sample_template_config, components)
    
    # Component variable should override base config
    assert config["python_version"] == "3.11"


@patch('shutil.copy2')
@patch('pathlib.Path.mkdir')
@patch('pathlib.Path.exists')
def test_merge_component_files(mock_exists, mock_mkdir, mock_copy, template_composer, mock_component_manager):
    """Test component file merging."""
    components = ["python_core", "cli_support"]
    target_dir = Path("/tmp/target")

    # Mock file existence
    mock_exists.return_value = True

    template_composer._merge_component_files(components, target_dir)

    # Verify directories were created
    assert mock_mkdir.call_count >= 1

    # Verify files were copied
    assert mock_copy.call_count == 3  # 2 from python_core + 1 from cli_support


@patch('builtins.open', create=True)
def test_create_hooks(mock_open, template_composer, mock_component_manager):
    """Test hooks creation."""
    components = ["python_core", "cli_support"]
    temp_dir = Path("/tmp/template")
    
    template_composer._create_hooks(components, temp_dir)
    
    # Check that files were opened for writing
    assert mock_open.call_count >= 1


def test_create_hooks_empty_components(template_composer):
    """Test hooks creation with no components."""
    with patch('builtins.open', create=True) as mock_open:
        template_composer._create_hooks([], Path("/tmp/template"))
        
        # Should still create basic hooks structure
        assert mock_open.call_count >= 1


def test_compose_template_with_empty_components(template_composer, sample_template_config, mock_component_manager):
    """Test template composition with empty component list."""
    mock_component_manager.resolve_dependencies.return_value = []
    
    with patch('tempfile.mkdtemp') as mock_mkdtemp, \
         patch('pathlib.Path.mkdir'), \
         patch('builtins.open', create=True), \
         patch('json.dump'):
        
        mock_mkdtemp.return_value = "/tmp/test"
        
        result = template_composer.compose_template(sample_template_config, [])
        
        assert result == Path("/tmp/test")
        # Even with empty selected components, required_components are still included
        mock_component_manager.resolve_dependencies.assert_called_once_with(["python_core"])


@patch('tempfile.mkdtemp')
def test_compose_template_file_operations_error(mock_mkdtemp, template_composer, sample_template_config, mock_component_manager):
    """Test template composition when file operations fail."""
    mock_mkdtemp.return_value = "/tmp/test"
    mock_component_manager.resolve_dependencies.return_value = ["python_core"]
    
    with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
        with pytest.raises(OSError):
            template_composer.compose_template(sample_template_config, ["python_core"])


def test_merge_component_files_missing_source(template_composer, mock_component_manager):
    """Test file merging when source files are missing."""
    components = ["python_core"]
    target_dir = Path("/tmp/target")
    
    with patch('shutil.copy2', side_effect=FileNotFoundError("Source file not found")), \
         patch('pathlib.Path.mkdir'):
        
        with pytest.raises(FileNotFoundError):
            template_composer._merge_component_files(components, target_dir)


def test_build_cookiecutter_config_no_components(template_composer, sample_template_config):
    """Test cookiecutter config building with no components."""
    config = template_composer._build_cookiecutter_config(sample_template_config, [])
    
    # Should only contain base configuration
    assert config["project_name"] == "My Python Library"
    assert "use_python" not in config
    assert "use_cli" not in config
