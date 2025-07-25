"""Unit tests for ComponentManager."""

from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from repo_scaffold.core.component_manager import Component
from repo_scaffold.core.component_manager import ComponentManager


@pytest.fixture
def mock_components_dir(tmp_path):
    """Create a mock components directory."""
    return tmp_path / "components"


@pytest.fixture
def sample_component_config():
    """Sample component configuration."""
    return {
        "name": "test_component",
        "display_name": "Test Component",
        "description": "A test component",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {"test_var": True},
        "files": [{"src": "test.txt", "dest": "test.txt"}],
        "hooks": {},
    }


def test_component_manager_init(mock_components_dir):
    """Test ComponentManager initialization."""
    manager = ComponentManager(mock_components_dir)
    assert manager.components_dir == mock_components_dir


def test_discover_components_empty_dir(mock_components_dir):
    """Test component discovery with empty directory."""
    mock_components_dir.mkdir(parents=True)
    manager = ComponentManager(mock_components_dir)

    components = manager._discover_components()
    assert components == {}


def test_discover_components_with_components(mock_components_dir):
    """Test component discovery with components."""
    import yaml

    # Create mock component directories with valid component files
    mock_components_dir.mkdir(parents=True)

    # Create comp1
    comp1_dir = mock_components_dir / "comp1"
    comp1_dir.mkdir()
    comp1_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component 1",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp1_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp1_config, f)

    # Create comp2
    comp2_dir = mock_components_dir / "comp2"
    comp2_dir.mkdir()
    comp2_config = {
        "name": "comp2",
        "display_name": "Component 2",
        "description": "Test component 2",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp2_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp2_config, f)

    manager = ComponentManager(mock_components_dir)

    assert len(manager.components) == 2
    assert "comp1" in manager.components
    assert "comp2" in manager.components


def test_load_component_success(mock_components_dir, sample_component_config):
    """Test successful component loading."""
    import yaml

    # Create component directory and file
    mock_components_dir.mkdir(parents=True)
    comp_dir = mock_components_dir / "test_component"
    comp_dir.mkdir()
    comp_file = comp_dir / "component.yaml"

    with open(comp_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_component_config, f)

    manager = ComponentManager(mock_components_dir)
    component = manager.get_component("test_component")

    assert component is not None
    assert component.name == "test_component"
    assert component.display_name == "Test Component"
    assert component.description == "A test component"
    assert component.category == "test"


def test_load_component_missing_file(mock_components_dir):
    """Test component loading with missing component.yaml."""
    mock_components_dir.mkdir(parents=True)
    comp_dir = mock_components_dir / "test_component"
    comp_dir.mkdir()
    # Don't create component.yaml file

    manager = ComponentManager(mock_components_dir)
    component = manager.get_component("test_component")

    # Should return None for missing component
    assert component is None


def test_resolve_dependencies_no_deps(tmp_path):
    """Test dependency resolution with no dependencies."""
    import yaml

    # Create a real component with no dependencies
    comp_dir = tmp_path / "comp1"
    comp_dir.mkdir()
    comp_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp_config, f)

    manager = ComponentManager(tmp_path)
    result = manager.resolve_dependencies(["comp1"])
    assert result == ["comp1"]


def test_resolve_dependencies_with_deps(tmp_path):
    """Test dependency resolution with dependencies."""
    import yaml

    # Create comp1 that depends on comp2
    comp1_dir = tmp_path / "comp1"
    comp1_dir.mkdir()
    comp1_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component",
        "category": "test",
        "dependencies": ["comp2"],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp1_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp1_config, f)

    # Create comp2 with no dependencies
    comp2_dir = tmp_path / "comp2"
    comp2_dir.mkdir()
    comp2_config = {
        "name": "comp2",
        "display_name": "Component 2",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp2_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp2_config, f)

    manager = ComponentManager(tmp_path)
    result = manager.resolve_dependencies(["comp1"])
    assert "comp1" in result
    assert "comp2" in result


