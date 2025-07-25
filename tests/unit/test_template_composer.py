"""Unit tests for TemplateComposer."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from repo_scaffold.core.component_manager import Component
from repo_scaffold.core.component_manager import ComponentManager
from repo_scaffold.core.template_composer import TemplateComposer


@pytest.fixture
def mock_component_manager():
    """Create a mock component manager."""
    return Mock(spec=ComponentManager)


@pytest.fixture
def template_composer(mock_component_manager):
    """Create a template composer instance."""
    return TemplateComposer(mock_component_manager)


@pytest.fixture
def sample_template_config():
    """Sample template configuration."""
    return {
        "name": "test-template",
        "display_name": "Test Template",
        "description": "A test template",
        "required_components": ["comp1", "comp2"],
        "optional_components": [],
        "base_cookiecutter_config": {"project_name": "Test Project", "version": "1.0.0"},
    }


@pytest.fixture
def sample_components():
    """Sample components for testing."""
    comp1 = Mock(spec=Component)
    comp1.name = "comp1"
    comp1.cookiecutter_vars = {"var1": "value1"}
    comp1.files = [{"src": "file1.txt", "dest": "output1.txt"}]
    # Ensure hasattr works correctly
    comp1.__class__.cookiecutter_vars = {"var1": "value1"}

    comp2 = Mock(spec=Component)
    comp2.name = "comp2"
    comp2.cookiecutter_vars = {"var2": "value2"}
    comp2.files = [{"src": "file2.txt", "dest": "output2.txt"}]
    # Ensure hasattr works correctly
    comp2.__class__.cookiecutter_vars = {"var2": "value2"}

    return {"comp1": comp1, "comp2": comp2}


def test_template_composer_init(mock_component_manager):
    """Test TemplateComposer initialization."""
    composer = TemplateComposer(mock_component_manager)
    assert composer.component_manager == mock_component_manager


def test_build_cookiecutter_config(template_composer, sample_template_config, sample_components):
    """Test building cookiecutter configuration."""
    # Mock the get_component method to return our components
    template_composer.component_manager.get_component = Mock(side_effect=lambda name: sample_components.get(name))

    config = template_composer._build_cookiecutter_config(sample_template_config, ["comp1", "comp2"])

    # Should include base config
    assert config["project_name"] == "Test Project"
    assert config["version"] == "1.0.0"

    # Should include component variables
    assert config["var1"] == "value1"
    assert config["var2"] == "value2"


def test_build_cookiecutter_config_variable_override(template_composer, sample_template_config, sample_components):
    """Test that base config overrides component variables."""
    # Add conflicting variable to component
    sample_components["comp1"].cookiecutter_vars = {"project_name": "Component Project"}

    template_composer.component_manager.components = sample_components

    config = template_composer._build_cookiecutter_config(sample_template_config, ["comp1"])

    # Base config should win
    assert config["project_name"] == "Test Project"


def test_create_template_structure(template_composer):
    """Test creating template directory structure."""
    # The actual method creates a temp directory internally
    # Let's test the compose_template method instead which uses this
    sample_config = {"name": "test-template", "base_cookiecutter_config": {"project_name": "Test"}}

    # Mock the component manager
    template_composer.component_manager.components = {}
    template_composer.component_manager.resolve_dependencies = Mock(return_value=[])

    # This will create the template structure internally
    result = template_composer.compose_template(sample_config, [])

    assert result.exists()
    assert result.is_dir()


def test_write_cookiecutter_json(template_composer):
    """Test writing cookiecutter.json file."""
    config = {"project_name": "Test", "version": "1.0.0"}

    # Test through compose_template which writes the json internally
    sample_config = {"name": "test-template", "base_cookiecutter_config": config}

    # Mock the component manager
    template_composer.component_manager.components = {}
    template_composer.component_manager.resolve_dependencies = Mock(return_value=[])

    result = template_composer.compose_template(sample_config, [])

    json_file = result / "cookiecutter.json"
    assert json_file.exists()

    with open(json_file, encoding="utf-8") as f:
        written_config = json.load(f)

    assert written_config["project_name"] == "Test"
    assert written_config["version"] == "1.0.0"


def test_merge_component_files(template_composer, tmp_path):
    """Test merging component files."""
    # Create mock components that behave like real ones
    comp1 = Mock(spec=Component)
    comp1.name = "comp1"
    comp1.files = [{"src": "file1.txt", "dest": "output1.txt"}]

    comp2 = Mock(spec=Component)
    comp2.name = "comp2"
    comp2.files = [{"src": "file2.txt", "dest": "output2.txt"}]

    # Create real component files
    comp1_files_dir = tmp_path / "comp1" / "files"
    comp1_files_dir.mkdir(parents=True)
    (comp1_files_dir / "file1.txt").write_text("content1")

    comp2_files_dir = tmp_path / "comp2" / "files"
    comp2_files_dir.mkdir(parents=True)
    (comp2_files_dir / "file2.txt").write_text("content2")

    # Mock the component manager to return our components
    template_composer.component_manager.get_component = Mock(
        side_effect=lambda name: {"comp1": comp1, "comp2": comp2}.get(name)
    )
    template_composer.component_manager.components_dir = tmp_path

    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir)

        # The method expects files to be real dicts, not Mock objects
        # Let's override the files attribute to be real dicts
        comp1.files = [{"src": "file1.txt", "dest": "output1.txt"}]
        comp2.files = [{"src": "file2.txt", "dest": "output2.txt"}]

        template_composer._merge_component_files(["comp1", "comp2"], target_dir)

        # Check that files were copied
        assert (target_dir / "output1.txt").exists()
        assert (target_dir / "output2.txt").exists()


def test_merge_component_files_creates_directories(template_composer, tmp_path):
    """Test that merging files creates necessary directories."""
    # Create component with nested file structure
    comp_dir = tmp_path / "comp1" / "files"
    comp_dir.mkdir(parents=True)
    (comp_dir / "file.txt").write_text("test content")

    # Create component mock
    comp1 = Mock(spec=Component)
    comp1.name = "comp1"
    comp1.files = [{"src": "file.txt", "dest": "nested/dir/file.txt"}]

    # Mock the component manager to return our component
    template_composer.component_manager.get_component = Mock(return_value=comp1)
    template_composer.component_manager.components_dir = tmp_path

    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir)

        template_composer._merge_component_files(["comp1"], target_dir)

        # Should create nested directory
        expected_file = target_dir / "nested" / "dir" / "file.txt"
        assert expected_file.exists()


def test_compose_template_full_flow(template_composer, sample_template_config, sample_components, tmp_path):
    """Test complete template composition flow."""
    # Create mock component files
    for comp_name in ["comp1", "comp2"]:
        comp_dir = tmp_path / comp_name / "files"
        comp_dir.mkdir(parents=True)
        (comp_dir / f"{comp_name}_file.txt").write_text(f"{comp_name} content")

    # Update component files to match created files
    sample_components["comp1"].files = [{"src": "comp1_file.txt", "dest": "comp1_output.txt"}]
    sample_components["comp2"].files = [{"src": "comp2_file.txt", "dest": "comp2_output.txt"}]

    # Mock all the necessary methods
    template_composer.component_manager.get_component = Mock(side_effect=lambda name: sample_components.get(name))
    template_composer.component_manager.components_dir = tmp_path
    template_composer.component_manager.resolve_dependencies = Mock(return_value=["comp1", "comp2"])

    result = template_composer.compose_template(sample_template_config, ["comp1", "comp2"])

    # Should return path to template
    assert result.exists()
    assert result.is_dir()

    # Should have cookiecutter.json
    json_file = result / "cookiecutter.json"
    assert json_file.exists()

    # Should have project template directory
    project_dir = result / "{{cookiecutter.package_name}}"
    assert project_dir.exists()

    # Should have component files
    assert (project_dir / "comp1_output.txt").exists()
    assert (project_dir / "comp2_output.txt").exists()


def test_compose_template_missing_component(template_composer, sample_template_config, tmp_path):
    """Test template composition with missing component."""
    template_composer.component_manager.components = {}
    template_composer.component_manager.components_dir = tmp_path
    # Mock resolve_dependencies to return empty list for missing components
    template_composer.component_manager.resolve_dependencies = Mock(return_value=[])

    # Should not raise an error, just skip missing components
    result = template_composer.compose_template(sample_template_config, ["comp1"])
    assert result.exists()


def test_compose_template_missing_source_file(template_composer, sample_template_config, sample_components, tmp_path):
    """Test template composition with missing source file."""
    template_composer.component_manager.components = sample_components
    template_composer.component_manager.components_dir = tmp_path
    # Mock resolve_dependencies to return the component list
    template_composer.component_manager.resolve_dependencies = Mock(return_value=["comp1"])

    # Don't create the source files, should handle gracefully
    result = template_composer.compose_template(sample_template_config, ["comp1"])
    assert result.exists()


def test_cookiecutter_config_serialization(template_composer):
    """Test that cookiecutter config is properly serializable."""
    config = {
        "string_var": "test",
        "int_var": 42,
        "bool_var": True,
        "list_var": ["a", "b", "c"],
        "dict_var": {"key": "value"},
    }

    # Test through compose_template which handles serialization
    sample_config = {"name": "test-template", "base_cookiecutter_config": config}

    # Mock the component manager
    template_composer.component_manager.components = {}
    template_composer.component_manager.resolve_dependencies = Mock(return_value=[])

    result = template_composer.compose_template(sample_config, [])

    json_file = result / "cookiecutter.json"
    with open(json_file, encoding="utf-8") as f:
        loaded_config = json.load(f)

    # Check that all our config values are present
    for key, value in config.items():
        assert loaded_config[key] == value
