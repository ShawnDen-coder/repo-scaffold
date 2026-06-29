set dotenv-load := true
set shell := ["bash", "-euc"]

package_name := "repo_scaffold"
python_min_version := "3.12"
python_max_version := "3.12"
python_dev_version := python_min_version
pypi_server_url := "https://pypiserver.shawndeng.cc"

# Show available recipes
default:
    @just --list

# Sync deps and install pre-commit hooks
init:
    uv sync --all-extras
    uvx pre-commit install

# Run ruff fix + format + check
lint:
    uvx ruff check --fix .
    uvx ruff format .
    uvx ruff check .

# Add `# noqa` for current violations, then re-run lint
lint-add-noqa: && lint-pre-commit lint
    uvx ruff check --add-noqa .

# Run all pre-commit hooks against the whole tree
lint-pre-commit:
    uvx pre-commit run --all-files

# Watch and re-run ruff on changes
lint-watch:
    uvx ruff check --watch .

# Run tests with the dev Python version
test:
    @just test-version {{python_dev_version}}

# Run tests across the configured Python version range
test-all:
    for version in $(python -c "min_ver = '{{python_min_version}}'.split('.'); max_ver = '{{python_max_version}}'.split('.'); [print(f'{min_ver[0]}.{minor}') for minor in range(int(min_ver[1]), int(max_ver[1]) + 1)]"); do just test-version "$version"; done

# Run tests for a specific Python version
test-version version:
    echo "Testing with Python {{version}}..."
    uv run --extra dev --python {{version}} pytest --cov={{package_name}} --cov-report=xml --cov-report=term-missing -v tests/

# Serve docs locally
docs:
    uv run --extra docs mkdocs serve

# Build static docs
docs-build:
    uv run --extra docs mkdocs build

# Deploy docs to GitHub Pages
deploy-gh-pages:
    uv run --extra docs mkdocs gh-deploy --force

# Build sdist + wheel
build:
    uv build

# Publish to public PyPI
publish-pypi:
    uv publish

# Publish to the private PyPI server
publish-pypi-server:
    UV_PUBLISH_USERNAME="${PYPI_SERVER_USERNAME}" UV_PUBLISH_PASSWORD="${PYPI_SERVER_PASSWORD}" UV_PUBLISH_URL="${PYPI_SERVER_URL:-{{pypi_server_url}}}" uv publish dist/*

# Publish to both indexes
publish-all: publish-pypi publish-pypi-server

# Build then publish to public PyPI
deploy-pypi: build publish-pypi

# Build then publish to the private server
deploy-pypi-server: build publish-pypi-server

# Build then publish to both indexes
deploy-all: build publish-all

# Export pinned deps to requirements.txt
export-deps:
    uv export --no-hashes --output-file requirements.txt
