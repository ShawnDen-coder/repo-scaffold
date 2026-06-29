# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common commands

- Bootstrap and run recipes without prior install: `uvx --from rust-just just <recipe>`.
- Install/sync the development environment and hooks: `uvx --from rust-just just init` (runs `uv sync` and installs pre-commit hooks).
- Run the full lint/format cycle: `uvx --from rust-just just lint` (Ruff check with fixes, Ruff format, then Ruff check again).
- Run all pre-commit hooks: `uvx --from rust-just just lint-pre-commit`.
- Run the default test suite with coverage: `uvx --from rust-just just test`.
- Run tests across the configured Python version range: `uvx --from rust-just just test-all`.
- Run a single test file or test node: `uv run --extra dev pytest -v tests/test_import.py` or `uv run --extra dev pytest -v tests/test_import.py::test_imports`.
- Build distributions: `uvx --from rust-just just build` (`uv build`).
- Serve docs locally: `uvx --from rust-just just docs`; build docs: `uvx --from rust-just just docs-build`.
- Exercise the CLI locally: `uv run repo-scaffold list` and `uv run repo-scaffold create python --no-input -o <output-dir>`.

## Project overview

This is a Python 3.12 package that exposes the `repo-scaffold` console command. The package is a thin Click CLI around Cookiecutter templates:

- `repo_scaffold/cli.py` contains the CLI entry point, template discovery, and project generation flow.
- `repo_scaffold/templates/cookiecutter.json` is the registry of available templates. Add new templates there so `repo-scaffold list` and `repo-scaffold create <template>` can discover them.
- Template source lives under `repo_scaffold/templates/template-python/`. Files below `{{cookiecutter.project_slug}}/` are copied into generated projects and may contain Jinja expressions.
- `repo_scaffold/templates/template-python/cookiecutter.json` defines the prompts/defaults for generated Python projects.
- `repo_scaffold/templates/template-python/hooks/post_gen_project.py` runs after generation. It removes optional CLI/container/GitHub Actions files based on prompt choices, then runs `uv sync` inside the generated project.

## Template-specific notes

- The top-level project and the generated templates use `justfile` for developer workflows; keep shared recipe behavior in sync only when the same behavior is intended in both places.
- The root `.ruff.toml` excludes `repo_scaffold/templates/**/*`, so generated-template Python and Jinja files are not linted by the root Ruff configuration.
- Be careful editing files inside `repo_scaffold/templates/*/{{cookiecutter.project_slug}}/`: preserve Cookiecutter/Jinja delimiters and raw blocks, especially in GitHub Actions YAML and any literal `${{ ... }}` or `{{ ... }}` syntax.
- The generated Python template can optionally include a Click CLI, Podman compose files, docs, and GitHub Actions; optional files are removed by `post_gen_project.py`, not by conditional directory omission.

## Tests and validation

- Current root tests are import smoke tests in `tests/test_import.py`, which import all modules under `repo_scaffold`.
- For CLI/template changes, supplement `uvx --from rust-just just test` with a manual generation check such as `uv run repo-scaffold create python --no-input -o <temp-dir>` because the existing test suite does not validate Cookiecutter rendering or generated project behavior.
- CI runs `uvx --from rust-just just init`, `uvx --from rust-just just lint`, and `uvx --from rust-just just test-all` on pushes and pull requests.

## Release and docs

- Versioning is managed by Commitizen (`.cz.yaml`) with `version_provider: uv`; tags use plain semver like `0.13.5`.
- The release workflow publishes tagged builds to the private PyPI server by default and conditionally to public PyPI when `PUBLISH_TO_PUBLIC_PYPI` is true.
- MkDocs uses generated pages from `docs/gen_ref_pages.py` and `docs/gen_home_pages.py`; the docs source reflects the package API and README.
