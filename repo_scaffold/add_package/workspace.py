"""Workspace-specific add-package implementations.

Two functions, one per workspace type, that create the package skeleton,
update ``cog.toml`` for cocogitto tracking, and verify the workspace
compiles/syncs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

from .config import AddPackageConfig


# cocogitto uses {{version}} as a template variable in pre_bump_hooks;
# build the literal string at runtime.
_COG_VERSION_PLACEHOLDER = "{" + "{version}" + "}"

# ---------------------------------------------------------------------------
# Rust workspace
# ---------------------------------------------------------------------------

_CARGO_TOML_TEMPLATE = """\
[package]
name = "{name}"
version.workspace = true
edition.workspace = true
license.workspace = true
authors.workspace = true
description = ""

[dependencies]
"""

_LIB_RS_TEMPLATE = """\
// {name} crate
"""

_RUST_COG_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "cargo workspaces version --all --force '*' --no-git-commit {version_placeholder}",
]
"""


def add_rust_package(config: AddPackageConfig) -> None:
    """Add a new crate to a cargo workspace.

    Steps:
      1. Validate ``packages/<name>`` does not already exist.
      2. Create ``packages/<name>/Cargo.toml`` and ``src/lib.rs``.
      3. Append a ``[packages.<name>]`` section to ``cog.toml``.
      4. Run ``cargo check`` to verify the workspace compiles.
    """
    name = config.name
    project_path = config.project_path
    pkg_dir = project_path / "packages" / name

    if pkg_dir.exists():
        raise click.ClickException(f"❌ {pkg_dir.relative_to(project_path)} already exists")

    # 1. Create package skeleton
    click.echo(f"Creating crate '{name}' …")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    src_dir = pkg_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # Write Cargo.toml
    cargo_toml = pkg_dir / "Cargo.toml"
    cargo_toml.write_text(_CARGO_TOML_TEMPLATE.format(name=name), encoding="utf-8")

    # Write src/lib.rs
    lib_rs = src_dir / "lib.rs"
    lib_rs.write_text(_LIB_RS_TEMPLATE.format(name=name), encoding="utf-8")

    # 2. Append cog.toml section
    _append_cog_section(project_path, name, _RUST_COG_SECTION_TEMPLATE)

    # 3. Verify workspace compiles
    click.echo("Checking workspace …")
    result = subprocess.run(
        ["cargo", "check"],
        cwd=str(project_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"⚠️  cargo check failed:\n{result.stderr}")
    else:
        click.echo(f"✅ Crate '{name}' added.")

    click.echo("\nNext steps:")
    click.echo(f"  1. Add dependencies to packages/{name}/Cargo.toml")
    click.echo(f"  2. Implement your domain in packages/{name}/src/")
    click.echo("  3. Register routes in packages/api-server/src/app.rs")


# ---------------------------------------------------------------------------
# uv workspace
# ---------------------------------------------------------------------------

_UV_COG_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "uv version --package {name} {version_placeholder}",
]
"""


def add_uv_package(config: AddPackageConfig) -> None:
    """Add a new package to a uv workspace.

    Steps:
      1. Validate ``packages/<name>`` does not already exist.
      2. Run ``uv init --lib`` to create the package skeleton.
      3. Append a ``[packages.<name>]`` section to ``cog.toml``.
      4. Run ``uv sync --all-packages --all-groups`` to update the lockfile.
    """
    name = config.name
    project_path = config.project_path
    pkg_dir = project_path / "packages" / name

    if pkg_dir.exists():
        raise click.ClickException(f"❌ {pkg_dir.relative_to(project_path)} already exists")

    # 1. Create package skeleton via uv
    click.echo(f"Creating package '{name}' …")
    subprocess.check_call(
        ["uv", "init", "--lib", "--name", name, str(pkg_dir)],
        cwd=str(project_path),
    )

    # 2. Append cog.toml section
    _append_cog_section(project_path, name, _UV_COG_SECTION_TEMPLATE)

    # 3. Sync workspace
    click.echo("Syncing workspace …")
    subprocess.check_call(
        ["uv", "sync", "--all-packages", "--all-groups"],
        cwd=str(project_path),
    )

    module = name.replace("-", "_")
    click.echo(f"✅ Package '{name}' added. Module import name: {module}")


# ---------------------------------------------------------------------------
# pnpm workspace
# ---------------------------------------------------------------------------

_PNPM_PACKAGE_JSON_TEMPLATE = """\
{{
  "name": "{name}",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.cjs",
  "module": "dist/index.mjs",
  "types": "dist/index.d.ts",
  "exports": {{
    ".": {{
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs"
    }}
  }},
  "files": ["dist"],
  "scripts": {{
    "build": "vite build",
    "typecheck": "tsc --noEmit"
  }},
  "devDependencies": {{
    "typescript": "~5.9.3",
    "vite": "^7.3.1",
    "vite-plugin-dts": "^4.5.4"
  }}
}}
"""

_PNPM_VITE_CONFIG_TEMPLATE = """\
import {{ defineConfig }} from 'vite'
import {{ resolve }} from 'path'
import dts from 'vite-plugin-dts'

