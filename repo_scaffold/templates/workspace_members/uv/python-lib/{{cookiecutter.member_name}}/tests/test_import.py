"""Import test."""

import importlib


def test_import_package() -> None:
    """Test package import."""
    importlib.import_module("{{ cookiecutter.package_module }}")
