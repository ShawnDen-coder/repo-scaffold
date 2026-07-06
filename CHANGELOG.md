# Changelog

All notable changes to this project will be documented in this file.
See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

- - -
## [0.20.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/428c1762f0ad75b24010014b3e5d68a5267372ed..0.20.0) - 2026-07-06
#### Features
- sync uv-workspace template with trade-system improvements - ([428c176](https://github.com/ShawnDen-coder/repo-scaffold/commit/428c1762f0ad75b24010014b3e5d68a5267372ed)) - ShawnDeng-code

- - -

## [0.19.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/869e4b1ac3a0b1ee05569dbf1ebc04300147d2a0..0.19.1) - 2026-06-30
#### Bug Fixes
- **(gh-init)** authenticate git push with the bootstrap token - ([869e4b1](https://github.com/ShawnDen-coder/repo-scaffold/commit/869e4b1ac3a0b1ee05569dbf1ebc04300147d2a0)) - ShawnDeng-code

- - -

## [0.19.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/6c5976cd291c8c8da62c9c6c03de71e2f0fcc567..0.19.0) - 2026-06-30
#### Features
- **(gh-init)** detect owner, deploy docs via mkdocs, and split into a package - ([6c5976c](https://github.com/ShawnDen-coder/repo-scaffold/commit/6c5976cd291c8c8da62c9c6c03de71e2f0fcc567)) - ShawnDen-coder

- - -

## [0.18.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/90f983ea941980ba867fd5fd4cd47b5b65360972..0.18.0) - 2026-06-30
#### Features
- **(gh-init)** add --protect-branch to protect the default branch - ([90f983e](https://github.com/ShawnDen-coder/repo-scaffold/commit/90f983ea941980ba867fd5fd4cd47b5b65360972)) - ShawnDen-coder

- - -

## [0.17.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/182fdc7e74b0604f60f49a5dd069a5660365edde..0.17.0) - 2026-06-30
#### Features
- git init on create and auto-configure gh-pages in gh-init - ([182fdc7](https://github.com/ShawnDen-coder/repo-scaffold/commit/182fdc7e74b0604f60f49a5dd069a5660365edde)) - ShawnDen-coder

- - -

## [0.16.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/850b0ba9ec973262479b6d85ab1fb8f4bbf47efd..0.16.1) - 2026-06-30
#### Bug Fixes
- **(ci)** skip bootstrap workflows for generated repos - ([850b0ba](https://github.com/ShawnDen-coder/repo-scaffold/commit/850b0ba9ec973262479b6d85ab1fb8f4bbf47efd)) - ShawnDen-coder
#### Miscellaneous Chores
- **(ci)** push cocogitto tags explicitly - ([87ecfa6](https://github.com/ShawnDen-coder/repo-scaffold/commit/87ecfa6d040c87981470f4933aaffbdd6126c427)) - ShawnDen-coder
- **(version)** 0.16.1 - ([f059cdc](https://github.com/ShawnDen-coder/repo-scaffold/commit/f059cdc09bb06c1094e3ff34bc8c298d7eccaeef)) - cog-bot

- - -

## [0.16.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/850b0ba9ec973262479b6d85ab1fb8f4bbf47efd..0.16.1) - 2026-06-30
#### Bug Fixes
- **(ci)** skip bootstrap workflows for generated repos - ([850b0ba](https://github.com/ShawnDen-coder/repo-scaffold/commit/850b0ba9ec973262479b6d85ab1fb8f4bbf47efd)) - ShawnDen-coder

- - -

## [0.16.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/c312abdad572ea98e387557470eb429bbf6f3d11..0.16.0) - 2026-06-29
#### Bug Fixes
- **(ci)** push bump commit + tag from cog.toml post_bump_hooks - ([363df66](https://github.com/ShawnDen-coder/repo-scaffold/commit/363df66eadf66de1f833c95f63b810a2f202d505)) - ShawnDen-coder
- replace broken pypi badge and add classifiers - ([c312abd](https://github.com/ShawnDen-coder/repo-scaffold/commit/c312abdad572ea98e387557470eb429bbf6f3d11)) - ShawnDen-coder
#### Features
- add `repo-scaffold gh-init` to bootstrap GitHub for a project - ([c70c5a9](https://github.com/ShawnDen-coder/repo-scaffold/commit/c70c5a9f1ab2dd44b4ae0fabf3bf5b9763e11c5a)) - ShawnDen-coder

- - -

## [0.15.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/3fed160c1dfeb4f3f1bc8252d666a7cc5d58287d..0.15.1) - 2026-06-29
#### Bug Fixes
- (**ci**) checkout before download-artifact in publish-private-pypi - ([3fed160](https://github.com/ShawnDen-coder/repo-scaffold/commit/3fed160c1dfeb4f3f1bc8252d666a7cc5d58287d)) - ShawnDen-coder, Claude Opus 4.7 (1M context)

- - -

## [0.15.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/90ad20b8cd357961273a2d277696c6a9bbc68d2e..0.15.0) - 2026-06-29
#### Features
- replace commitizen with cocogitto for versioning - ([90ad20b](https://github.com/ShawnDen-coder/repo-scaffold/commit/90ad20b8cd357961273a2d277696c6a9bbc68d2e)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
#### Bug Fixes
- (**justfile**) make recipes work on Windows PowerShell - ([f0affa4](https://github.com/ShawnDen-coder/repo-scaffold/commit/f0affa4495fa5d863ddcdf76af4ed5c4dd0659df)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
- (**uv-workspace**) skip already-published packages on monorepo release - ([2d12e44](https://github.com/ShawnDen-coder/repo-scaffold/commit/2d12e44a9803c1d8267e30a07fe87ee0d77666ce)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
#### Revert
- (**ci**) keep docs-deploy on the gh-pages branch flow - ([4d61423](https://github.com/ShawnDen-coder/repo-scaffold/commit/4d6142331a212e1695bdc3f43ad5ac771217994f)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
#### Documentation
- add CI/CD pipeline guide and link from template pages - ([0bfe156](https://github.com/ShawnDen-coder/repo-scaffold/commit/0bfe156ae1ed4b743f2a33c2a353da103c547f40)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
- add per-template guides and mkdocs nav entry - ([93c727b](https://github.com/ShawnDen-coder/repo-scaffold/commit/93c727bfb14037d48783ad949573464da5d84e84)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
- clarify post-init usage of plain just - ([d42970f](https://github.com/ShawnDen-coder/repo-scaffold/commit/d42970f8c1e3422c454314f5c8f5b16b39d9576b)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
#### Continuous Integration
- rework workflows for caching, parallelism, and Pages - ([57adc4c](https://github.com/ShawnDen-coder/repo-scaffold/commit/57adc4cf70a24a5bd22636fac7da2958e3597a1c)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
#### Refactoring
- streamline justfile and drop uvx-only dev deps - ([909f6e9](https://github.com/ShawnDen-coder/repo-scaffold/commit/909f6e98dac80719770cf3c02fb48352b4d327f2)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
#### Miscellaneous Chores
- (**changelog**) start a fresh changelog for cocogitto - ([82237f5](https://github.com/ShawnDen-coder/repo-scaffold/commit/82237f55651102833ae84a83c759897977afd918)) - ShawnDen-coder, Claude Opus 4.7 (1M context)
- prepare CHANGELOG.md for cocogitto - ([610c153](https://github.com/ShawnDen-coder/repo-scaffold/commit/610c15363735fe3c41f15be00b885a0cf5b977a8)) - ShawnDen-coder, Claude Opus 4.7 (1M context)

- - -

