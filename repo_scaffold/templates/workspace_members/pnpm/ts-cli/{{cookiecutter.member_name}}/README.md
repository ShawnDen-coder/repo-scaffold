# {{ cookiecutter.package_name }}

TypeScript CLI member for this pnpm workspace.

## Commands

```bash
pnpm --filter {{ cookiecutter.package_name }} build
pnpm --filter {{ cookiecutter.package_name }} test
pnpm --filter {{ cookiecutter.package_name }} exec {{ cookiecutter.member_name }} hello
```

`dist/index.cjs` is the published binary entry point.
