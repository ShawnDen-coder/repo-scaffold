# {{ cookiecutter.project_slug }}

{{ cookiecutter.description }}

## Development

```bash
pnpm install
pnpm check
pnpm typecheck
pnpm test
pnpm build
```

Run the development command directly from TypeScript:

```bash
pnpm exec {{ cookiecutter.project_slug }} hello --name Codex
```

## Release

Use Conventional Commits. Cocogitto updates `package.json` and generates
`CHANGELOG.md` during a version bump; the changelog is intentionally not a
template file.

```bash
cog bump --auto
```
