"""Tests for Python Core component."""

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
def python_core_component(component_manager):
    """Get the Python Core component."""
    components = component_manager._discover_components()
    return components.get("python_core")


def test_python_core_component_exists(python_core_component):
    """Test that Python Core component exists and has correct metadata."""
    assert python_core_component is not None
    assert python_core_component.name == "python_core"
    assert python_core_component.display_name == "Python Core"
    assert python_core_component.category == "core"


def test_python_core_no_conflicts(python_core_component):
    """Test that Python Core has no conflicts."""
    assert python_core_component.conflicts == []


def test_python_core_cookiecutter_vars(python_core_component):
    """Test that Python Core sets correct cookiecutter variables."""
    expected_vars = {"use_python": True, "use_uv": True}

    for key, expected_value in expected_vars.items():
        assert key in python_core_component.cookiecutter_vars
        assert python_core_component.cookiecutter_vars[key] == expected_value


def test_python_core_files(python_core_component):
    """Test that Python Core component has correct files."""
    expected_files = {
        "pyproject.toml",
        "README.md",
        "{{cookiecutter.project_slug}}/__init__.py",
        "{{cookiecutter.project_slug}}/py.typed",
        "tests/__init__.py",
        "tests/test_{{cookiecutter.package_name}}.py",
        ".gitignore",
        ".cz.yaml",
        ".pre-commit-config.yaml",
        ".ruff.toml",
        ".yamlfmt.yaml",
    }

    actual_files = {file_config["dest"] for file_config in python_core_component.files}
    assert actual_files == expected_files


def test_pyproject_toml_content(components_dir):
    """Test pyproject.toml template content."""
    pyproject_path = components_dir / "python_core" / "files" / "pyproject.toml.j2"
    assert pyproject_path.exists()

    content = pyproject_path.read_text(encoding="utf-8")

    # Check for uv and modern Python tooling
    assert "hatchling" in content
    assert "pytest" in content
    assert "ruff" in content
    assert "commitizen" in content
    assert "pre-commit" in content

    # Check for proper package structure
    assert "{{cookiecutter.project_slug}}" in content
    assert "{{cookiecutter.package_name}}" in content


def test_ruff_config_content(components_dir):
    """Test .ruff.toml template content."""
    ruff_path = components_dir / "python_core" / "files" / ".ruff.toml.j2"
    assert ruff_path.exists()

    content = ruff_path.read_text(encoding="utf-8")

    # Check for proper configuration
    assert "{{cookiecutter.project_slug}}" in content
    assert "py{{cookiecutter.python_min_version.replace" in content
    assert "line-length = 120" in content
    assert 'convention = "google"' in content


def test_pre_commit_config_content(components_dir):
    """Test .pre-commit-config.yaml template content."""
    precommit_path = components_dir / "python_core" / "files" / ".pre-commit-config.yaml.j2"
    assert precommit_path.exists()

    content = precommit_path.read_text(encoding="utf-8")

    # Check for uv integration
    assert "uv-pre-commit" in content
    assert "uv-lock" in content
    assert "yamlfmt" in content


def test_readme_template_content(components_dir):
    """Test README.md template content."""
    readme_path = components_dir / "python_core" / "files" / "README.md.j2"
    assert readme_path.exists()

    content = readme_path.read_text(encoding="utf-8")

    # Check for uv usage instructions
    assert "uv sync" in content
    assert "uv run pytest" in content
    assert "uv run ruff" in content
    assert "uv run cz bump" in content
    assert "{{cookiecutter.project_name}}" in content


def test_gitignore_content(components_dir):
    """Test .gitignore content."""
    gitignore_path = components_dir / "python_core" / "files" / ".gitignore"
    assert gitignore_path.exists()

    content = gitignore_path.read_text(encoding="utf-8")

    # Check for Python-specific ignores
    assert "__pycache__/" in content
    assert ".venv" in content  # Could be .venv or .venv/
    assert "*.egg-info/" in content
    assert ".pytest_cache/" in content
    assert ".python-version" in content


def test_commitizen_config_content(components_dir):
    """Test .cz.yaml template content."""
    cz_path = components_dir / "python_core" / "files" / ".cz.yaml.j2"
    assert cz_path.exists()

    content = cz_path.read_text(encoding="utf-8")

    # Check for uv integration
    assert "version_provider: uv" in content
    assert "cz_conventional_commits" in content
    assert "update_changelog_on_bump: true" in content


def test_yamlfmt_config_content(components_dir):
    """Test .yamlfmt.yaml template content."""
    yamlfmt_path = components_dir / "python_core" / "files" / ".yamlfmt.yaml.j2"
    assert yamlfmt_path.exists()

    content = yamlfmt_path.read_text(encoding="utf-8")

    # Check for YAML formatting configuration
    assert "line_length: 100" in content
    assert "indentation: 2" in content
    assert "preserve_quotes: true" in content


def test_init_file_content(components_dir):
    """Test __init__.py template content."""
    init_path = components_dir / "python_core" / "files" / "src" / "__init__.py.j2"
    assert init_path.exists()

    content = init_path.read_text(encoding="utf-8")

    # Check for basic package structure
    assert "{{cookiecutter.description}}" in content
    assert '__version__ = "{{cookiecutter.version}}"' in content


def test_test_file_content(components_dir):
    """Test test template content."""
    test_path = components_dir / "python_core" / "files" / "tests" / "test_basic.py.j2"
    assert test_path.exists()

    content = test_path.read_text(encoding="utf-8")

    # Check for proper test structure
    assert "import {{cookiecutter.project_slug.replace" in content
    assert "def test_version():" in content
    assert "def test_import():" in content


def test_component_yaml_syntax(components_dir):
    """Test that component.yaml has valid syntax."""
    component_yaml = components_dir / "python_core" / "component.yaml"
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


def test_all_template_files_exist(components_dir):
    """Test that all referenced template files exist."""
    component_yaml = components_dir / "python_core" / "component.yaml"

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files_dir = components_dir / "python_core" / "files"

    for file_config in config["files"]:
        src_file = files_dir / file_config["src"]
        assert src_file.exists(), f"Template file not found: {src_file}"
