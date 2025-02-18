"""Nox automation file for repo-scaffold project.

This module contains nox sessions for automating development tasks including:
- Code linting and formatting
- Unit testing with coverage reporting
- Package building
- Project cleaning
- Baseline creation for linting rules
- Documentation building

Typical usage example:
    nox -s lint   # Run linting
    nox -s test   # Run tests with current Python version
    nox -s test-all  # Run tests with all supported Python versions
    nox -s build  # Build package
    nox -s clean  # Clean project
    nox -s baseline  # Create a new baseline for linting rules
    nox -s docs    # Build documentation
    nox -s docs-serve  # Serve documentation locally
"""
import nox
import shutil
from pathlib import Path

# 支持的 Python 版本范围
MIN_PYTHON = "3.12"
MAX_PYTHON = "3.12"

# 生成版本列表
PYTHON_VERSIONS = [MIN_PYTHON]


def install_with_uv(session: nox.Session, extras: list[str] | None = None) -> None:
    """Helper function to install packages using uv.
    
    Args:
        session: Nox session object for running commands
        extras: Optional list of extra dependency groups to install (e.g. ["dev", "docs"])
    """
    session.install("uv")
    if extras:
        session.run("uv", "sync", *(f"--extra={extra}" for extra in extras))
    else:
        session.run("uv", "sync")


@nox.session(python=PYTHON_VERSIONS[-1], reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run code quality checks using ruff.

    Performs linting and formatting checks on the codebase using ruff.
    Reports any issues found without auto-fixing.

    Args:
        session: Nox session object for running commands
    """
    # Install dependencies
    install_with_uv(session, extras=["dev"])

    # Run ruff checks
    session.run("uv", "run", "ruff", "check", ".")
    session.run("uv", "run", "ruff", "format", "--check", ".")


@nox.session(python=PYTHON_VERSIONS[-1], reuse_venv=True)
def test(session: nox.Session) -> None:
    """Run the test suite with coverage reporting.

    Executes pytest with coverage reporting for the repo_scaffold package.
    Generates both terminal and XML coverage reports.

    Args:
        session: Nox session object for running commands
    """
    # Install dependencies
    install_with_uv(session, extras=["dev"])

    # Run pytest with coverage
    session.run(
        "uv",
        "run",
        "pytest",
        "--cov=repo_scaffold",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-v",
        "tests"
    )


@nox.session(python=PYTHON_VERSIONS)
def test_all(session: nox.Session) -> None:
    """Run tests on all supported Python versions.

    This session runs the test suite against all supported Python versions.
    It's useful for ensuring compatibility across different Python versions.
    Also generates coverage report when running with the latest Python version.

    Args:
        session: Nox session object for running commands
    """
    # Install dependencies
    session.install("uv")
    install_with_uv(session, extras=["dev"])

    # 运行测试
    session.run(
        "uv",
        "run",
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

    Creates a distributable package using build command.

    Args:
        session: Nox session object for running commands
    """
    install_with_uv(session, extras=["dev"])
    session.run("uv","build")


@nox.session(reuse_venv=True)
def clean(session: nox.Session) -> None:
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
    """
    # 要清理的目录和文件
    paths_to_clean = [
        # 构建和分发
        "build",
        "dist",
        # 虚拟环境
        ".nox",
        # 缓存
        ".pytest_cache",
        ".ruff_cache",
        # 覆盖率报告
        ".coverage",
        "coverage.xml",
        "site"
    ]

    # 清理指定的目录和文件
    for path in paths_to_clean:
        path = Path(path)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    # 清理 Python 缓存文件
    for pattern in ["**/*.pyc", "**/__pycache__"]:
        for path in Path().glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


@nox.session(reuse_venv=True)
def baseline(session: nox.Session) -> None:
    """Create a new baseline for linting rules.

    This command will:
    1. Add # noqa comments to all existing violations
    2. Update the pyproject.toml with new extend-ignore rules
    3. Show a summary of changes made

    Args:
        session: Nox session object for running commands
    """
    # Install dependencies
    install_with_uv(session, extras=["dev"])

    # 运行 ruff 并自动修复所有问题
    session.run("uv", "run", "ruff", "check", ".", "--add-noqa")
    session.run("uv", "run", "ruff", "format", ".")


@nox.session(reuse_venv=True)
def docs(session: nox.Session) -> None:
    """Build the documentation.

    Uses MkDocs to build the documentation site.

    Args:
        session: Nox session object for running commands
    """
    session.install("uv")
    install_with_uv(session, extras=["docs"])
    session.run("uv", "run", "mkdocs", "build")


@nox.session(reuse_venv=True)
def docs_serve(session: nox.Session) -> None:
    """Serve the documentation locally.

    Starts a local server to preview the documentation site.

    Args:
        session: Nox session object for running commands
    """
    session.install("uv")
    install_with_uv(session, extras=["docs"])
    session.run("uv", "run", "mkdocs", "serve")
