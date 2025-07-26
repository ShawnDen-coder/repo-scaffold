"""Post-generation project setup and cleanup script.

This script runs after cookiecutter generates the project template.
It removes unnecessary files based on user choices and initializes the project.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Union


class ProjectCleaner:
    """Handles removal of unnecessary files and directories based on cookiecutter choices."""

    def __init__(self):
        self.project_slug = "{{cookiecutter.project_slug}}"
        self.use_cli = "{{cookiecutter.include_cli}}" == "yes"
        self.use_github_actions = "{{cookiecutter.use_github_actions}}" == "yes"
        self.use_podman = "{{cookiecutter.use_podman}}" == "yes"

    def _safe_remove(self, path: Union[str, Path]) -> bool:
        """Safely remove a file or directory.

        Args:
            path: Path to remove

        Returns:
            bool: True if removed successfully, False otherwise
        """
        try:
            path = Path(path)
            if not path.exists():
                return False

            if path.is_file():
                path.unlink()
                print(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            return True
        except Exception as e:
            print(f"Warning: Failed to remove {path}: {e}")
            return False

    def _remove_files(self, files: List[Union[str, Path]]) -> None:
        """Remove multiple files or directories.

        Args:
            files: List of file/directory paths to remove
        """
        for file_path in files:
            self._safe_remove(file_path)

    def clean_cli_files(self) -> None:
        """Remove CLI related files if CLI is not needed."""
        if self.use_cli:
            return

        cli_files = [
            Path(self.project_slug) / "cli.py"
        ]
        print("Removing CLI files...")
        self._remove_files(cli_files)

    def clean_container_files(self) -> None:
        """Remove container related files if Podman is not used."""
        if self.use_podman:
            return

        container_files = [
            ".dockerignore",
            "container",
            Path(".github") / "workflows" / "container-release.yaml"
        ]
        print("Removing container files...")
        self._remove_files(container_files)

    def clean_github_actions_files(self) -> None:
        """Remove GitHub Actions and documentation files if not needed."""
        if self.use_github_actions:
            return

        github_files = [
            ".github",
            "mkdocs.yml",
            "docs"
        ]
        print("Removing GitHub Actions and documentation files...")
        self._remove_files(github_files)


class ProjectInitializer:
    """Handles project initialization tasks."""

    def __init__(self):
        self.project_slug = "{{cookiecutter.project_slug}}"

    def setup_environment(self) -> None:
        """Initialize project dependencies and environment."""
        project_dir = Path(self.project_slug).resolve()

        if not project_dir.exists():
            print(f"Error: Project directory {project_dir} does not exist")
            sys.exit(1)

        print(f"Changing to project directory: {project_dir}")
        os.chdir(project_dir)

        try:
            print("Installing project dependencies...")
            subprocess.run(["task", "init"], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ uv not found. Please install uv first: https://docs.astral.sh/uv/")
            sys.exit(1)


def main() -> None:
    """Main execution function."""
    print("🚀 Starting post-generation project setup...")

    # Initialize cleaner and perform cleanup
    cleaner = ProjectCleaner()

    print("\n📁 Cleaning up unnecessary files...")
    cleaner.clean_cli_files()
    cleaner.clean_container_files()
    cleaner.clean_github_actions_files()

    # Initialize project
    print("\n🔧 Initializing project...")
    initializer = ProjectInitializer()
    initializer.setup_environment()

    print("\n✨ Project setup completed successfully!")
    print(f"📂 Your project is ready at: {{cookiecutter.project_slug}}")


if __name__ == "__main__":
    main()