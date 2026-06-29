set dotenv-load := true
set shell := ["bash", "-uc"]

package_name := "repo_scaffold"
python_min_version := "3.12"
python_max_version := "3.12"
python_dev_version := python_min_version
pypi_server_url := "https://pypiserver.shawndeng.cc"

init:
    uv sync
    uvx pre-commit install

lint:
    uvx ruff check --fix .
    uvx ruff format .
    uvx ruff check .

lint-add-noqa:
    uvx ruff check --add-noqa .
    just lint-pre-commit
    just lint

lint-pre-commit:
    uvx pre-commit run --all-files

lint-watch:
    uvx ruff check --watch .

test:
    just test-version {{python_dev_version}}

test-all:
    for version in $(python -c "min_ver = '{{python_min_version}}'.split('.'); max_ver = '{{python_max_version}}'.split('.'); [print(f'{min_ver[0]}.{minor}') for minor in range(int(min_ver[1]), int(max_ver[1]) + 1)]"); do just test-version "$version"; done

test-version version:
    echo "Testing with Python {{version}}..."
    uv run --extra dev --python {{version}} pytest --cov={{package_name}} --cov-report=xml --cov-report=term-missing -v tests/

test-watch:
    uv run --extra dev ptw --runner "pytest -vx"

docs:
    uv run --extra docs mkdocs serve

docs-build:
    uv run --extra docs mkdocs build

deploy-gh-pages:
    uv run --extra docs mkdocs gh-deploy --force

build:
    uv build

publish-pypi:
    uv publish

publish-pypi-server:
    UV_PUBLISH_USERNAME="${PYPI_SERVER_USERNAME}" UV_PUBLISH_PASSWORD="${PYPI_SERVER_PASSWORD}" UV_PUBLISH_URL="${PYPI_SERVER_URL:-{{pypi_server_url}}}" uv publish dist/*

publish-all:
    just publish-pypi
    just publish-pypi-server

deploy-pypi:
    just build
    just publish-pypi

deploy-pypi-server:
    just build
    just publish-pypi-server

deploy-all:
    just build
    just publish-all

export-deps:
    uv pip compile pyproject.toml --no-deps --output-file requirements.txt
