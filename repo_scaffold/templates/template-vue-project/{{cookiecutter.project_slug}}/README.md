# {{cookiecutter.project_slug}}

{{cookiecutter.description}}

## Tech Stack

- **Vue 3** — Composition API with `<script setup>`
- **Vue Router** — File-based routing with lazy-loaded pages
- **Pinia** — Type-safe state management
- **Tailwind CSS v4** — Utility-first styling with `@tailwindcss/vite`
- **TypeScript** — Strict mode with `vue-tsc`
- **Vite** — Fast dev server and build

## Project Structure

```
src/
├── components/
│   ├── ui/          → Reusable UI primitives (AppButton, AppCard)
│   ├── layout/      → App shell (AppHeader, AppFooter)
│   └── common/      → Shared non-domain components (EmptyState, ContentNote, FolderTree)
├── pages/
│   ├── HomePage/    → Home page + private sub-components
│   └── AboutPage/   → About page
├── router/          → Vue Router config + setup helper
├── stores/          → Pinia stores + setup helper
├── App.vue          → Root layout (Header → RouterView → Footer)
├── main.ts          → App bootstrap
└── style.css        → Tailwind + design tokens
```

## Commands

| Command | Description |
|---|---|
| `pnpm dev` | Start dev server |
| `pnpm build` | Type-check and build for production |
| `pnpm preview` | Preview production build |
| `pnpm format` | Format with Prettier |
| `pnpm format:check` | Check formatting |

## Development

```bash
pnpm install
pnpm dev
```

## License

MIT
