set dotenv-load := true
set shell := ["bash", "-euc"]
set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

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
    uv tool install rust-just
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
    uv run python -c "import subprocess; mn=int('{{python_min_version}}'.split('.')[1]); mx=int('{{python_max_version}}'.split('.')[1]); [subprocess.check_call(['uv','run','--extra','dev','--python',f'3.{m}','pytest','--cov={{package_name}}','--cov-report=xml','--cov-report=term-missing','-v','tests/']) for m in range(mn, mx + 1)]"

# Run tests for a specific Python version
test-version version:
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
    uv publish --username {{env_var('PYPI_SERVER_USERNAME')}} --password {{env_var('PYPI_SERVER_PASSWORD')}} --publish-url {{env_var_or_default('PYPI_SERVER_URL', pypi_server_url)}}

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
