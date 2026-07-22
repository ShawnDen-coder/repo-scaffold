"""Post-generation project setup and cleanup script for pnpm workspace projects."""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Union


# Mapping from cookiecutter choice to variant directory name
_VARIANT_DIRS = {
    "vue-app": "_vue-app",
    "ts-lib": "_ts-lib",
    "react-app": "_react-app",
    "ts-cli": "_ts-cli",
}


class ProjectValidator:
    """Validates rendered Cookiecutter values before cleanup and initialization."""

    def __init__(self):
        self.project_slug = "{{cookiecutter.project_slug}}"
        self.package_slug = "{{cookiecutter.package_slug}}"

    def validate(self) -> None:
        """Validate generated workspace and package names."""
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


class ProjectCleaner:
    """Handles removal of unnecessary files and directories based on cookiecutter choices."""

    def __init__(self):
        self.use_github_actions = "{{cookiecutter.use_github_actions}}" == "yes"
        self.initial_package_type = "{{cookiecutter.initial_package_type}}"

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
        """Remove multiple files or directories."""
        for file_path in files:
            self._safe_remove(file_path)

    def clean_github_actions_files(self) -> None:
        """Remove GitHub Actions files if not needed."""
        if self.use_github_actions:
            return

        github_files = [
            ".github",
            "cog.toml",
        ]
        print("Removing GitHub Actions files...")
        self._remove_files(github_files)

    def clean_shared_fragments(self) -> None:
        """Remove the _shared/ directory used for workflow fragment includes."""
        shared_dir = Path("_shared")
        if shared_dir.is_dir():
            print("Removing shared workflow fragments...")
            self._safe_remove(shared_dir)

    def select_sub_package_variant(self) -> None:
        """Keep only the chosen sub-package variant and rename it to the package slug.

        The template includes all four variant directories under packages/:
          _vue-app, _ts-lib, _react-app, _ts-cli

        This method:
          1. Renames the chosen variant to the user's package_slug
          2. Removes the other variant directories
        """
        chosen = self.initial_package_type
        chosen_dir = _VARIANT_DIRS.get(chosen)
        if not chosen_dir:
            print(f"Warning: Unknown initial_package_type '{chosen}', skipping variant cleanup.")
            return

        packages_dir = Path("packages")
        if not packages_dir.is_dir():
            print("Warning: packages/ directory not found, skipping variant cleanup.")
            return

        # Rename the chosen variant to the package slug
        variant_path = packages_dir / chosen_dir
        target_path = packages_dir / "{{cookiecutter.package_slug}}"

        if variant_path.is_dir():
            print(f"Renaming packages/{chosen_dir} → packages/{{cookiecutter.package_slug}}...")
            shutil.move(str(variant_path), str(target_path))
        else:
            print(f"Warning: Variant directory packages/{chosen_dir} not found.")

        # Remove all other variant directories
        for variant_name in _VARIANT_DIRS.values():
            variant_path = packages_dir / variant_name
            if variant_path.is_dir():
                print(f"Removing unused variant: packages/{variant_name}")
                self._safe_remove(variant_path)


class ProjectInitializer:
    """Handles project initialization tasks."""

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
                subprocess.run(["git", "init"], check=True, capture_output=True)
                subprocess.run(
                    ["git", "symbolic-ref", "HEAD", "refs/heads/master"],
                    check=True,
                    capture_output=True,
                )
            print("✅ Initialized empty git repository on branch 'master'")
        except FileNotFoundError:
            print("⚠️  git not found; skipped git init. Install git to enable version control.")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Skipped git init: {e}")

    def setup_environment(self) -> None:
        """Initialize workspace dependencies with pnpm."""
        if not self.install_after_generate:
            print("Skipping dependency installation (--no-install selected).")
            return

        workspace_dir = Path.cwd()
        if not (workspace_dir / "package.json").exists():
            print(f"Error: Workspace package.json not found in {workspace_dir}")
            sys.exit(1)

        try:
            print("Installing workspace dependencies with pnpm...")
            subprocess.run(["pnpm", "install"], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ pnpm not found. Please install pnpm first: https://pnpm.io/installation")
            sys.exit(1)


def main() -> None:
    """Main execution function."""
    print("🚀 Starting pnpm workspace post-generation setup...")

    validator = ProjectValidator()
    validator.validate()

    cleaner = ProjectCleaner()

    print("\n📁 Selecting sub-package variant...")
    cleaner.select_sub_package_variant()

    print("\n📁 Cleaning up unnecessary files...")
    cleaner.clean_shared_fragments()
    cleaner.clean_github_actions_files()

    print("\n🔧 Initializing workspace...")
    initializer = ProjectInitializer()
    initializer.init_git_repo()
    initializer.setup_environment()

    print("\n✨ Workspace setup completed successfully!")
    print(f"📂 Your project is ready at: {{cookiecutter.project_slug}}")


if __name__ == "__main__":
    main()
