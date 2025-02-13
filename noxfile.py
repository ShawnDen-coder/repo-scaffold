"""Nox automation file for github-action-test project.

This module contains nox sessions for automating development tasks including:
- Code linting and formatting
- Unit testing with coverage reporting
- Package building
- Project cleaning

Typical usage example:
    nox -s lint   # Run linting
    nox -s test   # Run tests
    nox -s build  # Build package
    nox -s clean  # Clean project
"""
import nox
import shutil
from pathlib import Path


def install_with_uv(session: nox.Session, editable: bool = False) -> None:
    """Helper function to install packages using uv.
    
    Args:
        session: Nox session object for running commands
        editable: Whether to install in editable mode
    """
    session.install("uv")
    if editable:
        session.run("uv", "pip", "install", "-e", ".[dev]")
    else:
        session.run("uv", "pip", "install", ".")


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run code quality checks using ruff.

    Performs linting and formatting checks on the codebase using ruff.
    Fixes auto-fixable issues and shows formatting differences.

    Args:
        session: Nox session object for running commands
    """
    # Install dependencies
    session.install("ruff")
    install_with_uv(session, editable=True)
    
    # Run linting checks
    session.run(
        "ruff",
        "check",
        ".",
        "--fix",
        "--verbose"
    )
    session.run(
        "ruff",
        "format",
        "--verbose",
        "--diff"
    )


@nox.session(reuse_venv=True)
def test(session: nox.Session) -> None:
    """Run the test suite with coverage reporting.

    Executes pytest with coverage reporting for the repo_scaffold package.
    Generates both terminal and XML coverage reports.

    Args:
        session: Nox session object for running commands
    """
    # Install dependencies
    install_with_uv(session, editable=True)
    session.install("pytest", "pytest-cov", "pytest-mock")
    
    # Run tests
    session.run(
        "pytest",
        "--cov=repo_scaffold",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-v",
        "tests"
    )


@nox.session(reuse_venv=True)
def build(session: nox.Session) -> None:
    """Build the Python package.

    Creates a distributable package using uv build command.

    Args:
        session: Nox session object for running commands
    """
    session.install("uv")
    session.run("uv", "build", "--wheel", "--sdist")


@nox.session(reuse_venv=True)
def clean(session: nox.Session) -> None:  # pylint: disable=unused-argument
    """Clean the project directory.

    Removes build artifacts, cache directories, and other temporary files:
    - build/: Build artifacts
    - dist/: Distribution packages
    - .nox/: Nox virtual environments
    - .pytest_cache/: Pytest cache
    - .ruff_cache/: Ruff cache
    - .coverage: Coverage data
    - coverage.xml: Coverage report
    - **/*.pyc: Python bytecode
    - **/__pycache__/: Python cache directories
    - **/*.egg-info: Package metadata

    Args:
        session: Nox session object (unused)
    """
    root = Path(".")
    patterns = [
        "build",
        "dist",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".coverage",
        "coverage.xml",
        "**/*.pyc",
        "**/__pycache__",
        "**/*.egg-info",
    ]
    
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                path.unlink()
                print(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
