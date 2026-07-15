"""Add a new crate to the cargo workspace.

Usage: python scripts/add_package.py <crate-name>

This script:
1. Creates a minimal Cargo.toml package skeleton under packages/<name>/
2. Creates src/lib.rs
3. Appends a ``[packages.<name>]`` section to cog.toml for cocogitto tracking
4. Runs ``cargo check`` to verify the workspace compiles
"""

import subprocess
import sys
from pathlib import Path

# cocogitto uses {% raw %}{{version}}{% endraw %} as a template variable in pre_bump_hooks;
# build the literal string at runtime to avoid Jinja2 confusion during cookiecutter rendering.
_COG_VERSION_PLACEHOLDER = "{" + "{version}" + "}"

CARGO_TOML_TEMPLATE = """\
[package]
name = "{name}"
version.workspace = true
edition.workspace = true
license.workspace = true
authors.workspace = true
description = ""

[dependencies]
"""

LIB_RS_TEMPLATE = """\
// {name} crate
"""

COG_TOML_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "cargo workspaces version --all --force '*' --no-git-commit {version_placeholder}",
]
"""


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/add_package.py <crate-name>", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    pkg_dir = Path("packages") / name

    if pkg_dir.exists():
        print(f"❌ {pkg_dir} already exists", file=sys.stderr)
        sys.exit(1)

    # 1. Create package skeleton
    print(f"Creating crate '{name}' …")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    src_dir = pkg_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # Write Cargo.toml
    cargo_toml = pkg_dir / "Cargo.toml"
    cargo_toml.write_text(CARGO_TOML_TEMPLATE.format(name=name), encoding="utf-8")

    # Write src/lib.rs
    lib_rs = src_dir / "lib.rs"
    lib_rs.write_text(LIB_RS_TEMPLATE.format(name=name), encoding="utf-8")

    # 2. Append cog.toml section
    cog_path = Path("cog.toml")
    section = COG_TOML_SECTION_TEMPLATE.format(name=name, version_placeholder=_COG_VERSION_PLACEHOLDER)
    with cog_path.open("a", encoding="utf-8") as f:
        f.write(section)
    print(f"Appended [packages.{name}] to cog.toml")

    # 3. Verify workspace compiles
    print("Checking workspace …")
    result = subprocess.run(["cargo", "check"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  cargo check failed:\n{result.stderr}")
    else:
        print(f"✅ Crate '{name}' added. Crate name: {name}")
    print(f"\nNext steps:")
    print(f"  1. Add dependencies to packages/{name}/Cargo.toml")
    print(f"  2. Implement your domain in packages/{name}/src/")
    print(f"  3. Register routes in packages/api-server/src/app.rs")


if __name__ == "__main__":
    main()
