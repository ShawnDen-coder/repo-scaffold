# CI/CD pipeline

Every generated project ships a self-contained GitHub Actions pipeline that wires test → version bump → publish → docs → (optional) container release together. Both templates use the same five-workflow skeleton; the `python` template adds a sixth workflow when Podman is enabled.

This page documents what each workflow does, how they trigger one another, and what secrets / variables you need to configure on the repository.

## Pipeline at a glance

```
push to master/main ──▶ ci-tests       (lint + matrix tests)
                  └──▶ version-bump    (cocogitto release)
                          │
                          └─push tag X.Y.Z──▶ package-release  (build → publish → GitHub release)
                                          └─▶ docs-deploy      (mkdocs gh-deploy)
                                          └─▶ container-release (python + use_podman only)

pull_request ────────▶ ci-tests
```

| Workflow | Trigger | Purpose | `python` | `uv-workspace` |
| --- | --- | --- | --- | --- |
| `ci-tests.yaml` | push / pull_request | Lint + multi-Python matrix tests | ✅ | ✅ |
| `version-bump.yaml` | push to `master` / `main` | Cocogitto computes next version, updates files, tags | ✅ | ✅ (monorepo mode) |
| `package-release.yaml` | tag matching `[0-9]+.[0-9]+.[0-9]+` | Build → publish (public + private PyPI) → GitHub Release | ✅ | ✅ |
| `docs-deploy.yaml` | tag or manual dispatch | `mkdocs gh-deploy` to the `gh-pages` branch | only with `use_github_actions=yes` | only with `use_github_actions=yes` |
| `container-release.yaml` | GitHub Release published | Multi-arch container build → push to GHCR | only with `use_podman=yes` | — |

## Required secrets and variables

Set these once in **Settings → Secrets and variables → Actions** before the first push:

| Name | Type | Used by |
| --- | --- | --- |
| `PERSONAL_ACCESS_TOKEN` | Secret | `version-bump` (push tags), `container-release` (push to GHCR), `package-release` (create GitHub Release) |
| `PYPI_TOKEN` | Secret | `package-release` → public PyPI |
| `PYPI_SERVER_USERNAME` / `PYPI_SERVER_PASSWORD` | Secret | `package-release` → private PyPI server, plus uv index auth across all workflows |
| `PUBLISH_TO_PUBLIC_PYPI` | **Variable** | Set to `'true'` to enable the public PyPI publish job. Leave unset for private-only releases. |

`PERSONAL_ACCESS_TOKEN` must be a fine-grained PAT (or classic) with **`contents: write`** at minimum. The reason it is needed instead of the default `GITHUB_TOKEN` is so that the bump commit + tag pushed by `version-bump` actually triggers downstream workflows — pushes made with the default token do not re-trigger workflows by design.

## `ci-tests.yaml` — code quality gate

```
┌──────────┐    ┌────────────────────────────┐
│   lint   │──▶ │  test (matrix: 3.x, ...)   │
└──────────┘    └────────────────────────────┘
```

Runs on every push to `master` / `main` and every pull request.

**`lint` job**

- `setup-uv@v5` with `enable-cache: true`.
- `just init` to bootstrap the env (installs `rust-just` as a uv tool, `uv sync`, installs pre-commit hooks).
- `just lint` — Ruff fix + format + final verification check.
- `just lint-pre-commit` — runs every pre-commit hook (`uv-lock`, `yamlfmt`, `check-github-workflows`, `actionlint`) so workflow YAML errors are caught in PRs, not on `master`.

**`test` job (matrix)**

- `strategy.matrix.python-version` is rendered statically by Cookiecutter from `min_python_version..max_python_version`. Picking `3.10..3.13` produces `["3.10", "3.11", "3.12", "3.13"]`, so each version runs in its own runner in parallel.
- `fail-fast: false` so one version's failure doesn't kill the rest — useful for spotting compatibility issues at a glance.
- `setup-uv@v5` with `python-version: ${{ matrix.python-version }}` provisions the right interpreter directly through uv (no separate `actions/setup-python` step).
- `python` template: `uv sync --all-extras` then `just test-version <ver>`.
- `uv-workspace` template: `uv sync --all-groups` then `just test-version <ver>` — pytest is pointed at `packages/` so all members run together.

