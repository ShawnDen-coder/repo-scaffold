"""Post-generation project setup script for uv workspace projects."""

import subprocess
import sys
from pathlib import Path


class ProjectInitializer:
    """Handles workspace initialization tasks."""

    def setup_environment(self) -> None:
        """Initialize workspace dependencies and environment."""
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
    initializer = ProjectInitializer()
    initializer.setup_environment()
    print("\n✨ Workspace setup completed successfully!")


if __name__ == "__main__":
    main()
