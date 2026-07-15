"""Add a new package to the uv workspace.

.. deprecated::
    Use ``repo-scaffold add-package <name>`` instead.
    This script will be removed in a future release.

Usage: python scripts/add_package.py <package-name>

This script:
1. Runs ``uv init --lib`` to create the package skeleton under packages/<name>/
2. Appends a ``[packages.<name>]`` section to cog.toml for cocogitto tracking
3. Runs ``uv sync --all-packages --all-groups`` to update the lockfile
"""

import subprocess
import sys
from pathlib import Path

# cocogitto uses {% raw %}{{version}}{% endraw %} as a template variable in pre_bump_hooks;
# build the literal string at runtime to avoid Jinja2 confusion during cookiecutter rendering.
_COG_VERSION_PLACEHOLDER = "{" + "{version}" + "}"

COG_TOML_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "uv version --package {name} {version_placeholder}",
]
"""


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/add_package.py <package-name>", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    pkg_dir = Path("packages") / name

    if pkg_dir.exists():
        print(f"❌ {pkg_dir} already exists", file=sys.stderr)
        sys.exit(1)

    # 1. Create package skeleton
    print(f"Creating package '{name}' …")
    subprocess.check_call(["uv", "init", "--lib", "--name", name, str(pkg_dir)])

    # 2. Append cog.toml section
    cog_path = Path("cog.toml")
    section = COG_TOML_SECTION_TEMPLATE.format(name=name, version_placeholder=_COG_VERSION_PLACEHOLDER)
    with cog_path.open("a", encoding="utf-8") as f:
        f.write(section)
    print(f"Appended [packages.{name}] to cog.toml")

    # 3. Sync workspace
    print("Syncing workspace …")
    subprocess.check_call(["uv", "sync", "--all-packages", "--all-groups"])

    module = name.replace("-", "_")
    print(f"✅ Package '{name}' added. Module import name: {module}")


if __name__ == "__main__":
    main()
