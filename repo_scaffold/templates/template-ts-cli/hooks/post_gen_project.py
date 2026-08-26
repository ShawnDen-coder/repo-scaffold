"""Initialize a generated TypeScript CLI project."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _run(command: list[str]) -> None:
    """Run a setup command and surface a concise failure."""
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print(f"Skipped {' '.join(command)}: command is not installed.")
    except subprocess.CalledProcessError as error:
        print(f"Skipped {' '.join(command)}: {error}")


def main() -> None:
    """Honor the standard install and git Cookiecutter options."""
    project_dir = Path.cwd()
    if "{{cookiecutter.use_github_actions}}" == "no":
        shutil.rmtree(project_dir / ".github", ignore_errors=True)
    if "{{cookiecutter.init_git}}" == "yes" and not (project_dir / ".git").exists():
        _run(["git", "init", "-b", "master"])
    if "{{cookiecutter.install_after_generate}}" == "yes":
        _run(["pnpm", "install"])


if __name__ == "__main__":
    main()
