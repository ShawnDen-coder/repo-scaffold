"""Tests for fixture data integrity and loading.

This module tests that all YAML fixture files can be loaded correctly
and contain the expected structure and data.
"""

from tests.conftest import FIXTURES_DIR
from tests.conftest import load_fixture_yaml


class TestFixtureLoading:
    """Test that all fixture files can be loaded and have correct structure."""

    def test_component_fixtures_load(self):
        """Test that all component fixture files can be loaded."""
        component_files = ["python_core.yaml", "cli_support.yaml", "docker.yaml", "podman.yaml", "github_actions.yaml"]

        for filename in component_files:
            config = load_fixture_yaml(f"components/{filename}")

            # Verify required fields are present
            assert "name" in config
            assert "display_name" in config
            assert "description" in config
            assert "category" in config
            assert "dependencies" in config
            assert "conflicts" in config
            assert "cookiecutter_vars" in config
            assert "files" in config
            assert "hooks" in config

            # Verify data types
            assert isinstance(config["name"], str)
            assert isinstance(config["display_name"], str)
            assert isinstance(config["description"], str)
            assert isinstance(config["category"], str)
            assert isinstance(config["dependencies"], list)
            assert isinstance(config["conflicts"], list)
            assert isinstance(config["cookiecutter_vars"], dict)
            assert isinstance(config["files"], list)
            assert isinstance(config["hooks"], dict)

    def test_template_fixtures_load(self):
        """Test that all template fixture files can be loaded."""
        template_files = ["python-library.yaml", "python-cli.yaml"]

        for filename in template_files:
            config = load_fixture_yaml(f"templates/{filename}")

            # Verify required fields are present
            assert "name" in config
            assert "display_name" in config
            assert "description" in config
            assert "required_components" in config
            assert "optional_components" in config
            assert "base_cookiecutter_config" in config

            # Verify data types
            assert isinstance(config["name"], str)
            assert isinstance(config["display_name"], str)
            assert isinstance(config["description"], str)
            assert isinstance(config["required_components"], list)
            assert isinstance(config["optional_components"], dict)
            assert isinstance(config["base_cookiecutter_config"], dict)

    def test_component_file_templates_exist(self):
        """Test that component file templates exist and can be read."""
        template_files = ["pyproject.toml.j2", "cli.py.j2", "__init__.py.j2", "Dockerfile.j2"]

        for filename in template_files:
            file_path = FIXTURES_DIR / "component_files" / filename
            assert file_path.exists(), f"Template file {filename} does not exist"

            # Verify file can be read
            content = file_path.read_text()
            assert len(content) > 0, f"Template file {filename} is empty"

            # Verify it contains Cookiecutter variables
            assert "{{cookiecutter." in content, f"Template file {filename} doesn't contain Cookiecutter variables"

    def test_fixture_data_consistency(self):
        """Test that fixture data is consistent across files."""
        # Load all component configs
        python_core = load_fixture_yaml("components/python_core.yaml")
        cli_support = load_fixture_yaml("components/cli_support.yaml")
        docker = load_fixture_yaml("components/docker.yaml")
        podman = load_fixture_yaml("components/podman.yaml")

        # Test dependency relationships
        assert "python_core" in cli_support["dependencies"]
        assert python_core["name"] == "python_core"
        assert cli_support["name"] == "cli_support"

        # Test conflict relationships
        assert "podman" in docker["conflicts"]
        assert "docker" in podman["conflicts"]

        # Load template configs
        python_library = load_fixture_yaml("templates/python-library.yaml")
        python_cli = load_fixture_yaml("templates/python-cli.yaml")

        # Test template requirements
        assert "python_core" in python_library["required_components"]
        assert "python_core" in python_cli["required_components"]
        assert "cli_support" in python_cli["required_components"]

    def test_fixture_comments_present(self):
        """Test that fixture files contain usage comments."""
        component_files = [
            "components/python_core.yaml",
            "components/cli_support.yaml",
            "templates/python-library.yaml",
        ]

        for filename in component_files:
            file_path = FIXTURES_DIR / filename
            content = file_path.read_text()

            # Check for usage comments
            assert "Used by tests:" in content, f"File {filename} missing usage comments"
            assert "test_" in content, f"File {filename} doesn't reference specific tests"


class TestFixtureUsage:
    """Test that fixtures are used correctly by the test suite."""

    def test_sample_component_configs_fixture(self, sample_component_configs):
        """Test that the sample_component_configs fixture works correctly."""
        assert "python_core" in sample_component_configs
        assert "cli_support" in sample_component_configs
        assert "docker" in sample_component_configs
        assert "podman" in sample_component_configs
        assert "github_actions" in sample_component_configs

        # Test that data is loaded from YAML
        python_core = sample_component_configs["python_core"]
        assert python_core["name"] == "python_core"
        assert python_core["display_name"] == "Python Core"
        assert python_core["category"] == "core"

    def test_sample_template_configs_fixture(self, sample_template_configs):
        """Test that the sample_template_configs fixture works correctly."""
        assert "python-library" in sample_template_configs
        assert "python-cli" in sample_template_configs

        # Test that data is loaded from YAML
        python_library = sample_template_configs["python-library"]
        assert python_library["name"] == "python-library"
        assert python_library["display_name"] == "Python Library"
        assert "python_core" in python_library["required_components"]
