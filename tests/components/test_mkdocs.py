"""Tests for MkDocs component."""

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
def mkdocs_component(component_manager):
    """Get the MkDocs component."""
    components = component_manager._discover_components()
    return components.get("mkdocs")


def test_mkdocs_component_exists(mkdocs_component):
    """Test that MkDocs component exists and has correct metadata."""
    assert mkdocs_component is not None
    assert mkdocs_component.name == "mkdocs"
    assert mkdocs_component.display_name == "MkDocs Documentation"
    assert "documentation" in mkdocs_component.description.lower()
    assert mkdocs_component.category == "documentation"


def test_mkdocs_no_conflicts(mkdocs_component):
    """Test that MkDocs has no conflicts."""
    assert mkdocs_component.conflicts == []


def test_mkdocs_cookiecutter_vars(mkdocs_component):
    """Test that MkDocs sets correct cookiecutter variables."""
    expected_vars = {"use_mkdocs": True}

    for key, expected_value in expected_vars.items():
        assert key in mkdocs_component.cookiecutter_vars
        assert mkdocs_component.cookiecutter_vars[key] == expected_value


def test_mkdocs_files(mkdocs_component):
    """Test that MkDocs component has correct files."""
    expected_files = {
        "mkdocs.yml",
        "docs/index.md",
        "docs/gen_ref_pages.py",
        "docs/gen_home_pages.py",
        ".github/workflows/docs-deploy.yaml",
    }

    actual_files = {file_config["dest"] for file_config in mkdocs_component.files}
    assert actual_files == expected_files


def test_mkdocs_yml_content(components_dir):
    """Test mkdocs.yml template content."""
    mkdocs_yml_path = components_dir / "mkdocs" / "files" / "mkdocs.yml.j2"
    assert mkdocs_yml_path.exists()

    content = mkdocs_yml_path.read_text(encoding="utf-8")

    # Check for Material theme
    assert "material" in content
    assert "theme:" in content

    # Check for API reference generation
    assert "gen-files" in content
    assert "mkdocstrings" in content


def test_docs_index_content(components_dir):
    """Test docs/index.md template content."""
    index_path = components_dir / "mkdocs" / "files" / "docs" / "index.md.j2"
    assert index_path.exists()

    content = index_path.read_text(encoding="utf-8")

    # Check for project variables
    assert "{{cookiecutter.project_name}}" in content
    assert "{{cookiecutter.description}}" in content


def test_docs_deploy_workflow_content(components_dir):
    """Test docs deploy workflow content."""
    workflow_path = components_dir / "mkdocs" / "files" / "docs-deploy.yaml.j2"
    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    # Check for proper triggers
    assert "push:" in content
    assert "tags:" in content
    assert "workflow_dispatch:" in content
    assert "docs/**" in content
    assert "mkdocs.yml" in content

    # Check for MkDocs deployment
    assert "uv run mkdocs" in content or "task deploy:gh-pages" in content
    assert "astral-sh/setup-uv@v5" in content


def test_component_yaml_syntax(components_dir):
    """Test that component.yaml has valid syntax."""
    component_yaml = components_dir / "mkdocs" / "component.yaml"
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
        # Files should be either docs/, mkdocs.yml, or .github/workflows/
        dest = file_config["dest"]
        assert dest.startswith("docs/") or dest == "mkdocs.yml" or dest.startswith(".github/workflows/")


def test_file_templates_exist(components_dir):
    """Test that all referenced template files exist."""
    component_yaml = components_dir / "mkdocs" / "component.yaml"

    with open(component_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files_dir = components_dir / "mkdocs" / "files"

    for file_config in config["files"]:
        src_file = files_dir / file_config["src"]
        assert src_file.exists(), f"Template file not found: {src_file}"


def test_gen_ref_pages_content(components_dir):
    """Test gen_ref_pages.py content."""
    gen_ref_path = components_dir / "mkdocs" / "files" / "docs" / "gen_ref_pages.py.j2"
    assert gen_ref_path.exists()

    content = gen_ref_path.read_text(encoding="utf-8")

    # Check for API reference generation logic
    assert "mkdocs_gen_files" in content
    assert "{{cookiecutter.package_name}}" in content


def test_gen_home_pages_content(components_dir):
    """Test gen_home_pages.py content."""
    gen_home_path = components_dir / "mkdocs" / "files" / "docs" / "gen_home_pages.py.j2"
    assert gen_home_path.exists()

    content = gen_home_path.read_text(encoding="utf-8")

    # Check for home page generation logic
    assert "mkdocs_gen_files" in content
    assert "getting-started" in content
