# {{cookiecutter.repo_name}}

### Overview

{{cookiecutter.description}}

### Workspace layout

This repository is a uv workspace. Packages live under `packages/`.

### Development

```bash
uvx --from rust-just just init
uvx --from rust-just just lint
uvx --from rust-just just test-all
```
