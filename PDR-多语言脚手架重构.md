# PDR: 基于 Cookiecutter 的组件化脚手架重构

## 问题陈述

当前的 `repo-scaffold` 项目被设计为一个专注于 Python 项目的单体模板系统。它存在以下几个限制：

1. **单体模板设计**：所有功能都打包在单个模板中，缺乏细粒度控制
2. **定制化有限**：用户只能启用/禁用整个功能集，而不能选择单个组件
3. **重复代码**：不同模板间存在大量重复的配置和文件
4. **维护困难**：修改共同功能需要在多个模板中重复操作
5. **扩展性差**：添加新功能或模板类型需要大量重复工作

### 当前架构问题

- 模板功能耦合严重，无法独立重用
- 缺乏标准化的模板引擎，重新发明轮子
- 组件依赖关系没有明确管理
- 没有利用现有成熟的模板生态系统

## 决策

我们将把 `repo-scaffold` 项目重构为一个**基于 Cookiecutter 的组件化模板系统**，支持：

- 利用 Cookiecutter 的成熟模板引擎和生态系统
- 具有细粒度控制的模块化组件架构
- 组件重用和动态组合
- 运行时根据用户选择组合模板
- 保持配置简单直观，降低学习成本

## 需求

### 功能性需求

#### FR1: Cookiecutter 集成
- 基于 Cookiecutter 作为核心模板引擎
- 利用现有的 Cookiecutter 生态系统和最佳实践
- 保持与标准 Cookiecutter 模板的兼容性

#### FR2: 组件化架构
- 可独立开发和维护的模块化组件
- 组件间的依赖管理和冲突检测
- 运行时动态组合选定组件

#### FR3: 简化的配置系统
- 基于 YAML 的简单组件配置
- 直观的模板定义格式
- 最小化配置复杂性

#### FR4: 动态模板生成
- 根据用户选择动态组合 Cookiecutter 模板
- 自动处理组件文件合并和变量组合
- 临时模板生成和清理

#### FR5: 组件重用
- 跨模板类型的组件重用（如 GitHub Actions、Docker 等）
- 标准化的组件接口和文件结构
- 易于扩展的组件库

### 非功能性需求

#### NFR1: 简单性
- 降低学习曲线，易于理解和使用
- 最小化配置复杂性
- 利用用户已熟悉的 Cookiecutter 工作流

#### NFR2: 可扩展性
- 简单的组件创建和添加流程
- 标准化的组件接口
- 易于添加新的模板类型

#### NFR3: 用户体验
- 直观的 CLI 界面
- 清晰的组件选择过程
- 有用的错误消息和帮助信息

#### NFR4: 可维护性
- 清晰的关注点分离
- 组件独立性，便于维护
- 简化的代码结构
- 基本的配置验证

## 设计

### 架构概览

新架构基于 Cookiecutter，采用组件化设计：

```
┌─────────────────────────────────────────┐
│              CLI 层                     │
├─────────────────────────────────────────┤
│         模板组合器                       │
├─────────────────────────────────────────┤
│         组件管理器                       │
├─────────────────────────────────────────┤
│        Cookiecutter 引擎                │
├─────────────────────────────────────────┤
│           组件库                        │
└─────────────────────────────────────────┘
```

### 目录结构