export default defineConfig({{
  publicDir: false,
  build: {{
    lib: {{
      entry: resolve(__dirname, 'src/index.ts'),
      name: '{name}',
      formats: ['es', 'cjs'],
      fileName: (format) => `index.${{format === 'es' ? 'mjs' : 'cjs'}}`,
    }},
  }},
  plugins: [dts({{ rollupTypes: true }})],
  resolve: {{
    alias: [{{ find: /^@(.+)$/, replacement: new URL('./src/$1', import.meta.url).pathname }}],
  }},
}})
"""

_PNPM_TSCONFIG_TEMPLATE = """\
{{
  "compilerOptions": {{
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2022"],
    "types": ["vite/client"],
    "baseUrl": ".",
    "paths": {{ "@*": ["src/*", "src/*/index"] }},
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  }},
  "include": ["src"]
}}
"""

_PNPM_INDEX_TS_TEMPLATE = """\
// {name} entry point
export const version = '0.1.0'
"""

_PNPM_COG_SECTION_TEMPLATE = """\

[packages.{name}]
path = "packages/{name}"
public_api = true
changelog_path = "packages/{name}/CHANGELOG.md"
pre_bump_hooks = [
    "pnpm --filter {name} version {version_placeholder} --no-git-tag-version",
]
"""


def add_pnpm_package(config: AddPackageConfig) -> None:
    """Add a new package to a pnpm workspace.

    Steps:
      1. Validate ``packages/<name>`` does not already exist.
      2. Create ``packages/<name>/package.json``, ``vite.config.ts``,
         ``tsconfig.json``, and ``src/index.ts``.
      3. Append a ``[packages.<name>]`` section to ``cog.toml``.
      4. Run ``pnpm install`` to update the lockfile.
    """
    name = config.name
    project_path = config.project_path
    pkg_dir = project_path / "packages" / name

    if pkg_dir.exists():
        raise click.ClickException(f"❌ {pkg_dir.relative_to(project_path)} already exists")

    # 1. Create package skeleton
    click.echo(f"Creating package '{name}' …")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    src_dir = pkg_dir / "src"
    src_dir.mkdir(exist_ok=True)

    (pkg_dir / "package.json").write_text(_PNPM_PACKAGE_JSON_TEMPLATE.format(name=name), encoding="utf-8")
    (pkg_dir / "vite.config.ts").write_text(_PNPM_VITE_CONFIG_TEMPLATE.format(name=name), encoding="utf-8")
    (pkg_dir / "tsconfig.json").write_text(_PNPM_TSCONFIG_TEMPLATE.format(), encoding="utf-8")
    (src_dir / "index.ts").write_text(_PNPM_INDEX_TS_TEMPLATE.format(name=name), encoding="utf-8")

    # 2. Append cog.toml section
    _append_cog_section(project_path, name, _PNPM_COG_SECTION_TEMPLATE)

    # 3. Sync workspace
    click.echo("Syncing workspace …")
    subprocess.check_call(
        ["pnpm", "install"],
        cwd=str(project_path),
    )

    click.echo(f"✅ Package '{name}' added.")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _append_cog_section(
    project_path: Path,
    name: str,
    template: str,
) -> None:
    """Append a ``[packages.<name>]`` section to ``cog.toml``."""
    cog_path = project_path / "cog.toml"
    section = template.format(name=name, version_placeholder=_COG_VERSION_PLACEHOLDER)
    with cog_path.open("a", encoding="utf-8") as f:
        f.write(section)
    click.echo(f"Appended [packages.{name}] to cog.toml")
