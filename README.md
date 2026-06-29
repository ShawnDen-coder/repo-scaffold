# repo-scaffold

[![PyPI version](https://badge.fury.io/py/repo-scaffold.svg)](https://badge.fury.io/py/repo-scaffold)
[![Python Version](https://img.shields.io/pypi/pyversions/repo-scaffold.svg)](https://pypi.org/project/repo-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
```

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

Both templates use `just` (via `rust-just`) as the task runner — every recipe can be run without a prior install via `uvx --from rust-just just <recipe>`.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/ShawnDen-coder/repo-scaffold.git
cd repo-scaffold

# Sync dependencies and install pre-commit hooks
uvx --from rust-just just init

# Run lint and tests
uvx --from rust-just just lint
uvx --from rust-just just test
```

## Releasing

This project (and the templates it generates) uses Cocogitto driven by conventional commits:

- Push a `feat:` / `fix:` / breaking-change commit to `master` and the `version-bump` workflow runs `cog bump --auto`, updating `CHANGELOG.md`, bumping `pyproject.toml` via `uv version`, committing, and tagging.
- The release workflow then builds and publishes the tagged version.

See `cog.toml` for hook and changelog configuration.
