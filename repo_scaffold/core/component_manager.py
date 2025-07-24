"""
Component management for repo-scaffold.

This module handles component discovery, dependency resolution, and validation.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Component:
    """Represents a single component with its configuration and metadata."""
    
    name: str
    display_name: str
    description: str
    category: str = "general"
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    cookiecutter_vars: Dict[str, Any] = field(default_factory=dict)
    files: List[Dict[str, str]] = field(default_factory=list)
    hooks: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, config_file: Path) -> "Component":
        """Load a component from a YAML configuration file."""
        if not config_file.exists():
            raise FileNotFoundError(f"Component configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {config_file}: {e}")
        
        # Validate required fields
        required_fields = ['name', 'display_name', 'description']
        for field_name in required_fields:
            if field_name not in config:
                raise ValueError(f"Missing required field '{field_name}' in {config_file}")
        
        return cls(
            name=config['name'],
            display_name=config['display_name'],
            description=config['description'],
            category=config.get('category', 'general'),
            dependencies=config.get('dependencies', []),
            conflicts=config.get('conflicts', []),
            cookiecutter_vars=config.get('cookiecutter_vars', {}),
            files=config.get('files', []),
            hooks=config.get('hooks', {})
        )


class ComponentManager:
    """Manages component discovery, dependency resolution, and validation."""
    
    def __init__(self, components_dir: Path):
        """Initialize the component manager with a components directory."""
        self.components_dir = Path(components_dir)
        self.components: Dict[str, Component] = self._discover_components()
    
    def _discover_components(self) -> Dict[str, Component]:
        """Discover all components in the components directory."""
        components = {}
        
        if not self.components_dir.exists():
            return components
        
        for component_dir in self.components_dir.iterdir():
            if not component_dir.is_dir():
                continue
            
            config_file = component_dir / "component.yaml"
            if not config_file.exists():
                continue
            
            try:
                component = Component.from_file(config_file)
                components[component.name] = component
            except (ValueError, yaml.YAMLError, FileNotFoundError) as e:
                # Log the error but continue discovering other components
                print(f"Warning: Failed to load component from {component_dir}: {e}")
                continue
        
        return components
    
    def resolve_dependencies(self, selected: List[str]) -> List[str]:
        """
        Resolve component dependencies recursively.
        
        Args:
            selected: List of selected component names
            
        Returns:
            List of component names including all dependencies
            
        Raises:
            KeyError: If a component or its dependency is not found
        """
        resolved = set()
        to_process = set(selected)
        processing = set()  # Track components being processed to detect cycles
        
        def _resolve_component(component_name: str):
            if component_name in resolved:
                return
            
            if component_name in processing:
                # Circular dependency detected - for now, just include both
                # In a more sophisticated implementation, we might raise an error
                return
            
            if component_name not in self.components:
                raise KeyError(f"Component '{component_name}' not found")
            
            processing.add(component_name)
            component = self.components[component_name]
            
            # Recursively resolve dependencies
            for dep in component.dependencies:
                _resolve_component(dep)
            
            processing.remove(component_name)
            resolved.add(component_name)
        
        # Process all selected components
        for component_name in selected:
            _resolve_component(component_name)
        
        return list(resolved)
    
    def validate_selection(self, selected: List[str]) -> List[str]:
        """
        Validate component selection for conflicts.
        
        Args:
            selected: List of selected component names
            
        Returns:
            List of conflict messages (empty if no conflicts)
        """
        conflicts = []
        
        for component_name in selected:
            if component_name not in self.components:
                continue
            
            component = self.components[component_name]
            for conflict in component.conflicts:
                if conflict in selected:
                    conflicts.append(f"{component_name} conflicts with {conflict}")
        
        return conflicts
    
    def get_component(self, name: str) -> Optional[Component]:
        """Get a component by name."""
        return self.components.get(name)
    
    def list_components(self) -> List[Component]:
        """Get a list of all available components."""
        return list(self.components.values())
    
    def get_components_by_category(self, category: str) -> List[Component]:
        """Get components filtered by category."""
        return [comp for comp in self.components.values() if comp.category == category]
