"""Initialize and validate a generated pnpm Electron workspace."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from repo_scaffold.workspace_member import WorkspaceEcosystem
from repo_scaffold.workspace_member import add_member
from repo_scaffold.workspace_member import build_member_spec


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


def create_workspace_members() -> None:
    """Create the Electron workspace members through shared pnpm templates."""
    workspace = Path.cwd()
    members = (
        ("shared", "ts-lib", "packages", ()),
        ("ui", "react-lib", "packages", (f"@{PROJECT_SLUG}/shared",)),
        ("web", "react-app", "apps", (f"@{PROJECT_SLUG}/ui",)),
        ("desktop", "electron-app", "apps", ()),
    )
    for name, member_type, location, depends_on in members:
        spec = build_member_spec(
            project_path=workspace,
            name=name,
            ecosystem=WorkspaceEcosystem.PNPM,
            member_type=member_type,
            location=location,
            scope=f"@{PROJECT_SLUG}",
            private=True,
            public_api=False,
            depends_on=depends_on,
            no_install=True,
            no_verify=True,
        )
        add_member(spec)


def init_git() -> None:
    if not INIT_GIT or (Path.cwd() / ".git").exists():
        return
    try:
        subprocess.run(["git", "init", "-b", "master"], check=True, capture_output=True)
    except FileNotFoundError:
        print("Warning: git not found; skipped git initialization.")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "init"], check=True)


def install() -> None:
    if not INSTALL_AFTER_GENERATE:
        return
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        print(
            "Warning: pnpm not found; skipped dependency installation. "
            "Install pnpm and run pnpm install in the generated project: "
            "https://pnpm.io/installation"
        )
        return
    subprocess.run([pnpm, "install"], check=True)


def main() -> None:
    validate()
    create_workspace_members()
    remove_optional_files()
    init_git()
    install()
    print(f"Electron workspace ready: {PROJECT_SLUG}")


if __name__ == "__main__":
    main()
