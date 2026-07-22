# repo-scaffold

[![PyPI](https://img.shields.io/pypi/v/repo-scaffold.svg)](https://pypi.org/project/repo-scaffold/)
[![Python Version](https://img.shields.io/pypi/pyversions/repo-scaffold.svg)](https://pypi.org/project/repo-scaffold/)
[![CI](https://github.com/ShawnDen-coder/repo-scaffold/actions/workflows/ci-tests.yaml/badge.svg)](https://github.com/ShawnDen-coder/repo-scaffold/actions/workflows/ci-tests.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A modern project scaffolding tool that helps you quickly create standardized project structures with best practices.

## Features

- 🚀 Quick project initialization with modern best practices
- 📦 Cookiecutter templates with standardized structure
- ⚙️ Interactive project configuration
- 🔧 Pre-configured development tools (ruff, pytest, just)
- 📚 Documentation setup with MkDocs Material
- 🔄 GitHub Actions workflows included
- 🏷️ Conventional-commit driven versioning via [Cocogitto](https://docs.cocogitto.io/)
- 📦 Dependency / workspace management with [uv](https://docs.astral.sh/uv/)

## Installation

```bash
# Recommended: install as a uv tool
uv tool install repo-scaffold

# Or run without installing
uvx repo-scaffold list

# Or with pip
pip install repo-scaffold
```

## Quick Start

```bash
# List available templates
repo-scaffold list

# Create a new project (interactive)
repo-scaffold create python

# Create a project in a specific directory, no prompts
repo-scaffold create python --no-input -o ./my-projects

# Create a uv workspace monorepo
repo-scaffold create uv-workspace -o ./my-projects

# Push a generated project to GitHub: create the repo, set CI secrets,
# push the initial commit, create the gh-pages branch, and point GitHub
# Pages at it. Reads GITHUB_TOKEN from the environment.
export GITHUB_TOKEN=ghp_...
repo-scaffold gh-init ./my-projects/my-python-project

# Add a new package to a workspace project (auto-detects Rust or uv)
repo-scaffold add-package my-new-lib -p ./my-projects/my-workspace
```

See the [GitHub bootstrap docs](https://shawnden-coder.github.io/repo-scaffold/templates/gh-init/) for the full flag list and the secrets/variables `gh-init` knows how to set.

## End-to-End: From `create` to GitHub Pages

A full walkthrough from an empty directory to a published repository with CI and docs.

```bash
# 1. Generate the project. `create` also runs `git init` on branch `master`
#    (opt out with --no-git). Drop --no-input to configure it interactively.
repo-scaffold create python --no-input -o ./workspace
cd ./workspace/my_python_project   # directory name is the project_slug

# 2. (Optional) make your own first changes here. gh-init creates the
#    initial commit for you, so an extra commit at this point is optional.

# 3. Provide a GitHub token with `repo` scope (or `public_repo` for public repos).
export GITHUB_TOKEN=ghp_...

# 4. Bootstrap GitHub. By default gh-init will:
#      - create the repository (name/description pulled from pyproject.toml)
#      - set the CI secrets/variables the generated workflows expect
#      - push the initial commit to `master`
#      - create the `gh-pages` branch and set it as the GitHub Pages source
repo-scaffold gh-init .

# 5. Publish docs: push a release tag (or let the Cocogitto version-bump
#    workflow create one). The docs-deploy workflow builds the site and
#    pushes it to `gh-pages`, which GitHub Pages now serves automatically.
git push --tags   # or: git tag 0.1.0 && git push origin 0.1.0
```

Common opt-outs:

- `repo-scaffold create python --no-git` — skip the local `git init`.
- `repo-scaffold gh-init . --private` — create a private repository.
- `repo-scaffold gh-init . --protect-branch` — protect the default branch (require PR review; admins can still push so releases keep working).
- `repo-scaffold gh-init . --no-push` — create the repo and set secrets without pushing (Pages setup is skipped, since it needs the pushed branch).
- `repo-scaffold gh-init . --no-pages` — push, but don't create `gh-pages` or configure Pages (you can set it later in repo Settings → Pages).

## Available Templates

Currently supported project templates:

- **`python`** — single-package Python project
  - `pyproject.toml` + `uv` for dependency management
  - `pytest` + coverage, `ruff` for lint & format
  - Optional Click CLI, Podman compose files, GitHub Actions, MkDocs Material docs
  - Cocogitto release workflow that bumps version, writes `CHANGELOG.md`, tags, and triggers PyPI publish

- **`uv-workspace`** — uv workspace monorepo
  - Workspace-aware `pyproject.toml` with one initial member under `packages/`
  - Shared `dev` / `docs` dependency groups
  - Cocogitto monorepo release workflow with per-package and global tags
  - Same lint / test / docs tooling as the python template

- **`react`** — TanStack Start (SSR React) project
  - TanStack Router/Query/Form/Store, MUI, Tailwind CSS
  - Biome for lint/format, pnpm for deps, Vitest for testing
  - Optional Docker/Podman support, GitHub Actions CI, and demo pages

- **`rust`** — Axum + SQLx cargo workspace project
  - Cargo workspace with `packages/api-server/` as initial member
  - Domain-driven architecture (domain/infra/api/dto layers)
  - Axum web framework + SQLx (PostgreSQL, compile-time queries, offline mode)
  - JWT auth middleware, health check reference domain
  - Optional Docker/Podman, GitHub Actions CI, OpenAPI/Swagger (utoipa), and OpenTelemetry support
  - Cocogitto monorepo versioning with `cargo-workspaces`

- **`ts-sdk`** — TypeScript SDK library
  - Vite lib mode producing dual ESM + CJS output with bundled type declarations
  - Generic `ApiClient` with automatic token lifecycle (authenticate → cache → refresh → fallback)
  - `AuthService` supporting four OAuth grant types with exponential-backoff retry
  - Prettier for formatting, pnpm for deps
  - Optional GitHub Actions CI + dual npm/GPR publish + Cocogitto version bump

- **`pnpm-workspace`** — pnpm monorepo with mixed sub-package types
  - Workspace root with `pnpm-workspace.yaml` + Prettier
  - Initial sub-package type selection: `vue-app` / `ts-lib` / `react-app` / `ts-cli`
  - Cocogitto monorepo versioning with `pnpm --filter` per-package hooks
  - `repo-scaffold add-package` supports adding new sub-packages to pnpm workspaces
  - Optional GitHub Actions CI

- **`vue-project`** — standalone Vue 3 project with Router, Pinia, and Tailwind CSS
  - Full layered component structure: `components/ui/`, `components/layout/`, `components/common/`
  - Pages with colocated sub-components: `pages/HomePage/`, `pages/AboutPage/`
  - Vue Router with lazy-loaded routes, Pinia stores with Composition API
  - Tailwind CSS v4 via `@tailwindcss/vite`, Prettier, pnpm
  - Optional GitHub Actions CI + Cocogitto version bump

Both templates use `just` (via `rust-just`) as the task runner. Bootstrap from a clean machine with `uvx --from rust-just just init` — that recipe also installs `rust-just` as a uv tool, so every subsequent recipe can be run as plain `just <recipe>`.

## Adding Packages to Workspaces

The `add-package` command adds a new member to a workspace project and updates `cog.toml` for Cocogitto tracking:

```bash
# Inside a generated workspace project directory
repo-scaffold add-package my-new-lib

# Or specify the project path explicitly
repo-scaffold add-package my-new-lib -p /path/to/project
```

The command auto-detects the project type:
- **Rust workspace** (`Cargo.toml` with `[workspace]`): creates a crate skeleton under `packages/<name>/`, appends a `[packages.<name>]` section to `cog.toml` with `cargo workspaces version` pre-bump hooks, and runs `cargo check`.
- **uv workspace** (`pyproject.toml` with `[tool.uv.workspace]`): runs `uv init --lib`, appends a `[packages.<name>]` section to `cog.toml` with `uv version --package` pre-bump hooks, and runs `uv sync`.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/ShawnDen-coder/repo-scaffold.git
cd repo-scaffold

# Bootstrap once: installs rust-just as a uv tool, syncs deps, installs hooks
uvx --from rust-just just init

# Subsequent runs use `just` directly
just lint
just test
```

## Releasing

This project (and the templates it generates) uses Cocogitto driven by conventional commits:

- Push a `feat:` / `fix:` / breaking-change commit to `master` and the `version-bump` workflow runs `cog bump --auto`, updating `CHANGELOG.md`, bumping `pyproject.toml` via `uv version`, committing, and tagging.
- The release workflow then builds and publishes the tagged version.

See `cog.toml` for hook and changelog configuration.
