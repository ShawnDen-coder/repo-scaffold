"""Post-generation project setup and cleanup script for pnpm workspace projects."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from repo_scaffold.workspace_member import WorkspaceEcosystem
from repo_scaffold.workspace_member import add_member
from repo_scaffold.workspace_member import build_member_spec


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

    def clean_github_actions_files(self) -> None:
        """Remove GitHub Actions files if not needed."""
        if self.use_github_actions:
            return

        github_files = [
            ".github",
            "cog.toml",
        ]
        print("Removing GitHub Actions files...")
        for file_path in github_files:
            path = Path(file_path)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"Removed: {path}")

    def clean_shared_fragments(self) -> None:
        """Remove the _shared/ directory used for workflow fragment includes."""
        shared_dir = Path("_shared")
        if shared_dir.is_dir():
            print("Removing shared workflow fragments...")
            shutil.rmtree(shared_dir)
            print(f"Removed: {shared_dir}")


def create_initial_member() -> None:
    """Generate the initial package through the shared member provider."""
    spec = build_member_spec(
        project_path=Path.cwd(),
        name="{{cookiecutter.package_slug}}",
        ecosystem=WorkspaceEcosystem.PNPM,
        member_type="{{cookiecutter.initial_package_type}}",
        location="packages",
        private=True,
        public_api=True,
        no_install=True,
        no_verify=True,
    )
    add_member(spec)


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

    print("\n📦 Creating initial workspace member...")
    create_initial_member()

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
