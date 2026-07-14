"""Post-generation project setup and cleanup script for TanStack Start React projects."""

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

    def validate(self) -> None:
        """Validate generated project slug format."""
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.project_slug):
            print(
                "Error: project_slug must be a lowercase repository slug using letters, "
                f"numbers, and hyphens (got {self.project_slug!r})"
            )
            sys.exit(1)


class ProjectCleaner:
    """Handles removal of unnecessary files and directories based on cookiecutter choices."""

    def __init__(self):
        self.include_demos = "{{cookiecutter.include_demos}}" == "yes"
        self.use_docker = "{{cookiecutter.use_docker}}" == "yes"
        self.use_github_actions = "{{cookiecutter.use_github_actions}}" == "yes"

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

    def clean_demo_files(self) -> None:
        """Remove demo related files if demos are not needed."""
        if self.include_demos:
            return

        demo_files = [
            Path("src") / "routes" / "demo",
            Path("src") / "lib" / "demo-store.ts",
            Path("src") / "lib" / "demo-store-devtools.tsx",
            Path("src") / "components" / "demo.FormComponents.tsx",
            Path("src") / "hooks" / "demo.form-context.ts",
            Path("src") / "hooks" / "demo.form.ts",
        ]
        print("Removing demo files...")
        self._remove_files(demo_files)

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

    def clean_container_files(self) -> None:
        """Remove container related files if Docker/Podman is not used."""
        if self.use_docker:
            return

        container_files = [
            ".dockerignore",
            "container",
        ]
        print("Removing container files...")
        self._remove_files(container_files)


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
                # Older git without `-b`: init, then point HEAD at master.
                subprocess.run(["git", "init"], check=True, capture_output=True)
                subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/master"], check=True, capture_output=True)
            print("✅ Initialized empty git repository on branch 'master'")
        except FileNotFoundError:
            print("⚠️  git not found; skipped git init. Install git to enable version control.")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Skipped git init: {e}")

    def setup_environment(self) -> None:
        """Initialize project dependencies with pnpm."""
        if not self.install_after_generate:
            print("Skipping dependency installation (--no-install selected).")
            return

        project_dir = Path.cwd()
        if not (project_dir / "package.json").exists():
            print(f"Error: Project package.json not found in {project_dir}")
            sys.exit(1)

        try:
            print("Installing project dependencies with pnpm...")
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
    print("🚀 Starting TanStack Start React project post-generation setup...")

    validator = ProjectValidator()
    validator.validate()

    cleaner = ProjectCleaner()

    print("\n📁 Cleaning up unnecessary files...")
    cleaner.clean_demo_files()
    cleaner.clean_container_files()
    cleaner.clean_github_actions_files()

    print("\n🔧 Initializing project...")
    initializer = ProjectInitializer()
    initializer.init_git_repo()
    initializer.setup_environment()

    print("\n✨ Project setup completed successfully!")
    print(f"📂 Your project is ready at: {{cookiecutter.project_slug}}")


if __name__ == "__main__":
    main()
