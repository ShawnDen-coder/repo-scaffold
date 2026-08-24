# {{cookiecutter.project_slug}}

{{cookiecutter.description}}

## Workspace layout

- `apps/web` — browser application
- `apps/desktop` — Electron main process and desktop shell
- `packages/shared` — framework-independent shared types and utilities
- `packages/ui` — UI components shared by Web and Electron

## Commands

```bash
pnpm install
pnpm dev
pnpm dev:desktop
pnpm typecheck
pnpm test
pnpm build
```

Keep business-specific rules in separate packages; do not couple shared packages to Electron.
