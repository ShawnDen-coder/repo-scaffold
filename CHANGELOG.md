# Changelog

All notable changes to this project will be documented in this file.
See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

- - -
## [0.32.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/31b8545aa4dcc862153d9cb419e3a31e127094c4..0.32.0) - 2026-08-26
#### Bug Fixes
- validate generated pnpm members end to end - ([9065665](https://github.com/ShawnDen-coder/repo-scaffold/commit/9065665a71379968a9cc58315443d67b4e2f4804)) - colyerdeng
- make generated workspace members buildable - ([dfa7064](https://github.com/ShawnDen-coder/repo-scaffold/commit/dfa70640f23871d996b4d9b0788221e5df48287a)) - colyerdeng
#### Features
- add typed workspace member templates - ([31b8545](https://github.com/ShawnDen-coder/repo-scaffold/commit/31b8545aa4dcc862153d9cb419e3a31e127094c4)) - colyerdeng
#### Tests
- harden workspace member generation - ([13e8257](https://github.com/ShawnDen-coder/repo-scaffold/commit/13e8257f1cf6ac485b60685da6bb1074d5ac5106)) - colyerdeng

- - -

## [0.31.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/6191eb585ded086b23e0b5c30ae60e6c7b8d5dd7..0.31.1) - 2026-08-25
#### Bug Fixes
- **(electron)** resolve pnpm Windows shim - ([6191eb5](https://github.com/ShawnDen-coder/repo-scaffold/commit/6191eb585ded086b23e0b5c30ae60e6c7b8d5dd7)) - colyerdeng

- - -

## [0.31.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/a53fcdac37a1bc2ea53a9aaf8ada7ffe68492241..0.31.0) - 2026-08-24
#### Bug Fixes
- **(release)** let CI own project version - ([e3c1d41](https://github.com/ShawnDen-coder/repo-scaffold/commit/e3c1d417d3515674f2252105c57cb20593ac32f3)) - ShawnDeng-code
- **(tests)** avoid hardcoded workflow version - ([3e87d44](https://github.com/ShawnDen-coder/repo-scaffold/commit/3e87d440de02e5241cf5e3ed4609cdf622f5837a)) - ShawnDeng-code
#### Features
- **(templates)** add generic electron workspace - ([7ab37d8](https://github.com/ShawnDen-coder/repo-scaffold/commit/7ab37d88b2d1118882528291996766f3415b0f05)) - ShawnDeng-code
#### Miscellaneous Chores
- **(deps)** update shawnden-coder/repo-scaffold action to v0.29.4 - ([e6e7a42](https://github.com/ShawnDen-coder/repo-scaffold/commit/e6e7a420112ec6b6c346d7ce01f267c5eec40953)) - renovate[bot]
- **(deps)** update docker/login-action action to v4 - ([ae0390d](https://github.com/ShawnDen-coder/repo-scaffold/commit/ae0390d0f0d896a925932aa5f471ee6a3c671def)) - renovate[bot]
- **(deps)** update docker/build-push-action action to v7 - ([e6c1527](https://github.com/ShawnDen-coder/repo-scaffold/commit/e6c152728674b5973b3a8dd631eeee629de20e58)) - renovate[bot]
- **(deps)** update docker/setup-qemu-action action to v4 - ([1b65be1](https://github.com/ShawnDen-coder/repo-scaffold/commit/1b65be14f38c32fe2d3aafa848d418ba98d6ca5d)) - renovate[bot]
- **(deps)** update github artifact actions - ([89d4cc2](https://github.com/ShawnDen-coder/repo-scaffold/commit/89d4cc2aa3c4ae95f6d30c6c0ba6f37a785d6e31)) - renovate[bot]
- **(deps)** update actions/setup-node action to v7 - ([d7c210b](https://github.com/ShawnDen-coder/repo-scaffold/commit/d7c210b32d28f90a97a7746b4468664754f852d2)) - renovate[bot]
- **(deps)** update actions/cache action to v6 - ([5f3e353](https://github.com/ShawnDen-coder/repo-scaffold/commit/5f3e35351ff0567bdce41477105dff701c38f83f)) - renovate[bot]
- **(deps)** update pnpm/action-setup action to v6 - ([2869c7e](https://github.com/ShawnDen-coder/repo-scaffold/commit/2869c7ece724e67199dbaaaf6965fb3591ec60bf)) - renovate[bot]
- **(deps)** update redhat-actions/buildah-build action to v3 - ([9dcf035](https://github.com/ShawnDen-coder/repo-scaffold/commit/9dcf035e3d106ff2c0949ade650fef95dfb6ab7d)) - renovate[bot]
- **(deps)** update redhat-actions/podman-login action to v2 - ([89374b5](https://github.com/ShawnDen-coder/repo-scaffold/commit/89374b58c3da7859e8a180287c2fcc50c9b6be61)) - renovate[bot]
- **(deps)** update redhat-actions/push-to-registry action to v3 - ([849ab5f](https://github.com/ShawnDen-coder/repo-scaffold/commit/849ab5fda4a84ed4dd43dca577af6bfc9d6f66c5)) - renovate[bot]
- **(deps)** update softprops/action-gh-release action to v3 - ([a53fcda](https://github.com/ShawnDen-coder/repo-scaffold/commit/a53fcdac37a1bc2ea53a9aaf8ada7ffe68492241)) - renovate[bot]

- - -

## [0.30.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/a8429d3428327df51da735ef8f03151ac2ecbb03..0.30.0) - 2026-08-23
#### Bug Fixes
- **(tests)** satisfy Ruff line length - ([0f18f42](https://github.com/ShawnDen-coder/repo-scaffold/commit/0f18f4298c9a0d696dcd720cc4b4ce02d4e072c4)) - ShawnDeng-code
- **(workflows)** forward nested package credentials - ([e54d1ef](https://github.com/ShawnDen-coder/repo-scaffold/commit/e54d1efb1a2828bd54d22215b669fe806044e0eb)) - ShawnDeng-code
#### Features
- **(templates)** adopt corrected Python workflows - ([805e996](https://github.com/ShawnDen-coder/repo-scaffold/commit/805e9964b57a65bbd6f48dcaf94bd464ed56764f)) - ShawnDeng-code
- **(workflows)** centralize Rust container pipelines - ([6ef87a9](https://github.com/ShawnDen-coder/repo-scaffold/commit/6ef87a9caed74eab325b78a52253c6bab1f177a7)) - ShawnDeng-code
#### Miscellaneous Chores
- **(deps)** update actions/checkout action to v7 - ([3de88ff](https://github.com/ShawnDen-coder/repo-scaffold/commit/3de88ff36c228e1d1fa73d9fd2e4951dd3d36fff)) - renovate[bot]
- **(deps)** update astral-sh/setup-uv action to v10 - ([130cf74](https://github.com/ShawnDen-coder/repo-scaffold/commit/130cf741e20d1fd8c4eee21f17783ebd3d7b00ef)) - renovate[bot]
- **(deps)** lock file maintenance - ([a8429d3](https://github.com/ShawnDen-coder/repo-scaffold/commit/a8429d3428327df51da735ef8f03151ac2ecbb03)) - renovate[bot]

- - -

## [0.29.4](https://github.com/ShawnDen-coder/repo-scaffold/compare/ec06f703c49cfd420dbf49ec31077d6adc5835b7..0.29.4) - 2026-08-23
#### Bug Fixes
- **(renovate)** ignore template package metadata - ([ec06f70](https://github.com/ShawnDen-coder/repo-scaffold/commit/ec06f703c49cfd420dbf49ec31077d6adc5835b7)) - ShawnDeng-code

- - -

## [0.29.3](https://github.com/ShawnDen-coder/repo-scaffold/compare/2cdbbb4f288b19b020025d9b97db01471e761b1e..0.29.3) - 2026-08-23
#### Bug Fixes
- **(renovate)** keep GitHub Action version tags - ([2cdbbb4](https://github.com/ShawnDen-coder/repo-scaffold/commit/2cdbbb4f288b19b020025d9b97db01471e761b1e)) - ShawnDeng-code

- - -

## [0.29.2](https://github.com/ShawnDen-coder/repo-scaffold/compare/d277ca68f46bb1b54368d167f85a55846ab1c224..0.29.2) - 2026-08-23
#### Bug Fixes
- **(renovate)** preserve workflow version tags - ([d277ca6](https://github.com/ShawnDen-coder/repo-scaffold/commit/d277ca68f46bb1b54368d167f85a55846ab1c224)) - ShawnDeng-code

- - -

## [0.29.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/0c132317170578efe7843e8b56f17080ffbbd053..0.29.1) - 2026-08-23
#### Bug Fixes
- **(workflows)** preserve package write permission - ([0c13231](https://github.com/ShawnDen-coder/repo-scaffold/commit/0c132317170578efe7843e8b56f17080ffbbd053)) - ShawnDeng-code

- - -

## [0.29.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/e69529406d6cee05f1bfe5b8eed7c3344ed7e089..0.29.0) - 2026-08-23
#### Features
- **(workflows)** configure container release inputs - ([e695294](https://github.com/ShawnDen-coder/repo-scaffold/commit/e69529406d6cee05f1bfe5b8eed7c3344ed7e089)) - ShawnDeng-code

- - -

## [0.28.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/e890d8ed0d365423ffaf196b1521b574f2fff75b..0.28.0) - 2026-08-23
#### Features
- **(workflows)** support release artifacts in docs deploy - ([e890d8e](https://github.com/ShawnDen-coder/repo-scaffold/commit/e890d8ed0d365423ffaf196b1521b574f2fff75b)) - ShawnDeng-code

- - -

## [0.27.1](https://github.com/ShawnDen-coder/repo-scaffold/compare/42dc9ab555d41e969c6470dcc8e421c327f1e273..0.27.1) - 2026-08-23
#### Bug Fixes
- **(workflows)** restore bootstrap release pipelines - ([42dc9ab](https://github.com/ShawnDen-coder/repo-scaffold/commit/42dc9ab555d41e969c6470dcc8e421c327f1e273)) - ShawnDeng-code

- - -

## [0.27.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/36848d198a99417a49a57f227adfb26aa0e5fd2f..0.27.0) - 2026-08-23
#### Bug Fixes
- **(workflows)** use local callers in repository ci - ([d997620](https://github.com/ShawnDen-coder/repo-scaffold/commit/d9976206d0abc924a78a45521b7bd5417d6b9884)) - ShawnDeng-code
#### Documentation
- **(workflows)** explain shared workflow design - ([5bf28ff](https://github.com/ShawnDen-coder/repo-scaffold/commit/5bf28ff1f98f1c46f67913762b995d7094b198ee)) - ShawnDeng-code
#### Features
- **(workflows)** centralize node and rust releases - ([3dfa251](https://github.com/ShawnDen-coder/repo-scaffold/commit/3dfa251310b2e0d3cd1b623a946735fa83e75586)) - ShawnDeng-code
- **(workflows)** centralize rust ci - ([affa71c](https://github.com/ShawnDen-coder/repo-scaffold/commit/affa71ca7a818bc855f8d167120580cb685cfab5)) - ShawnDeng-code
- **(workflows)** centralize node ci - ([377fcdf](https://github.com/ShawnDen-coder/repo-scaffold/commit/377fcdf987f0315c193df9f88e6168d162b83531)) - ShawnDeng-code
- **(workflows)** centralize python releases - ([86c2359](https://github.com/ShawnDen-coder/repo-scaffold/commit/86c2359fee13b59c71da50b239313841ac249270)) - ShawnDeng-code
- **(workflows)** centralize docs deployment - ([9c24e0e](https://github.com/ShawnDen-coder/repo-scaffold/commit/9c24e0ecd6d5a90207e0926fb67aa49ae11ba87a)) - ShawnDeng-code
- **(workflows)** centralize python ci - ([36848d1](https://github.com/ShawnDen-coder/repo-scaffold/commit/36848d198a99417a49a57f227adfb26aa0e5fd2f)) - ShawnDeng-code
#### Miscellaneous Chores
- **(version)** prepare 0.27.0 - ([e78c0d3](https://github.com/ShawnDen-coder/repo-scaffold/commit/e78c0d39f0beaafecdf7c626e8fdfc44f122f4a7)) - ShawnDeng-code
#### Refactoring
- **(workflows)** use shared workflows internally - ([7f72af3](https://github.com/ShawnDen-coder/repo-scaffold/commit/7f72af3e2ccdd9e78df2c073a05a4f0c85b2e725)) - ShawnDeng-code

- - -

## [0.26.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/7861927d52d8f9fe98a997211be35db244dbf6e7..0.26.0) - 2026-08-23
#### Features
- **(python-template)** adopt reusable release workflows - ([c3d84c9](https://github.com/ShawnDen-coder/repo-scaffold/commit/c3d84c93f5486ae6fa97fbbb0c6c32548bf0e667)) - ShawnDeng-code
- **(uv-workspace)** adopt reusable release workflows - ([7861927](https://github.com/ShawnDen-coder/repo-scaffold/commit/7861927d52d8f9fe98a997211be35db244dbf6e7)) - ShawnDeng-code

- - -

## [0.25.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/25e676146dd7d28b9bf1e5acddbaf88d0e0e0efb..0.25.0) - 2026-07-29
#### Features
- **(uv-workspace)** sync template with trade-system best practices - ([25e6761](https://github.com/ShawnDen-coder/repo-scaffold/commit/25e676146dd7d28b9bf1e5acddbaf88d0e0e0efb)) - colyerdeng

- - -

## [0.24.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/bb157459990fbc7d395056559a24c6afe0ef7ac1..0.24.0) - 2026-07-22
#### Features
- **(templates)** add ts-sdk, pnpm-workspace, and vue-project templates + modularize pnpm workflows - ([bb15745](https://github.com/ShawnDen-coder/repo-scaffold/commit/bb157459990fbc7d395056559a24c6afe0ef7ac1)) - colyerdeng
- add Renovate dependency update config to all templates - ([6208059](https://github.com/ShawnDen-coder/repo-scaffold/commit/620805911ed934cfbc7897f86e795ae571286993)) - colyerdeng

- - -

## [0.23.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/b07a539cffcd1a79a0462c9bc91fb1efab96f37b..0.23.0) - 2026-07-15
#### Features
- **(cli)** add add-package subcommand for workspace package management - ([9dad424](https://github.com/ShawnDen-coder/repo-scaffold/commit/9dad42451b393f7386cb6de20d375d1e7b6d2d72)) - ShawnDen-coder
- **(rust-template)** add Axum + SQLx cargo workspace template - ([b07a539](https://github.com/ShawnDen-coder/repo-scaffold/commit/b07a539cffcd1a79a0462c9bc91fb1efab96f37b)) - ShawnDen-coder
#### Miscellaneous Chores
- remove deprecated scripts/add_package.py from templates - ([170bbf1](https://github.com/ShawnDen-coder/repo-scaffold/commit/170bbf1ade34133907f215259587686b58d1de6f)) - ShawnDen-coder

- - -

## [0.22.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/d5e762b6f5b6d46827d68e81a17115ac880aa965..0.22.0) - 2026-07-15
#### Features
- **(react-template)** add justfile, usehooks-ts, and rename demo to base样板 - ([029e326](https://github.com/ShawnDen-coder/repo-scaffold/commit/029e326fa5b8a99a29fab8381a5a3a54b94863db)) - ShawnDen-coder
#### Miscellaneous Chores
- **(react-template)** remove .cta.json scaffolding state file - ([d5e762b](https://github.com/ShawnDen-coder/repo-scaffold/commit/d5e762b6f5b6d46827d68e81a17115ac880aa965)) - ShawnDen-coder

- - -

## [0.21.0](https://github.com/ShawnDen-coder/repo-scaffold/compare/003505693f0f0c1e312c8dfdd08ebeb3e3752707..0.21.0) - 2026-07-14
#### Features
- **(react-template)** add Docker/Podman containerization support - ([591257b](https://github.com/ShawnDen-coder/repo-scaffold/commit/591257bcd267c7d7f984178382d2888ea9023653)) - ShawnDen-coder
- add TanStack Start React template with MUI and pnpm - ([0035056](https://github.com/ShawnDen-coder/repo-scaffold/commit/003505693f0f0c1e312c8dfdd08ebeb3e3752707)) - ShawnDen-coder
#### Miscellaneous Chores
- add tmp/ to gitignore and vscode pytest settings - ([8103e86](https://github.com/ShawnDen-coder/repo-scaffold/commit/8103e86f6a7766b852bf32391789c82a6fb8b894)) - ShawnDen-coder

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

