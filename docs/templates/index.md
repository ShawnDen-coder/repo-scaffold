# Templates

`repo-scaffold` ships a small set of [Cookiecutter](https://www.cookiecutter.io/) templates that share the same baseline tooling. Run `repo-scaffold list` to see what's available, and `repo-scaffold create <name>` to scaffold one.

| Template | Layout | Use it for |
| --- | --- | --- |
| [`python`](python.md) | Single-package | One library/CLI/service in one repository. |
| [`uv-workspace`](uv-workspace.md) | uv workspace monorepo | Multiple related packages versioned together with per-package release tags. |

## Shared infrastructure

Both templates start from the same baseline so that switching between them is mostly a layout decision, not a tooling decision.

### Package manager — [uv](https://docs.astral.sh/uv/)

- Dependency resolution and locking via `pyproject.toml` + `uv.lock`.
- The `python` template ships dev/docs deps under `[project.optional-dependencies]`; the `uv-workspace` template uses `[dependency-groups]` (workspace-friendly).
- Dev tools that are always invoked through `uvx` (currently `ruff` and `pre-commit`) are intentionally **not** listed as project deps — they are run from isolated tool environments and do not need to be installed into the project venv.

### Task runner — [just](https://github.com/casey/just)

Every recipe is exposed as `just <recipe>`:

```bash
# First-time bootstrap from a clean machine. This recipe also installs
# `rust-just` as a uv tool, so subsequent calls can use plain `just`.
uvx --from rust-just just init

# After init, run any recipe directly:
just lint
just test
just docs
```

`just` (no argument) prints the recipe list. The shell is set to `bash -euc` so any failed command in a multi-line recipe aborts immediately.

### Lint & format — [Ruff](https://docs.astral.sh/ruff/)

- `just lint` runs `ruff check --fix`, `ruff format`, then a final `ruff check` as a verification pass.
- `just lint-watch` re-runs lint on file changes.
- `just lint-add-noqa` adds `# noqa` for current violations, then re-runs `pre-commit` and `lint` (useful when adopting Ruff into an existing codebase).
- Ruff rules live in `.ruff.toml`.

### Tests — [pytest](https://docs.pytest.org/) with coverage

- `just test` runs the suite at the dev Python version with coverage reports (`coverage.xml` + terminal).
- `just test-all` iterates the configured `min..max` Python range and runs the suite for each.
- `just test-version <ver>` runs the suite for a specific version.

### Pre-commit hooks — [pre-commit](https://pre-commit.com/)

`init` installs the git hooks. The default hook set is:

| Hook | Purpose |
| --- | --- |
| `uv-lock` | Keep `uv.lock` in sync with `pyproject.toml`. |
| `yamlfmt` | Format YAML files. |
| `check-github-workflows` | Validate workflow files against the GitHub Actions schema. |
| `actionlint` | Lint workflow shell + expression syntax. |

Run them all manually with `just lint-pre-commit`.

### Versioning — [Cocogitto](https://docs.cocogitto.io/)

Versions are driven by [Conventional Commits](https://www.conventionalcommits.org/). A push to `master` / `main` runs the `version-bump.yaml` workflow, which calls [`cocogitto-action`](https://docs.cocogitto.io/ci_cd/action.html) with `release: true` to:

1. Compute the next version from commits since the last tag.
2. Run `pre_bump_hooks` — the templates use `uv version {{version}}` + `uv lock --no-upgrade` to keep `pyproject.toml` and the lockfile in sync with the new tag.
3. Update `CHANGELOG.md`.
4. Create a bump commit and a SemVer tag.

The tag then triggers `package-release.yaml` to build & publish.

`cog.toml` configures hooks, branch whitelist (`master`, `main`), and the changelog template.

### CI/CD — GitHub Actions

Both templates ship the same five-workflow pipeline (the `python` template adds a sixth for container builds when Podman is enabled). See the [CI/CD pipeline](ci-cd.md) page for the full job DAG, what each workflow does, and the secrets / variables it needs.

### Docs — [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)

- `just docs` serves docs locally; `just docs-build` builds the static site; `just deploy-gh-pages` publishes to GitHub Pages.
- API reference is auto-generated from docstrings via [`mkdocstrings`](https://mkdocstrings.github.io/) + `mkdocs-gen-files` + `mkdocs-literate-nav`.
- `docs/gen_home_pages.py` mirrors `README.md` into the docs index.

### Other shared files

- `.gitignore` — covers Python build artifacts, coverage output, MkDocs `site/`, and `.env`.
- `.yamlfmt.yaml` — yamlfmt formatting rules.
- `.vscode/settings.json` — recommended editor defaults.

## Common Cookiecutter prompts

These prompts are shared across the templates (the prompt strings are localized to Chinese in the `__prompts__` block of each template's `cookiecutter.json`):

| Variable | Description |
| --- | --- |
| `repo_name` | Repository name. Drives the directory name and `project_slug`. |
| `full_name` / `email` | Author identity for `pyproject.toml`. |
| `github_username` | Owner used in changelog links and badges. |
| `description` | Short project description. |
| `min_python_version` / `max_python_version` | Inclusive Python version range; used by `requires-python` and `test-all`. |
| `use_github_actions` | Toggle the entire `.github/`, `mkdocs.yml`, and `docs/` set. |
| `pypi_server_url` | Optional private PyPI URL. Can be overridden at publish time via the `PYPI_SERVER_URL` environment variable. |
| `install_after_generate` | Run `uv sync` automatically inside the post-generation hook. |