**Concurrency**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

PR pushes cancel superseded runs to save minutes; pushes to `master` / `main` are queued (never cancelled), so failed runs on the default branch always show up.

**Container build smoke test (`python` only, `use_podman=yes`)**

When the `python` template is generated with `use_podman=yes`, an extra `container-build-test` job runs alongside the test matrix:

- Sets up QEMU.
- Builds the container image for `linux/amd64` and `linux/arm64` via `redhat-actions/buildah-build@v2`.
- **Does not push** — the build itself is the assertion.

This catches Dockerfile / dependency regressions on PRs, before they would otherwise blow up in `container-release`.

## `version-bump.yaml` — cocogitto release

```
┌─────────────────────────────────────────────────┐
│ release (cocogitto/cocogitto-action@v3)         │
│   - cog bump --auto                             │
│   - run pre_bump_hooks (uv version, uv lock)    │
│   - update CHANGELOG.md                         │
│   - commit + tag (cog-bot identity)             │
│   - push commit + tag                           │
└─────────────────────────────────────────────────┘
```

Triggers on every push to `master` / `main` (and `workflow_dispatch`).

**Skip guard**

```yaml
if: ${{ !startsWith(github.event.head_commit.message, 'chore(version):') }}
```

Cocogitto's own bump commits are prefixed with `chore(version):`, so the workflow ignores them and avoids re-triggering itself.

**Why a PAT, not the default token**

Checkout uses `token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}`. When cocogitto pushes the bump commit and tag, that push needs to come from a token GitHub recognizes as "real activity" — pushes made with the default `GITHUB_TOKEN` are explicitly prevented from triggering downstream workflows, which would mean the `X.Y.Z` tag push never fires `package-release` or `docs-deploy`.

**Concurrency**

```yaml
concurrency:
  group: version-bump-${{ github.ref }}
  cancel-in-progress: false
```

Two pushes in quick succession are queued, never run in parallel — important because cocogitto computes the next version from current refs and concurrent runs would race each other.

**Monorepo difference (`uv-workspace`)**

The workflow file itself is identical to the `python` template's. The monorepo behavior comes entirely from `cog.toml`:

- `generate_mono_repository_global_tag = true` → one `X.Y.Z` tag for the repo state.
- `generate_mono_repository_package_tags = true` + `monorepo_version_separator = "-"` → per-package tags like `<pkg>-X.Y.Z`.
- `[packages.<slug>]` blocks tell cocogitto which paths "belong" to each package, so a commit only bumps the packages whose paths it touched.

The downstream `package-release` workflow only listens for the global `X.Y.Z` tag, so a single bump cycle produces one publish run.

## `package-release.yaml` — build & publish

```
┌─────────┐
│  build  │ ── upload-artifact dist/
└────┬────┘
     ├──────────────────┬───────────────────┐
     ▼                  ▼                   ▼
publish-pypi    publish-private-pypi   (gate)
(if PUBLISH_     (always)               │
 TO_PUBLIC_PYPI                         │
 == 'true')                             │
     └──────────────────┴───────────────────┘
                        ▼
                ┌──────────────┐
                │   release    │  softprops/action-gh-release
                └──────────────┘
```

Triggers on tag pushes matching `[0-9]+.[0-9]+.[0-9]+`.

**`build` job**

`just build` (which is `uv build` for the `python` template, `uv build --all-packages` for `uv-workspace`). The `dist/` directory is uploaded as an artifact named `dist`, so downstream publishers don't recompile.

**`publish-pypi` (public)**

