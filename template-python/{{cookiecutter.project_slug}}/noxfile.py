"""Nox automation file for github-action-test project.

This module contains nox sessions for automating development tasks including:
- Code linting and formatting
- Unit testing with coverage reporting
- Package building
- Executable creation

Typical usage example:
    nox -s lint  # Run linting
    nox -s test  # Run tests
    nox -s build # Build package
    nox -s build_exe # Build package with standalone executable
"""
import nox


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run code quality checks using ruff.

    Performs linting and formatting checks on the codebase using ruff.
    Fixes auto-fixable issues and shows formatting differences.

    Args:
        session: Nox session object for running commands
    """
    session.install("poetry")
    session.install("ruff")
    session.run("poetry", "install", "--only", "dev")
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

    Executes pytest with coverage reporting for the github_action_test package.
    Generates both terminal and XML coverage reports.

    Args:
        session: Nox session object for running commands
    """
    session.install("poetry")
    session.run("poetry", "install")
    session.run(
        "pytest",
        "--cov={{cookiecutter.project_slug}}",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-v",
        "tests"
    )


@nox.session(reuse_venv=True)
def build(session: nox.Session) -> None:
    """Build the Python package.

    Creates a distributable package using poetry build command
    with verbose output and excluding dev dependencies.

    Args:
        session: Nox session object for running commands
    """
    session.install("poetry")
    session.run("poetry", "install", "--without", "dev")
    session.run("poetry", "build", "-vvv")


@nox.session(reuse_venv=True)
def build_exe(session: nox.Session) -> None:
    """Build the Python package with standalone executable.

    Creates an executable using poetry-pyinstaller-plugin.
    Installs required plugin and builds without dev dependencies.

    Args:
        session: Nox session object for running commands
    """
    session.install("poetry")
    session.install("poetry", "self", "add", "poetry-pyinstaller-plugin")
    session.run("poetry", "install", "--without", "dev")
    session.run("poetry", "build", "-vvv")
