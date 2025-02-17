"""Import Test."""

import importlib
import pkgutil

import {{cookiecutter.project_slug}} # noqa

def test_imports():
    """Test import modules."""
    prefix = "{}.".format({{cookiecutter.project_slug}}.__name__) # noqa
    iter_packages = pkgutil.walk_packages(
        {{cookiecutter.project_slug}}.__path__,  # noqa
        prefix,
    )
    for _, name, _ in iter_packages:
        module_name = name if name.startswith(prefix) else prefix + name
        importlib.import_module(module_name)