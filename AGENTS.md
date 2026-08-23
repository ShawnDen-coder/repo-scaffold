# Repository Guidelines

## Project Structure & Module Organization

`repo_scaffold/` contains the Python 3.12 Click CLI and its feature packages: `github_init/` for GitHub bootstrapping and `add_package/` for workspace package management. Cookiecutter sources live in `repo_scaffold/templates/`; update `cookiecutter.json` when adding a discoverable template. Tests are in `tests/`, documentation sources and generators are in `docs/`, and CI workflows are in `.github/workflows/`. Keep root workflows and generated-template workflows distinct unless their release models match.

## Build, Test, and Development Commands

Use `uv` and the `justfile` for repeatable workflows:

- `uvx --from rust-just just init` — sync all extras and install pre-commit hooks.
- `just lint` — apply Ruff fixes/formatting, then check the tree.
- `just lint-pre-commit` — run all repository pre-commit hooks.
- `just test` — run pytest with coverage for Python 3.12.
- `just test-all` — run tests across the configured Python versions.
- `just build` — build the source distribution and wheel.
- `just docs` / `just docs-build` — serve or build MkDocs documentation.

For focused work, use `uv run --extra dev pytest -v tests/test_templates.py` or a specific test node.

## Coding Style & Naming Conventions

Follow Ruff configuration in `.ruff.toml`, use four-space Python indentation, and prefer clear `snake_case` functions/modules with `PascalCase` classes. Keep generated-template files consistent with their ecosystem: Ruff for Python, Prettier/Biome for JavaScript/TypeScript, and Cargo formatting for Rust. Preserve Cookiecutter variables and Jinja raw blocks; literal `{{ ... }}` or `${{ ... }}` in templates may require escaping.

## Testing Guidelines

Tests use pytest, `pytest-mock`, and `pytest-cov`; coverage is reported by `just test` and template files are excluded. Name tests `test_*.py` and functions `test_*`. For CLI or template changes, add or update unit tests and manually render a representative template, for example `uv run repo-scaffold create python --no-input --no-install -o <temp-dir>`.

## Commit & Pull Request Guidelines

Use Conventional Commits, such as `feat(cli): add template command`, `fix: handle missing config`, or `chore(version): 0.25.0`. PRs should explain behavior changes, include relevant tests and documentation updates, and note manual template-generation checks. Keep generated files and secrets out of commits; CI must pass lint, pre-commit, and tests.

## Security & Configuration Tips

Keep GitHub and package-index credentials in environment variables or local `.env` files excluded from Git. Exercise `gh-init` with `--no-push` during development and never commit tokens, generated secrets, or private registry credentials.
