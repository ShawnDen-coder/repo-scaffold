# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common commands

- Bootstrap and run recipes without prior install: `uvx --from rust-just just <recipe>`.
- Install/sync the development environment and hooks: `uvx --from rust-just just init` (installs `rust-just` as a uv tool, runs `uv sync --all-extras`, installs pre-commit hooks). After `init`, recipes can be invoked as `just <recipe>`.
- Run the full lint/format cycle: `just lint` (Ruff check with fixes, Ruff format, then Ruff check again).
- Run all pre-commit hooks: `just lint-pre-commit`.
- Run the default test suite with coverage: `just test`.
- Run tests across the configured Python version range: `just test-all`.
- Run a single test file or test node: `uv run --extra dev pytest -v tests/test_templates.py` or `uv run --extra dev pytest -v tests/test_github_init.py::test_build_config_pulls_defaults_from_pyproject`.
- Build distributions: `just build` (`uv build`).
- Serve docs locally: `just docs`; build docs: `just docs-build`.
- Exercise the CLI locally: `uv run repo-scaffold list`, `uv run repo-scaffold create python --no-input --no-install -o <temp-dir>`, and `uv run repo-scaffold create uv-workspace --no-input --no-install -o <temp-dir>`.
- Exercise GitHub bootstrap without pushing: `GITHUB_TOKEN=<token> uv run repo-scaffold gh-init <generated-project> --no-input --no-push`.

## Project overview

This is a Python 3.12 package exposing the `repo-scaffold` console command. It is a Click CLI around bundled Cookiecutter templates plus a GitHub bootstrap helper for generated projects.

- `repo_scaffold/cli.py` is the CLI entry point. It loads the template registry, implements `repo-scaffold list`, delegates `repo-scaffold create <template>` to Cookiecutter, and wires the `gh-init` command to the GitHub bootstrap layer.
- `repo_scaffold/github_init.py` contains the non-Click logic for `gh-init`: resolving defaults from `pyproject.toml`, `.env`, environment variables, and prompts; wrapping PyGithub; setting Actions secrets/variables; optionally initializing/committing/pushing a git repository; and (after a successful push, unless `--no-pages`) creating the `gh-pages` branch and configuring the repo's GitHub Pages source to it via the REST API (`GhInitClient.ensure_branch`/`enable_pages`, since PyGithub 2.x exposes no Pages helper).
- `repo_scaffold/templates/cookiecutter.json` is the registry of discoverable templates. Add new templates there so both `repo-scaffold list` and `repo-scaffold create <template>` can find them.
- Template source lives under `repo_scaffold/templates/template-python/` and `repo_scaffold/templates/template-uv-workspace/`. Files below each `{{cookiecutter.project_slug}}/` are copied into generated projects and may contain Jinja expressions.
- Each template has its own `cookiecutter.json` defining prompts/defaults and a `hooks/post_gen_project.py` that validates rendered values, removes optional files, initializes a git repo on branch `master` (unless `create --no-git` sets `init_git=no`), and optionally runs dependency installation (`uv sync` for the single-package template, `uv sync --all-groups` for the workspace template).
- The single-package template can optionally include a Click CLI, Podman compose files, GitHub Actions, and MkDocs docs. The uv-workspace template generates a workspace root plus an initial package under `packages/` and can optionally include GitHub Actions/docs.

## Template-specific notes

- The top-level project and generated templates all use `justfile` for developer workflows; keep shared recipe behavior in sync only when the same behavior is intended in both places.
- The root `.ruff.toml` and coverage config exclude `repo_scaffold/templates/**/*`, so generated-template Python/Jinja files are not linted or measured by the root Ruff/coverage settings.
- Be careful editing files inside `repo_scaffold/templates/*/{{cookiecutter.project_slug}}/`: preserve Cookiecutter/Jinja delimiters and raw blocks, especially in GitHub Actions YAML and any literal `${{ ... }}` or `{{ ... }}` syntax.
- Optional template files are removed by `post_gen_project.py` after rendering; do not rely on conditional directory omission unless you also update the hook and tests.

## Tests and validation

- `tests/test_import.py` imports all non-template modules under `repo_scaffold`.
- `tests/test_templates.py` validates the template registry, CLI template resolution, Cookiecutter rendering for both templates, static rendered-project checks, and post-generation hook behavior.
- `tests/test_github_init.py` unit-tests dotenv parsing, config resolution, PyGithub wrapper behavior, CLI wiring, and the git push helper for `gh-init`.
- For CLI/template changes, supplement `just test` with a manual generation check such as `uv run repo-scaffold create python --no-input --no-install -o <temp-dir>` because most tests validate static rendering, not full generated-project workflows after dependency installation.
- CI runs `uvx --from rust-just just init`, `uvx --from rust-just just lint`, `uvx --from rust-just just lint-pre-commit`, and `uvx --from rust-just just test-version 3.12` on pushes and pull requests.

## Release and docs

- Versioning is managed by [Cocogitto](https://docs.cocogitto.io/) (`cog.toml`); `pre_bump_hooks` run `uv version {{version}}` and `uv lock --no-upgrade`, and `post_bump_hooks` push commits/tags. Tags use plain semver like `0.15.1`.
- The version bump workflow (`.github/workflows/version-bump.yaml`) uses `cocogitto/cocogitto-action@v3` with `release: true` to compute the next version from conventional commits, write `CHANGELOG.md`, commit, and tag. The release workflow then publishes tagged builds.
- The release workflow publishes tagged builds to the private PyPI server by default and conditionally to public PyPI when `PUBLISH_TO_PUBLIC_PYPI` is true.
- MkDocs uses generated pages from `docs/gen_ref_pages.py` and `docs/gen_home_pages.py`; API reference generation excludes templates and the home page is generated from `README.md`.
