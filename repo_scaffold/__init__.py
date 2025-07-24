"""
repo-scaffold: A modern project scaffolding tool with component-based architecture.

This package provides a flexible, component-based approach to project scaffolding
using Cookiecutter as the underlying template engine.
"""

__version__ = "0.11.0"
__author__ = "shawndeng"
__email__ = "shawndeng1109@qq.com"

from .core.component_manager import ComponentManager
from .core.template_composer import TemplateComposer
from .core.cookiecutter_runner import CookiecutterRunner

__all__ = [
    "ComponentManager",
    "TemplateComposer", 
    "CookiecutterRunner",
]
