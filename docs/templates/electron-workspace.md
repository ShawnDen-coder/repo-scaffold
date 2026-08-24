# electron-workspace 模板

`electron-workspace` 是一个通用的 pnpm Monorepo 模板，目标是快速创建同时支持 Web 和 Electron 桌面端的 TypeScript 工程。它只提供工程结构和开发工具，不包含任何具体业务逻辑。

## 生成后的结构

```text
apps/web          浏览器前端
apps/desktop      Electron 主进程和桌面壳
packages/ui       Web 与桌面共享 UI
packages/shared   与框架无关的类型和工具
```

## DevOps 基础组件

- `pnpm-workspace.yaml`：统一管理 `apps/*` 和 `packages/*`。
- `packageManager`：固定 pnpm 主版本，减少本地和 CI 的差异。
- `default_branch`：生成时选择 `main` 或 `master`，CI 和版本工作流会使用同一个分支。
- `justfile`：统一封装安装、格式检查、类型检查、测试、构建和本地启动命令。
- `cog.toml`：使用 Conventional Commits 计算版本、更新 Changelog，并推送版本标签。
- GitHub Actions：调用仓库提供的 `reusable-electron-ci.yaml`、`reusable-electron-release.yaml` 和 `reusable-version-bump.yaml`，统一执行质量检查、跨平台打包和版本发布。
- `.github/renovate.json5`：同时更新 npm 依赖和 GitHub Actions，避免依赖长期过期。
- Conventional Commits / Cocogitto：为后续自动生成 Changelog 和版本发布保留入口。
- Cookiecutter Hook：生成后校验项目名、按开关删除 CI 文件、初始化 Git，并可执行 `pnpm install`。

## 工程使用建议

### 中央化 Workflow

生成项目中的 `.github/workflows/` 只保留触发器和参数；具体步骤集中在 repo-scaffold 的可复用 Workflow 中。当前模板包含：

- `ci.yaml`：Pull Request 和主分支质量检查。
- `version-bump.yaml`：调用中央 Cocogitto 版本流程。
- `release.yaml`：在 Tag 或手动触发时调用中央 Electron 打包流程。

Electron 打包流程默认生成 Windows、macOS 和 Linux 的未签名产物，并上传到 GitHub Release。中央 Workflow 已预留可选的证书 Secrets 通道；没有 Secrets 时不会签名。签名、公证仍需项目显式配置，模板不强制开启。

可选 Secrets：`WIN_CSC_LINK`、`WIN_CSC_KEY_PASSWORD`、`MAC_CSC_LINK`、`MAC_CSC_KEY_PASSWORD`、`APPLE_API_KEY`、`APPLE_API_KEY_ID`、`APPLE_API_ISSUER`、`APPLE_TEAM_ID`。

### 统一的可复用 CI

业务项目只声明：

```yaml
lint-command: pnpm format:check
build-command: pnpm build
test-command: pnpm test
```

Node、pnpm、缓存和权限配置集中在可复用 Workflow 中；本地命令统一通过 `just` 调用。具体项目可以在此基础上增加 API、领域测试和 Electron 打包 Job。

### Monorepo 依赖边界

`packages/shared` 不依赖 Electron 或 React，`packages/ui` 只承载跨 Web/桌面的界面能力，Electron 主进程留在 `apps/desktop`。这样业务包可以独立演进，不会把桌面运行时依赖扩散到所有包。

### 生成模板时保持可选择性

`use_github_actions` 和 `install_after_generate` 让模板既能生成完整工程，也能生成适合离线学习的最小工程。敏感配置只生成 `.env.example`，不把凭据写入模板。

## 业务项目的扩展方式

具体业务项目应在生成的工作区中增加自己的业务层：

```text
apps/api
packages/project-domain
packages/project-runtime
packages/project-connectors
packages/project-policy
```

这样脚手架负责 Web/Electron 工程一致性，业务项目负责自身领域能力演进。
