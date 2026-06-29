# `uv-workspace` template

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) monorepo. Best when several packages share tooling, dev deps, and a release cycle but each ships as its own distribution.

```bash
repo-scaffold create uv-workspace
# or fully unattended:
repo-scaffold create uv-workspace --no-input -o ./out
```

For everything shared with the [`python`](python.md) template, see the [shared infrastructure](index.md#shared-infrastructure) section.

## Layout

```
{{project_slug}}/
├── packages/
│   └── {{package_slug}}/
│       ├── pyproject.toml             # one [project] per package, hatchling build
│       ├── src/{{package_module}}/
│       │   ├── __init__.py
│       │   └── core.py
│       └── tests/
│           └── test_import.py
├── docs/                              # only when use_github_actions == "yes"
├── .github/workflows/                 # only when use_github_actions == "yes"
├── pyproject.toml                     # workspace root: [tool.uv.workspace], dependency-groups
├── cog.toml                           # cocogitto monorepo: [packages.*]
├── justfile
├── mkdocs.yml                         # only when use_github_actions == "yes"
├── .pre-commit-config.yaml
├── .ruff.toml
├── .yamlfmt.yaml
└── README.md
```

The root `pyproject.toml` is **not a buildable package** (`package = false`); it only declares the workspace and its dev/docs dependency groups. Each member under `packages/*` is its own buildable distribution.

## Template-specific prompts

| Variable | Description |
| --- | --- |
| `project_slug` | Repository directory name — kebab-cased (lowercase, hyphens). |
| `package_name` | Initial workspace member's distribution name (e.g. `my-project-core`). Defaults to `{{project_slug}}-core`. |
| `package_slug` | Auto-derived from `package_name` — kebab-cased; the directory under `packages/`. |
| `package_module` | Auto-derived Python module name (`package_slug` with hyphens swapped for underscores). |
| `use_github_actions` | Same as in the python template. |

`post_gen_project.py` validates the slug + module names, removes opt-out files, and runs `uv sync --all-groups` when `install_after_generate == yes`.

## Adding more workspace members

After scaffolding, drop another package under `packages/`:

```bash
mkdir -p packages/my-other-package/src/my_other_package
# author packages/my-other-package/pyproject.toml as a normal hatchling package
just init   # uv sync --all-groups picks it up automatically
```

Then register it in `cog.toml` so the monorepo bump knows about it (see below).

## Dependency layout

Dev and docs deps live in `[dependency-groups]` (workspace-aware):

```toml
[tool.uv]
package = false

[tool.uv.workspace]
members = ["packages/*"]

[dependency-groups]
dev = [
    "pytest>=8.3.4",
    "pytest-mock>=3.14.0",
    "pytest-cov>=6.0.0",
]

docs = [
    "mkdocs>=1.5.3",
    "mkdocs-material>=9.5.3",
    # ...
]
```

`just init` runs `uv sync --all-groups`, which installs every member and every group into a single shared venv.

## Test layout

Tests live under each package: `packages/*/tests/`.

```bash
just test         # run the dev-version sweep across packages/*/tests/
just test-all     # iterate every Python version in min..max
```

Coverage is reported across the matching `package_module`.

## Build & publish

`uv build --all-packages` builds every member into `dist/`, and `uv publish dist/*` ships them in one go. The `package-release.yaml` workflow runs both on tag pushes.

## Monorepo Cocogitto config

`cog.toml` enables monorepo bumps:

```toml
generate_mono_repository_global_tag = true
generate_mono_repository_package_tags = true
monorepo_version_separator = "-"

post_bump_hooks = [
    "uv lock --no-upgrade",
    "git add uv.lock",
    "git commit --amend --no-edit",
]

[packages.{{package_slug}}]
path = "packages/{{package_slug}}"
public_api = true
changelog_path = "packages/{{package_slug}}/CHANGELOG.md"
pre_bump_hooks = [
    "uv version --package {{package_slug}} {{version}}",
]
```

What this gives you per release:

- A **per-package** SemVer tag for each package whose source tree saw conventional commits since its last release. Tag format: `{{package_slug}}-X.Y.Z` (the separator comes from `monorepo_version_separator`).
- A **global** SemVer tag covering the whole repo state. The `package-release.yaml` workflow's `[0-9]+.[0-9]+.[0-9]+` tag filter triggers off this tag.
- Each package's version is updated via `uv version --package <slug>` before the bump commit, and the workspace `uv.lock` is regenerated and amended into the same commit by the global `post_bump_hooks`.

When you add a new workspace member, register it as another `[packages.<slug>]` block with the same shape. See the [Cocogitto monorepo guide](https://docs.cocogitto.io/guide/monorepo.html) for `public_api`, `bump_order`, and per-package profiles.