```
repo_scaffold/
├── cli.py                          # CLI 入口（包装 Cookiecutter）
├── core/                           # 核心功能
│   ├── component_manager.py        # 组件管理器
│   ├── template_composer.py        # 模板组合器
│   └── cookiecutter_runner.py      # Cookiecutter 运行器
├── components/                     # 组件库
│   ├── python_core/                # Python 核心组件
│   │   ├── component.yaml          # 组件配置
│   │   ├── files/                  # 组件文件
│   │   │   ├── pyproject.toml.j2
│   │   │   ├── src/
│   │   │   ├── tests/
│   │   │   ├── README.md.j2
│   │   │   └── .gitignore
│   │   └── hooks/                  # 组件 hooks
│   │       └── post_gen_project.py
│   ├── cli_support/                # CLI 支持
│   │   ├── component.yaml
│   │   ├── files/
│   │   │   ├── cli.py.j2
│   │   │   └── cli_tests.py.j2
│   │   └── hooks/
│   ├── web_framework/              # Web 框架
│   │   ├── component.yaml
│   │   ├── files/
│   │   └── hooks/
│   ├── docker/                     # Docker 支持
│   │   ├── component.yaml
│   │   ├── files/
│   │   │   ├── Dockerfile.j2
│   │   │   └── docker-compose.yml.j2
│   │   └── hooks/
│   ├── github_actions/             # CI/CD
│   │   ├── component.yaml
│   │   ├── files/
│   │   │   ├── test.yml.j2
│   │   │   └── release.yml.j2
│   │   └── hooks/
│   └── documentation/              # 文档系统
│       ├── component.yaml
│       ├── files/
│       │   ├── mkdocs.yml.j2
│       │   └── docs/
│       └── hooks/
├── templates/                      # 模板定义
│   ├── python-library.yaml         # 库项目模板
│   ├── python-cli.yaml             # CLI 项目模板
│   └── python-web.yaml             # Web 项目模板
└── temp/                           # 临时生成的 Cookiecutter 模板
```

### 核心组件

#### 组件管理器

`ComponentManager` 处理组件发现和依赖解析：

```python
class ComponentManager:
    def discover_components(self) -> Dict[str, Component]
    def resolve_dependencies(self, selected: List[str]) -> List[str]
    def validate_selection(self, selected: List[str]) -> List[str]
```

#### 模板组合器

`TemplateComposer` 负责动态组合 Cookiecutter 模板：

```python
class TemplateComposer:
    def compose_template(self, template_config: dict, selected_components: List[str]) -> Path
    def _build_cookiecutter_config(self, template_config: dict, components: List[str]) -> dict
    def _merge_component_files(self, components: List[str], target_dir: Path)
    def _create_hooks(self, components: List[str], temp_dir: Path)
```

#### Cookiecutter 运行器

`CookiecutterRunner` 包装 Cookiecutter 调用：

```python
class CookiecutterRunner:
    def run_cookiecutter(self, template_dir: Path, output_dir: Path = None) -> Path
    def cleanup_temp_template(self, template_dir: Path)
```

### 配置格式

#### 组件配置

每个组件在 `component.yaml` 文件中定义其元数据和行为：

```yaml
# components/cli_support/component.yaml
name: cli_support
display_name: CLI Support
description: Adds Click-based command line interface support
category: feature

# 组件依赖
dependencies:
  - python_core

# 冲突组件
conflicts: []

# Cookiecutter 变量贡献
cookiecutter_vars:
  use_cli: true
  cli_framework: click

# 文件映射
files:
  - src: "cli_module.py.j2"
    dest: "src/{{cookiecutter.package_name}}/cli.py"
  - src: "cli_tests.py.j2"
    dest: "tests/test_cli.py"

# 依赖包
dependencies_to_add:
  - click>=8.0.0
  - rich>=10.0.0

# 开发依赖
dev_dependencies_to_add:
  - pytest-click

# Hooks
hooks:
  post_gen:
    - update_pyproject_toml
    - add_cli_entry_point
```

#### 模板配置

每个模板在 YAML 文件中定义其可用的组件选项：

```yaml
# templates/python-library.yaml
name: python-library
display_name: Python Library
description: Create a Python library project

# 必需组件
required_components:
  - python_core

# 可选组件及其配置
optional_components:
  cli_support:
    prompt: "Add CLI support?"
    help: "Adds Click-based command line interface"
    default: false

  docker:
    prompt: "Add Docker support?"
    help: "Includes Dockerfile and docker-compose.yml"
    default: false

  github_actions:
    prompt: "Add GitHub Actions CI/CD?"
    help: "Automated testing and release workflows"
    default: true

  documentation:
    prompt: "Add documentation?"
    help: "MkDocs-based documentation system"
    default: true

# 基础 Cookiecutter 配置
base_cookiecutter_config:
  project_name: "My Python Library"
  package_name: "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}"
  author_name: "Your Name"
  author_email: "your.email@example.com"
  version: "0.1.0"
  description: "A short description of the project"
  license: ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
  python_version: "3.12"
```



### 模板生成流程