def test_resolve_dependencies_circular(tmp_path):
    """Test dependency resolution with circular dependencies."""
    import yaml

    # Create comp1 that depends on comp2
    comp1_dir = tmp_path / "comp1"
    comp1_dir.mkdir()
    comp1_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component",
        "category": "test",
        "dependencies": ["comp2"],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp1_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp1_config, f)

    # Create comp2 that depends on comp1 (circular)
    comp2_dir = tmp_path / "comp2"
    comp2_dir.mkdir()
    comp2_config = {
        "name": "comp2",
        "display_name": "Component 2",
        "description": "Test component",
        "category": "test",
        "dependencies": ["comp1"],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp2_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp2_config, f)

    manager = ComponentManager(tmp_path)
    # The current implementation handles circular dependencies gracefully
    result = manager.resolve_dependencies(["comp1"])
    assert "comp1" in result
    assert "comp2" in result


def test_resolve_dependencies_missing(tmp_path):
    """Test dependency resolution with missing dependency."""
    import yaml

    # Create comp1 that depends on missing component
    comp1_dir = tmp_path / "comp1"
    comp1_dir.mkdir()
    comp1_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component",
        "category": "test",
        "dependencies": ["missing_comp"],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp1_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp1_config, f)

    manager = ComponentManager(tmp_path)
    with pytest.raises(KeyError, match="Component 'missing_comp' not found"):
        manager.resolve_dependencies(["comp1"])


def test_validate_selection_no_conflicts():
    """Test selection validation with no conflicts."""
    manager = ComponentManager(Path("/fake"))

    # Mock components with no conflicts
    comp1 = Mock(spec=Component)
    comp1.conflicts = []
    comp2 = Mock(spec=Component)
    comp2.conflicts = []

    components = {"comp1": comp1, "comp2": comp2}

    with patch.object(manager, "_discover_components", return_value=components):
        conflicts = manager.validate_selection(["comp1", "comp2"])
        assert conflicts == []


def test_validate_selection_with_conflicts(tmp_path):
    """Test selection validation with conflicts."""
    import yaml

    # Create comp1 that conflicts with comp2
    comp1_dir = tmp_path / "comp1"
    comp1_dir.mkdir()
    comp1_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": ["comp2"],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp1_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp1_config, f)

    # Create comp2 that conflicts with comp1
    comp2_dir = tmp_path / "comp2"
    comp2_dir.mkdir()
    comp2_config = {
        "name": "comp2",
        "display_name": "Component 2",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": ["comp1"],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp2_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp2_config, f)

    manager = ComponentManager(tmp_path)
    conflicts = manager.validate_selection(["comp1", "comp2"])
    assert len(conflicts) > 0
    assert any("comp1" in conflict and "comp2" in conflict for conflict in conflicts)


def test_validate_selection_missing_component(tmp_path):
    """Test selection validation with missing component."""
    # Create empty components directory
    manager = ComponentManager(tmp_path)

    # Should not raise an error, just return empty conflicts list
    conflicts = manager.validate_selection(["missing"])
    assert conflicts == []


def test_get_component_info(tmp_path):
    """Test getting component information."""
    import yaml

    # Create a test component
    comp_dir = tmp_path / "test"
    comp_dir.mkdir()
    comp_config = {
        "name": "test",
        "display_name": "Test Component",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp_config, f)

    manager = ComponentManager(tmp_path)
    info = manager.get_component("test")
    assert info is not None
    assert info.name == "test"
    assert info.display_name == "Test Component"


def test_get_component_info_missing(tmp_path):
    """Test getting info for missing component."""
    manager = ComponentManager(tmp_path)

    info = manager.get_component("missing")
    assert info is None


def test_list_components(tmp_path):
    """Test listing all components."""
    import yaml

    # Create comp1
    comp1_dir = tmp_path / "comp1"
    comp1_dir.mkdir()
    comp1_config = {
        "name": "comp1",
        "display_name": "Component 1",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp1_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp1_config, f)

    # Create comp2
    comp2_dir = tmp_path / "comp2"
    comp2_dir.mkdir()
    comp2_config = {
        "name": "comp2",
        "display_name": "Component 2",
        "description": "Test component",
        "category": "test",
        "dependencies": [],
        "conflicts": [],
        "cookiecutter_vars": {},
        "files": [],
        "hooks": {},
    }
    with open(comp2_dir / "component.yaml", "w", encoding="utf-8") as f:
        yaml.dump(comp2_config, f)

    manager = ComponentManager(tmp_path)
    component_list = manager.list_components()
    assert len(component_list) == 2
    assert any(comp.name == "comp1" for comp in component_list)
    assert any(comp.name == "comp2" for comp in component_list)
