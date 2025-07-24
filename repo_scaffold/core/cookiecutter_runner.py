"""Cookiecutter runner for repo-scaffold.

This module handles running Cookiecutter with composed templates and managing temporary files.
"""

import shutil
from pathlib import Path
from typing import Any


try:
    from cookiecutter.main import cookiecutter
except ImportError:
    # Fallback for testing or when cookiecutter is not installed
    def cookiecutter(*args, **kwargs):
        """Fallback function when cookiecutter is not installed."""
        raise ImportError("cookiecutter package is required but not installed")


class CookiecutterRunner:
    """Runs Cookiecutter with composed templates and manages temporary files."""

    def __init__(self):
        """Initialize the Cookiecutter runner."""
        pass

    def run_cookiecutter(
        self,
        template_dir: Path,
        output_dir: Path | None = None,
        no_input: bool = False,
        extra_context: dict[str, Any] | None = None,
    ) -> Path:
        """Run Cookiecutter with the specified template.

        Args:
            template_dir: Path to the template directory
            output_dir: Output directory for the generated project (default: current directory)
            no_input: Whether to run without user input
            extra_context: Additional context variables for the template

        Returns:
            Path to the generated project directory

        Raises:
            Various cookiecutter exceptions if generation fails
        """
        # Convert Path objects to strings for cookiecutter
        template_path = str(template_dir)
        output_path = str(output_dir) if output_dir else "."

        # Prepare cookiecutter arguments
        kwargs = {"output_dir": output_path, "no_input": no_input}

        if extra_context:
            kwargs["extra_context"] = extra_context

        # Run cookiecutter
        result_path = cookiecutter(template_path, **kwargs)

        return Path(result_path)

    def cleanup_temp_template(self, template_dir: Path):
        """Clean up temporary template directory.

        Args:
            template_dir: Path to the temporary template directory to remove
        """
        try:
            shutil.rmtree(template_dir)
        except (OSError, PermissionError, FileNotFoundError) as e:
            # Log the error but don't raise - cleanup failures shouldn't break the workflow
            print(f"Warning: Failed to cleanup temporary template directory {template_dir}: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Could be used for cleanup if we track temporary directories
        pass