- Gated on the `PUBLISH_TO_PUBLIC_PYPI` repository variable so closed-source projects can release to private only.
- Uses PyPI [trusted publishing](https://docs.pypi.org/trusted-publishers/) (`id-token: write`) plus `UV_PUBLISH_TOKEN`.
- `uv-workspace`: `just publish-pypi` invokes `uv publish --check-url https://pypi.org/simple/`, so packages whose version is already on PyPI are silently skipped — important when only some workspace members were bumped.

**`publish-private-pypi`**

- Always runs.
- Calls `just publish-pypi-server`, which forwards `PYPI_SERVER_USERNAME` / `PYPI_SERVER_PASSWORD` and the configured `PYPI_SERVER_URL` to `uv publish --username --password --publish-url`.
- `uv-workspace`: same `--check-url` skip behavior, scoped to the private index.

**`release` job**

```yaml
needs: [publish-pypi, publish-private-pypi]
if: ${{ !failure() && !cancelled() }}
```

Runs after both publish jobs as long as nothing actually failed — a `skipped` `publish-pypi` (private-only mode) does not block the GitHub Release. Downloads the `dist/` artifact and creates a GitHub Release with auto-generated notes plus the wheel and sdist attached.

## `docs-deploy.yaml` — documentation

A single job; both templates ship the same content.

```
push tag X.Y.Z (or workflow_dispatch)
       │
       ▼
┌─────────────────────────────────────────────┐
│ deploy                                      │
│   - actions/checkout                        │
│   - setup-uv (cache)                        │
│   - just deploy-gh-pages                    │
│        ↳ uv run mkdocs gh-deploy --force    │
│        ↳ pushes to gh-pages branch          │
└─────────────────────────────────────────────┘
```

- Uses the default `GITHUB_TOKEN` with `permissions: contents: write` — sufficient to push the `gh-pages` branch, no PAT needed.
- `concurrency: { group: pages, cancel-in-progress: false }` queues two close-together releases instead of letting them race the gh-pages branch.
- **Repository setting required**: Settings → Pages → Source → **Deploy from a branch** → `gh-pages` / `(root)`.

The workflow is gated on the same `use_github_actions=yes` cookiecutter prompt as the rest of the docs setup; opting out removes the workflow file along with `mkdocs.yml` and the `docs/` directory.

## `container-release.yaml` — Podman / GHCR

Generated only for the `python` template when `use_podman=yes`. Skipped (the file is removed by `post_gen_project.py`) otherwise.

```
release (Published)
       │
       ▼
┌────────────────────────────────────────────┐
│ push_to_registry                           │
│   - actions/checkout                       │
│   - QEMU                                   │
│   - podman-login (ghcr.io, PAT)            │
│   - buildah-build (linux/amd64,arm64)      │
│       tags: latest, ${sha}, ${ref_name}    │
│   - push-to-registry                       │
└────────────────────────────────────────────┘
```

- Triggers on `release: { types: [published] }`, so it runs after `package-release` finishes successfully.
- `permissions: { contents: read, packages: write }` — the `packages: write` line is what authorizes the push to GHCR.
- Multi-arch builds use buildah with QEMU emulation; the `redhat-actions/*` action stack is small and doesn't need BuildKit.
- Tags pushed every release: `latest`, the commit `${sha}`, and the version `${ref_name}`. `latest` always points at the most recent published release.

## End-to-end timeline

A push of `feat: …` to `master` produces, in order:

1. **`ci-tests`** — lint passes, every Python version in the matrix passes.
2. **`version-bump`** — cocogitto computes a minor bump, updates `pyproject.toml` + `uv.lock` + `CHANGELOG.md`, commits as `cog-bot`, pushes tag `0.2.0`.
3. **`package-release`** — builds, publishes to public + private PyPI, attaches the wheel/sdist to a GitHub Release. The release itself becomes "published".
4. **`docs-deploy`** — `mkdocs gh-deploy` updates `gh-pages` from the freshly tagged source.
5. **`container-release`** (python + Podman only) — multi-arch container image pushed to GHCR.

The whole sequence runs without manual intervention as long as commits follow [Conventional Commits](https://www.conventionalcommits.org/). The only manual step is the initial repository configuration: secrets, the `PUBLISH_TO_PUBLIC_PYPI` variable, and Pages source pointed at `gh-pages`.
