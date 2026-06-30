# `repo-scaffold gh-init`

Bootstrap a GitHub repository for a project that you've already generated with `repo-scaffold create`. The command:

1. Creates the repository on GitHub (or finds it, with `--allow-existing`).
2. Sets the Actions secrets and variables that the generated workflows expect.
3. Initializes git locally (if needed), commits, and pushes the initial revision.
4. Creates the `gh-pages` branch and sets it as the GitHub Pages source (unless `--no-pages`).

Pages is configured for you, so there's no manual **Settings → Pages** step left — push your first version tag and the `docs-deploy` workflow publishes to `gh-pages`.

## Prerequisites

- A GitHub personal access token in the `GITHUB_TOKEN` environment variable.
  - **Public repo**: `public_repo` scope is enough.
  - **Private repo**: `repo` scope.
  - Generate one at <https://github.com/settings/tokens>.
- `git` on `PATH` (only needed when pushing).

`gh-init` does **not** read `gh auth token`. Set `GITHUB_TOKEN` explicitly so behavior is the same in CI and locally.

## Usage

```bash
# Generate a project, then push it to your account.
repo-scaffold create python --no-input -o ./projects
export GITHUB_TOKEN=ghp_...
repo-scaffold gh-init ./projects/my-python-project
```

The command will print a summary, prompt you to confirm, then create the repo and push.

### Common flags

| Flag | Behavior |
| --- | --- |
| `--owner <user-or-org>` | Push to an organization instead of your own account. |
| `--name <repo>` | Override the repository name (default: `pyproject.toml` `project.name`). |
| `--description <text>` | Override the repository description. |
| `--private` / `--public` | Repository visibility (default: public). |
| `--default-branch <name>` | Override the default branch (default: current local git branch or `master`). |
| `--allow-existing` | Don't fail if the repo already exists; refresh secrets/variables. |
| `--no-push` | Skip git init and push — only configure GitHub. Pages setup is skipped too. |
| `--no-pages` | Push, but don't create `gh-pages` or configure GitHub Pages. |
| `--force-push` | `git push --force` the initial commit (if the remote already has commits). |
| `--no-input` | Don't prompt; missing optional secrets are skipped. |

### Examples

Create a private org repo non-interactively:

```bash
GITHUB_TOKEN=... \
PYPI_SERVER_USERNAME=... \
PYPI_SERVER_PASSWORD=... \
repo-scaffold gh-init ./projects/my-private-tool \
  --owner my-org --private --no-input
```

Re-run after rotating a secret (the repo already exists, you just want to refresh values):

```bash
repo-scaffold gh-init ./projects/my-tool --allow-existing --no-push --no-input
```

## Where the secret values come from

`gh-init` looks for each value in this order. The first non-empty source wins; an empty result is **dropped**, never written as an empty secret.

1. The current process environment (`GITHUB_TOKEN`, `PYPI_TOKEN`, etc.).
2. A `.env` file in the project directory (simple `KEY=VALUE` lines, comments with `#`).
3. Interactive prompts (skipped under `--no-input`).
4. Defaults from the project's `pyproject.toml` for the repo name and description.

The default keys configured in the generated workflows are:

| Kind | Name | Used by |
| --- | --- | --- |
| Secret | `PERSONAL_ACCESS_TOKEN` | `version-bump` (push tags), `package-release` (GitHub Release), `container-release` (GHCR) |
| Secret | `PYPI_TOKEN` | `package-release` → public PyPI |
| Secret | `PYPI_SERVER_USERNAME` | `package-release` → private PyPI server |
| Secret | `PYPI_SERVER_PASSWORD` | `package-release` → private PyPI server |
| Variable | `PUBLISH_TO_PUBLIC_PYPI` | gates the public PyPI publish job (`'true'` to enable) |

Anything you skip can be added later under **Settings → Secrets and variables → Actions**.

## What the command actually does

1. Reads `GITHUB_TOKEN`, calls `GET /user` to verify the token early.
2. Calls `POST /user/repos` (or `POST /orgs/{owner}/repos`) with `auto_init=false`. If the repo exists and `--allow-existing` is set, it falls back to `GET /repos/{owner}/{name}`.
3. For each non-empty secret, calls the Actions secrets API (PUT, so existing secrets are overwritten).
4. For each non-empty variable, calls the Actions variables API. If the variable already exists, the call falls back to an `edit`.
5. Unless `--no-push` is set: runs `git init` if needed, stages every tracked and untracked file, creates a `chore: initial commit from repo-scaffold [skip ci]` commit (only if HEAD doesn't yet exist), renames the current branch, sets `origin`, and pushes. GitHub Actions treats `[skip ci]` in the commit message as a built-in signal to skip workflows for this bootstrap push; `gh-init` only adds it to the generated initial commit, not to later user commits.
6. Unless `--no-pages` (or `--no-push`) is set: creates `refs/heads/gh-pages` from the pushed default branch's head commit (skipped if it already exists), then calls the Pages API (`POST .../pages`, falling back to `PUT` if a site already exists) to set the source to `gh-pages` / `/ (root)`. PyGithub 2.x has no Pages helper, so this goes through the raw REST requester. A failure here is reported but does not abort the bootstrap.

## Enabling Pages manually (`--no-pages`)

By default `gh-init` creates the `gh-pages` branch and points Pages at it, so the site goes live after the first `docs-deploy` run with no extra clicks. The docs workflow uses `mkdocs gh-deploy --force` to overwrite `gh-pages` with the built HTML on each version tag.

If you ran with `--no-pages` (or `--no-push`), enable it yourself after the first `docs-deploy` run (triggered by your first version tag, e.g. `0.1.0`):

1. Open the new repo on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source: Deploy from a branch**.
4. Pick the `gh-pages` branch and `/ (root)` as the path.
5. Save. The site appears at `https://<owner>.github.io/<repo>` within a minute.
