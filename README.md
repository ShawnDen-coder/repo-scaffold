# repo-scaffold

[![PyPI version](https://badge.fury.io/py/repo-scaffold.svg)](https://badge.fury.io/py/repo-scaffold)
[![Python Version](https://img.shields.io/pypi/pyversions/repo-scaffold.svg)](https://pypi.org/project/repo-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern project scaffolding tool that helps you quickly create standardized project structures with best practices.

## Features

- 🚀 Quick project initialization with modern best practices
- 📦 Project templates with standardized structure
- ⚙️ Interactive project configuration
- 🔧 Pre-configured development tools (ruff, pytest, nox)
- 📚 Documentation setup with MkDocs Material
- 🔄 GitHub Actions workflows included

## Installation

```bash
# Using uvx (recommended)
uvx install repo-scaffold

# Using pip
pip install repo-scaffold

# Using poetry
poetry add repo-scaffold
```

## Quick Start

```bash
# List available templates
repo-scaffold list

# Create a new project
repo-scaffold create python

# Create a project in a specific directory
repo-scaffold create python -o ./my-projects
```

## Available Templates

Currently supported project templates:

- **Python Project Template**
  - Modern Python project structure
  - Testing setup with pytest and nox
  - Documentation with MkDocs Material
  - Code quality with ruff
  - GitHub Actions CI/CD workflows
  - Dependency management with your choice of tool
  - Automated version management
  - MIT License template

## Development Setup

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/ShawnDen-coder/repo-scaffold.git
cd repo-scaffold

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,docs]"
```
