"""Post-generation project setup and cleanup script for uv workspace projects."""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Union


class ProjectValidator:
    """Validates rendered Cookiecutter values before cleanup and initialization."""

    def __init__(self):
        self.project_slug = "{{cookiecutter.project_slug}}"
        self.package_slug = "{{cookiecutter.package_slug}}"
        self.package_module = "{{cookiecutter.package_module}}"
        self.min_python_version = "{{cookiecutter.min_python_version}}"
        self.max_python_version = "{{cookiecutter.max_python_version}}"

    def _version_tuple(self, version: str) -> tuple[int, int]:
        """Convert a Python major.minor version string into a comparable tuple."""
        major, minor = version.split(".", 1)
        return int(major), int(minor)

    def validate(self) -> None:
        """Validate generated workspace, distribution, and module names."""
        if self._version_tuple(self.min_python_version) > self._version_tuple(self.max_python_version):
            print(
                "Error: min_python_version must be less than or equal to max_python_version "
                f"({self.min_python_version} > {self.max_python_version})"
            )
            sys.exit(1)

        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.project_slug):
            print(
                "Error: project_slug must be a lowercase repository slug using letters, "
                f"numbers, and hyphens (got {self.project_slug!r})"
            )
            sys.exit(1)

        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.package_slug):
            print(
                "Error: package_slug must be a lowercase distribution name using letters, "
                f"numbers, and hyphens (got {self.package_slug!r})"
            )
            sys.exit(1)

        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", self.package_module):
            print(
                "Error: package_module must be a valid Python module name "
                f"(got {self.package_module!r})"
            )
            sys.exit(1)


class ProjectCleaner:
    """Handles removal of unnecessary files and directories based on cookiecutter choices."""

    def __init__(self):
        self.use_github_actions = "{{cookiecutter.use_github_actions}}" == "yes"

    def _safe_remove(self, path: Union[str, Path]) -> bool:
        """Safely remove a file or directory."""
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
        """Remove multiple files or directories."""
        for file_path in files:
            self._safe_remove(file_path)

    def clean_github_actions_files(self) -> None:
        """Remove GitHub Actions and documentation files if not needed."""
        if self.use_github_actions:
            return

        github_files = [
            ".github",
            "mkdocs.yml",
            "docs",
        ]
        print("Removing GitHub Actions and documentation files...")
        self._remove_files(github_files)


class ProjectInitializer:
    """Handles workspace initialization tasks."""

    def __init__(self):
        self.install_after_generate = "{{cookiecutter.install_after_generate}}" == "yes"
        self.init_git = "{{cookiecutter.init_git}}" == "yes"

    def init_git_repo(self) -> None:
        """Initialize a git repository on branch ``master`` (best effort)."""
        if not self.init_git:
            print("Skipping git init (--no-git selected).")
            return

        if (Path.cwd() / ".git").exists():
            print("Git repository already initialized, skipping git init.")
            return

        try:
            print("Initializing git repository (branch: master)...")
            try:
                subprocess.run(["git", "init", "-b", "master"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Older git without `-b`: init, then point HEAD at master.
                subprocess.run(["git", "init"], check=True, capture_output=True)
                subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/master"], check=True, capture_output=True)
            print("✅ Initialized empty git repository on branch 'master'")
        except FileNotFoundError:
            print("⚠️  git not found; skipped git init. Install git to enable version control.")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Skipped git init: {e}")

    def setup_environment(self) -> None:
        """Initialize workspace dependencies and environment."""
        if not self.install_after_generate:
            print("Skipping dependency installation (--no-install selected).")
            return

        workspace_dir = Path.cwd()
        if not (workspace_dir / "pyproject.toml").exists():
            print(f"Error: Workspace pyproject.toml not found in {workspace_dir}")
            sys.exit(1)

        try:
            print("Installing workspace dependencies...")
            subprocess.run(["uv", "sync", "--all-groups"], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ uv not found. Please install uv first: https://docs.astral.sh/uv/")
            sys.exit(1)


def main() -> None:
    """Main execution function."""
    print("🚀 Starting uv workspace post-generation setup...")

    validator = ProjectValidator()
    validator.validate()

    cleaner = ProjectCleaner()
    print("\n📁 Cleaning up unnecessary files...")
    cleaner.clean_github_actions_files()

    print("\n🔧 Initializing workspace...")
    initializer = ProjectInitializer()
    initializer.init_git_repo()
    initializer.setup_environment()
    print("\n✨ Workspace setup completed successfully!")


if __name__ == "__main__":
    main()
