# Workspace Member v1 Migration

This is a breaking v1 migration from package-specific workspace additions to a
workspace-member command.

## Compatibility

- repo-scaffold add-member is the v1 command.
- repo-scaffold add-package NAME -p PATH remains as a deprecated alias with
  its existing flags and defaults.
- New flags belong to add-member; the legacy command must not silently accept
  or reinterpret them.

## Release

The migration is released as 1.0.0. The release commit must use a breaking
Conventional Commit marker (feat!:) so Cocogitto computes the major release.

## First delivery

- `pnpm / ts-lib` and `pnpm / ts-cli` are delivered by v1.
- Existing uv and Cargo library behavior remains available behind the same
  `add-member` domain model.
- Other pnpm member types (`react-app`, `node-service`, and Vue or
  Electron variants) are deliberately deferred until their full standalone
  templates have been exercised and stabilized.

## Generated workspace workflow

New pnpm and Electron workspace templates contain `.repo-scaffold.toml` as
workspace metadata and pin their task-runner integration to `repo-scaffold==1.0.0`:

```bash
just add-member agent-core ts-lib
just add-lib agent-core
just add-member release-tool ts-cli
just plan-member agent-core ts-lib
```

The CLI remains usable directly for automation or non-generated workspaces:

