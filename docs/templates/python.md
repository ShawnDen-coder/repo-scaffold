# `python` template

A single-package Python project. Best for one library, one CLI, or one small service per repository.

```bash
repo-scaffold create python
# or fully unattended:
repo-scaffold create python --no-input -o ./out
```

For everything shared with the other template (uv, just, Ruff, pytest, pre-commit, Cocogitto, GitHub Actions, MkDocs), see the [shared infrastructure](index.md#shared-infrastructure) section.

## Layout

```
{{project_slug}}/
├── {{project_slug}}/        # Source package (importable)
│   ├── __init__.py
│   ├── core.py
│   ├── constants.py
│   └── cli.py               # only when include_cli == "yes"
├── tests/
│   └── test_import.py
├── container/               # only when use_podman == "yes"
│   ├── Dockerfile
│   └── compose.yaml
├── docs/                    # only when use_github_actions == "yes"
│   ├── gen_home_pages.py
│   └── gen_ref_pages.py
├── .github/workflows/       # only when use_github_actions == "yes"
├── pyproject.toml           # hatchling build, [project.optional-dependencies]
├── cog.toml                 # cocogitto: pre_bump_hooks run `uv version` + `uv lock`
├── justfile
├── mkdocs.yml               # only when use_github_actions == "yes"
├── .pre-commit-config.yaml
├── .ruff.toml
├── .yamlfmt.yaml
└── README.md
```

The build backend is `hatchling`; the project version is the canonical source-of-truth in `pyproject.toml` and Cocogitto bumps it via `uv version` during release.

## Template-specific prompts

| Variable | Description |
| --- | --- |
| `project_slug` | Auto-derived from `repo_name` — lowercased, spaces and hyphens replaced with underscores, so it doubles as a Python module name. |
| `include_cli` | When `yes`, ship a [Click](https://click.palletsprojects.com/) CLI under `{{project_slug}}.cli:cli` and register it as a `[project.scripts]` entry. When `no`, the file is removed by the post-generation hook. |
| `use_podman` | When `yes`, include `container/Dockerfile`, `container/compose.yaml`, and the `container-release.yaml` workflow. The `justfile` also gains `compose-up` / `compose-down` / `compose-build` / `compose-logs` / `compose-shell` recipes. |
| `use_github_actions` | When `no`, drop `.github/`, `mkdocs.yml`, `docs/`, and the `docs` extra entirely. |

`post_gen_project.py` validates input (Python version range, slug regex), removes opt-out files, and optionally runs `uv sync`.

## Dependency layout

Dev and docs dependencies live in `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
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

`just init` syncs both with `uv sync --all-extras`.

## Optional Podman recipes

When `use_podman == yes`, the `justfile` includes:

```bash
just compose-up        # podman compose up
just compose-down
just compose-build
just compose-logs      # follow logs
just compose-shell     # exec /bin/bash inside the running container
```

The `container-release.yaml` workflow builds and pushes images on tag pushes.
