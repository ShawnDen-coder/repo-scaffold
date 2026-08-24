"""Initialize and validate a generated pnpm Electron workspace."""

import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_SLUG = "{{cookiecutter.project_slug}}"
USE_GITHUB_ACTIONS = "{{cookiecutter.use_github_actions}}" == "yes"
INSTALL_AFTER_GENERATE = "{{cookiecutter.install_after_generate}}" == "yes"
INIT_GIT = "{{cookiecutter.init_git}}" == "yes"


def validate() -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", PROJECT_SLUG):
        print(f"Error: project_slug must be lowercase kebab-case (got {PROJECT_SLUG!r})")
        sys.exit(1)


def remove_optional_files() -> None:
    if USE_GITHUB_ACTIONS:
        return
    for path in (Path(".github"), Path("renovate.json5"), Path("cog.toml")):
        if path.exists():
            shutil.rmtree(path) if path.is_dir() else path.unlink()


def init_git() -> None:
    if not INIT_GIT or (Path.cwd() / ".git").exists():
        return
    try:
        subprocess.run(["git", "init", "-b", "main"], check=True, capture_output=True)
    except FileNotFoundError:
        print("Warning: git not found; skipped git initialization.")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "init"], check=True)


def install() -> None:
    if not INSTALL_AFTER_GENERATE:
        return
    try:
        subprocess.run(["pnpm", "install"], check=True)
    except FileNotFoundError:
        print("Error: pnpm not found. Install pnpm first: https://pnpm.io/installation")
        sys.exit(1)


def main() -> None:
    validate()
    remove_optional_files()
    init_git()
    install()
    print(f"Electron workspace ready: {PROJECT_SLUG}")


if __name__ == "__main__":
    main()
