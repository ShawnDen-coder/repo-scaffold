# repo-scaffold

[![PyPI version](https://badge.fury.io/py/repo-scaffold.svg)](https://badge.fury.io/py/repo-scaffold)
[![Python Version](https://img.shields.io/pypi/pyversions/repo-scaffold.svg)](https://pypi.org/project/repo-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/your-username/repo-scaffold/workflows/Tests/badge.svg)](https://github.com/your-username/repo-scaffold/actions)

A modern, intelligent project scaffolding tool that generates production-ready Python projects in seconds.

## ✨ Features

- 🚀 **Zero-config setup** - Create projects instantly without answering questions
- 📦 **Component-based architecture** - Mix and match features as needed
- 🎯 **Production-ready templates** - Includes CI/CD, testing, documentation, and more
- 🔧 **Modern Python tooling** - Built with uv, Ruff, pytest, and Task automation
- 🐳 **Container support** - Optional Podman/Docker integration
- 📚 **Documentation ready** - MkDocs setup with auto-generated API docs
- 🔄 **GitHub Actions** - Complete CI/CD workflows included
- 📦 **PyPI publishing** - Automated package publishing with trusted publishing
- 🎨 **Code quality** - Pre-commit hooks, linting, and formatting configured

## 🚀 Quick Start

### Installation

```bash
# Install globally with uvx (recommended)
uvx install repo-scaffold

# Or install with pip
pip install repo-scaffold
```

### Create Your First Project

```bash
# Create a Python library project (uses smart defaults)
repo-scaffold create

# That's it! Your project is ready with:
# ✅ Modern Python setup (pyproject.toml, uv)
# ✅ Testing framework (pytest with coverage)
# ✅ Code quality tools (ruff, pre-commit)
# ✅ GitHub Actions CI/CD
# ✅ Documentation (MkDocs)
# ✅ Task automation (Taskfile)
```

### What You Get

After running `repo-scaffold create`, you'll have a complete project structure:

```
my-python-library/
├── .github/workflows/     # CI/CD pipelines
├── docs/                  # MkDocs documentation
├── tests/                 # Test suite
├── my_python_library/     # Your package
├── pyproject.toml         # Modern Python configuration
├── Taskfile.yml          # Task automation
├── README.md             # Project documentation
└── .pre-commit-config.yaml # Code quality hooks
```

### Start Developing

```bash
cd my-python-library
task init    # Initialize development environment
task test    # Run tests
task lint    # Check code quality
task docs    # Serve documentation locally
```

## 📋 Available Commands

```bash
# Project creation
repo-scaffold create                    # Create with defaults (recommended)
repo-scaffold create --input           # Interactive mode with prompts
repo-scaffold create -t python-library # Specify template explicitly
repo-scaffold create -o ./my-project   # Specify output directory

# Information commands
repo-scaffold list                      # List available templates
repo-scaffold components               # List available components
repo-scaffold show python-library      # Show template details
repo-scaffold --help                   # Show help
```

## 🎯 Usage Examples

### Basic Usage (Recommended)

```bash
# Create a project with smart defaults - no questions asked!
repo-scaffold create
```

This creates a full-featured Python library with:
- **Python Core**: Modern pyproject.toml setup with uv
- **Task Automation**: Taskfile.yml for common development tasks
- **GitHub Actions**: Complete CI/CD with testing, linting, and publishing
- **Documentation**: MkDocs with auto-generated API docs
- **Code Quality**: Pre-commit hooks, Ruff linting and formatting
- **Container Support**: Podman/Docker setup for containerized development
- **PyPI Publishing**: Automated package publishing workflows

### Interactive Mode

```bash
# If you want to customize the setup
repo-scaffold create --input
```

This will prompt you to:
- Choose which components to include
- Configure project details
- Set up custom options

### Advanced Usage

```bash
# Create in specific directory
repo-scaffold create -o ~/projects/my-new-lib

# Use different template (when more templates are available)
repo-scaffold create -t python-library

# Combine options
repo-scaffold create -t python-library -o ~/projects --input
```

## 🧩 Available Components

The `python-library` template includes these components:

| Component | Description | Included by Default |
|-----------|-------------|-------------------|
| **Python Core** | Modern Python setup with pyproject.toml and uv | ✅ |
| **Task Automation** | Taskfile.yml for development workflows | ✅ |
| **GitHub Actions** | CI/CD pipelines for testing and deployment | ✅ |
| **MkDocs** | Documentation site with auto-generated API docs | ✅ |
| **Pre-commit** | Code quality hooks and automated formatting | ✅ |
| **Podman** | Container support for development and deployment | ✅ |
| **PyPI Publishing** | Automated package publishing to PyPI | ✅ |

## 🛠️ Development Workflow

After creating your project, here's the typical development workflow:

```bash
# 1. Initialize the development environment
task init

# 2. Make your changes
# Edit code in your_package/

# 3. Run tests
task test

# 4. Check code quality
task lint

# 5. View documentation
task docs

# 6. Build package
task build

# 7. Commit changes (pre-commit hooks will run automatically)
git add .
git commit -m "feat: add new feature"

# 8. Push to trigger CI/CD
git push
```

## 🔧 Configuration

### Default Values

The tool uses sensible defaults for all configuration:

- **Project Name**: "My Python Library"
- **Package Name**: Auto-generated from project name
- **Author**: "Your Name" (customize in interactive mode)
- **License**: MIT
- **Python Version**: 3.10-3.12 support, 3.10 for development
- **All Components**: Enabled by default

### Customization

Use `--input` flag for interactive customization:

```bash
repo-scaffold create --input
```

This allows you to:
- Set custom project name and description
- Choose your preferred license
- Select which components to include
- Configure component-specific options

## 📚 Documentation

- [Getting Started](docs/getting-started/)
- [Installation](docs/getting-started/installation.md)
- [Quick Start](docs/getting-started/quick-start.md)
- [Configuration](docs/getting-started/configuration.md)
- [Components](docs/components/)
- [Templates](docs/templates/)

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with modern Python tooling:
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [Ruff](https://github.com/astral-sh/ruff) - Lightning-fast Python linter
- [pytest](https://pytest.org/) - Testing framework
- [MkDocs](https://www.mkdocs.org/) - Documentation generator
- [Task](https://taskfile.dev/) - Task automation
- [Cookiecutter](https://github.com/cookiecutter/cookiecutter) - Template engine