1. **模板选择**：用户选择目标模板类型
2. **模板配置加载**：加载模板的 YAML 配置文件
3. **组件交互选择**：基于模板配置，用户交互式选择组件
   - 显示每个可选组件的描述和默认值
   - 用户通过简单的 Y/N 问题选择组件
4. **依赖解析**：系统自动解析组件依赖关系
5. **冲突检测**：检查组件间是否存在冲突
6. **模板组合**：动态组合选定的组件为 Cookiecutter 模板
   - 合并组件文件
   - 组合 cookiecutter.json 配置
   - 创建组合的 hooks
7. **Cookiecutter 执行**：调用 Cookiecutter 生成项目
8. **清理**：删除临时生成的模板文件

### CLI 界面

```bash
# 列出可用模板
repo-scaffold list

# 交互式创建项目
repo-scaffold create

# 使用特定模板创建项目
repo-scaffold create --template python-library

# 列出可用组件
repo-scaffold components

# 查看特定模板的配置
repo-scaffold show python-library
```

### 使用示例

```bash
$ repo-scaffold create --template python-library

? Add CLI support? (Adds Click-based command line interface) [y/N]: y
? Add Docker support? (Includes Dockerfile and docker-compose.yml) [y/N]: n
? Add GitHub Actions CI/CD? (Automated testing and release workflows) [Y/n]: y
? Add documentation? (MkDocs-based documentation system) [Y/n]: y

# 然后进入标准的 Cookiecutter 提示
project_name [My Python Library]: My Awesome Library
author_name [Your Name]: John Doe
author_email [your.email@example.com]: john@example.com
...

✨ Project created successfully!
```

## 风险和缓解措施

### 风险 1: Cookiecutter 依赖
**风险**：依赖外部库可能带来兼容性问题。
**缓解措施**：
- 使用稳定版本的 Cookiecutter
- 定期测试兼容性
- 考虑将来可能的替代方案

### 风险 2: 临时文件管理
**风险**：动态生成的临时模板可能导致磁盘空间或清理问题。
**缓解措施**：
- 实施可靠的临时文件清理机制
- 使用 Python 的 tempfile 模块确保自动清理
- 添加错误处理确保异常情况下也能清理

### 风险 3: 组件复杂性增长
**风险**：随着组件数量增加，依赖关系可能变得复杂。
**缓解措施**：
- 保持组件设计简单
- 建立明确的组件开发指南
- 定期审查和重构组件依赖关系

### 风险 4: 用户学习成本
**风险**：用户需要学习新的组件概念。
**缓解措施**：
- 提供清晰的文档和示例
- 保持组件选择界面简单直观
- 提供合理的默认值

## 成功标准

1. **Cookiecutter 集成**：成功集成 Cookiecutter 作为模板引擎
2. **组件模块化**：用户可以选择单个组件并正确解析依赖关系
3. **组件重用**：组件可以在不同模板类型间重用
4. **动态模板生成**：根据选定的组件动态生成 Cookiecutter 模板
5. **简化配置**：配置文件简单易懂，易于维护
6. **用户体验**：CLI 界面直观，组件选择过程清晰
7. **性能**：模板生成速度快，临时文件管理高效
8. **可扩展性**：易于添加新组件和模板类型

## 实施计划

### 阶段 1：核心功能 (2-3 周)
- 实现组件管理器和模板组合器
- 创建 3-4 个基础组件（python_core, cli_support, docker, github_actions）
- 实现基本的 CLI 界面
- 创建 2-3 个模板类型（library, cli, web）

### 阶段 2：增强功能 (1-2 周)
- 添加更多组件（documentation, testing, linting）
- 改进用户体验和错误处理
- 添加基本的配置验证
- 完善文档和示例

### 阶段 3：优化和扩展 (1 周)
- 性能优化
- 添加更多模板类型
- 社区反馈集成
- 测试覆盖完善

## 未来考虑

- **多语言扩展**：基于当前架构添加其他语言支持
- **组件市场**：社区贡献的组件库
- **IDE 集成**：VS Code 扩展支持
- **配置预设**：常见用例的预定义组件组合
- **高级依赖管理**：更复杂的组件依赖关系处理
