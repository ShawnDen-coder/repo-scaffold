"""Template registry and rendering tests."""

import json
import re
import subprocess
import tomllib
from pathlib import Path
from unittest.mock import Mock

import json5
from click.testing import CliRunner
from cookiecutter.main import cookiecutter

from repo_scaffold.cli import cli
from repo_scaffold.cli import get_package_path
from repo_scaffold.cli import load_templates


def _load_cookiecutter_config(template_name: str) -> dict:
    config_path = Path(get_package_path(f"templates/{template_name}/cookiecutter.json"))
    return json.loads(config_path.read_text(encoding="utf-8"))


def test_template_registry_entries_exist():
    """Test registered templates have required metadata and directories."""
    templates = load_templates()

    assert "template-python" in templates
    assert "template-uv-workspace" in templates
    assert "template-pnpm-workspace" in templates
    assert "template-electron-workspace" in templates
    assert "template-ts-sdk" in templates
    assert "template-vue-project" in templates

    assert "template-ts-cli" in templates
    titles = [info["title"] for info in templates.values()]
    assert len(titles) == len(set(titles))

    for info in templates.values():
        assert set(info) >= {"path", "title", "description"}
        template_dir = Path(get_package_path(f"templates/{info['path']}"))
        assert template_dir.is_dir()
        assert (template_dir / "cookiecutter.json").is_file()


def test_cli_list_includes_registered_templates():
    """Test list command includes available template titles."""
    result = CliRunner().invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "python" in result.output
    assert "uv-workspace" in result.output
    assert "pnpm-workspace" in result.output
    assert "electron-workspace" in result.output
    assert "ts-sdk" in result.output
    assert "vue-project" in result.output

    assert "ts-cli" in result.output

def test_template_question_defaults_are_user_friendly():
    """Test template prompt defaults and question metadata stay intentional."""
    python_config = _load_cookiecutter_config("template-python")
    workspace_config = _load_cookiecutter_config("template-uv-workspace")

    for config in (python_config, workspace_config):
        assert config["full_name"] == "Your Name"
        assert config["email"] == "you@example.com"
        assert config["github_username"] == "your-github-username"
        assert config["pypi_server_url"] == ""
        assert config["install_after_generate"] == "yes"
        assert config["init_git"] == "yes"
        assert config["use_github_actions"] == ["yes", "no"]
        assert config["min_python_version"][0] == "3.12"
        assert config["max_python_version"][0] == "3.12"
        assert {"full_name", "email", "github_username", "pypi_server_url"} <= set(config["__prompts__"])

    assert python_config["use_podman"] == ["no", "yes"]
    assert python_config["include_cli"] == ["yes", "no"]


def test_cli_create_resolves_template_key_and_title(monkeypatch, tmp_path):
    """Test create command resolves both registry key and template title."""
    calls = []
    mock_cookiecutter = Mock(side_effect=lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("repo_scaffold.cli.cookiecutter", mock_cookiecutter)

    runner = CliRunner()
    by_key = runner.invoke(cli, ["create", "template-uv-workspace", "--no-input", "-o", str(tmp_path)])
    by_title = runner.invoke(cli, ["create", "uv-workspace", "--no-input", "-o", str(tmp_path), "--no-install"])

    assert by_key.exit_code == 0
    assert by_title.exit_code == 0
    assert len(calls) == 2
    assert all(call["no_input"] is True for call in calls)
    assert all(call["output_dir"] == str(tmp_path) for call in calls)
    assert all(call["template"].endswith("template-uv-workspace") for call in calls)
    assert calls[0]["extra_context"] == {"install_after_generate": "yes", "init_git": "yes"}
    assert calls[1]["extra_context"] == {"install_after_generate": "no", "init_git": "yes"}


def test_cli_create_no_git_sets_extra_context(monkeypatch, tmp_path):
    """``--no-git`` flips the init_git extra_context value to 'no'."""
    calls = []
    mock_cookiecutter = Mock(side_effect=lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("repo_scaffold.cli.cookiecutter", mock_cookiecutter)

    result = CliRunner().invoke(cli, ["create", "template-python", "--no-input", "--no-git", "-o", str(tmp_path)])

    assert result.exit_code == 0
    assert calls[0]["extra_context"]["init_git"] == "no"


def _render_template(
    template_name: str,
    tmp_path: Path,
    extra_context: dict[str, str] | None = None,
    accept_hooks: bool = False,
) -> Path:
    template_dir = Path(get_package_path(f"templates/{template_name}"))
    return Path(
        cookiecutter(
            str(template_dir),
            output_dir=str(tmp_path),
            no_input=True,
            accept_hooks=accept_hooks,
            extra_context=extra_context,
        )
    )


def _assert_no_unrendered_markers(project_dir: Path) -> None:
    markers = ("{{ cookiecutter", "{{cookiecutter", "{% raw %}", "{% endraw %}")
    for path in project_dir.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert not any(marker in text for marker in markers), path


def _assert_no_task_runner_references(project_dir: Path) -> None:
    assert not (project_dir / "Taskfile.yml").exists()
    assert (project_dir / "justfile").is_file()

    workflow_dir = project_dir / ".github" / "workflows"
    if not workflow_dir.exists():
        return

    for path in workflow_dir.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "setup-task" not in text
        assert "run: task" not in text
        assert " task " not in text


def _assert_pyproject_files_parse(project_dir: Path) -> None:
    for path in project_dir.rglob("pyproject.toml"):
        with path.open("rb") as f:
            tomllib.load(f)


def _assert_justfile_parses(project_dir: Path) -> None:
    result = subprocess.run(
        ["uvx", "--from", "rust-just", "just", "--justfile", str(project_dir / "justfile"), "--list"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "test-all" in result.stdout


def _assert_workflows_have_github_expressions(project_dir: Path) -> None:
    workflow_dir = project_dir / ".github" / "workflows"
    if not workflow_dir.exists():
        return

    workflows = list(workflow_dir.glob("*.yaml"))
    assert workflows
    assert any("${{" in path.read_text(encoding="utf-8") for path in workflows)


def _assert_version_bump_avoids_self_trigger(project_dir: Path) -> None:
    version_bump = project_dir / ".github" / "workflows" / "version-bump.yaml"
    if not version_bump.exists():
        return

    text = version_bump.read_text(encoding="utf-8")
    assert "!startsWith(github.event.head_commit.message, 'chore(version):')" in text
    assert "release-version:" in text
    assert "cog bump --version \"$RELEASE_VERSION\"" in text


def _assert_cog_does_not_require_existing_tag(project_dir: Path) -> None:
    cog_config = project_dir / "cog.toml"
    if not cog_config.exists():
        return

    assert "from_latest_tag" not in cog_config.read_text(encoding="utf-8")


def _assert_cog_pushes_tags_explicitly(project_dir: Path) -> None:
    cog_config = project_dir / "cog.toml"
    if not cog_config.exists():
        return

    text = cog_config.read_text(encoding="utf-8")
    assert '"git push"' in text
    assert "git push origin " in text or '"git push --tags"' in text
    assert "git push --follow-tags" not in text


def _assert_static_project_valid(project_dir: Path) -> None:
    _assert_no_task_runner_references(project_dir)
    _assert_no_unrendered_markers(project_dir)
    _assert_pyproject_files_parse(project_dir)
    _assert_justfile_parses(project_dir)
    _assert_workflows_have_github_expressions(project_dir)
    _assert_version_bump_avoids_self_trigger(project_dir)
    _assert_cog_does_not_require_existing_tag(project_dir)
    _assert_cog_pushes_tags_explicitly(project_dir)


def test_template_python_renders_with_justfile(tmp_path):
    """Test existing Python template renders with justfile commands."""
    project_dir = _render_template("template-python", tmp_path)

    assert (project_dir / "pyproject.toml").is_file()
    assert (project_dir / "justfile").is_file()
    assert (project_dir / ".github" / "workflows" / "ci-tests.yaml").is_file()
    workflow_dir = project_dir / ".github" / "workflows"
    ci = (workflow_dir / "ci-tests.yaml").read_text(encoding="utf-8")
    version_bump = (workflow_dir / "version-bump.yaml").read_text(encoding="utf-8")
    package_release = (workflow_dir / "package-release.yaml").read_text(encoding="utf-8")
    docs_deploy = (workflow_dir / "docs-deploy.yaml").read_text(encoding="utf-8")
    assert "reusable-python-ci.yaml@" in ci
    assert "workspace: false" in ci
    assert "uses: ./.github/workflows/package-release.yaml" in version_bump
    assert "tag: ${{ needs.release.outputs.tag }}" in version_bump
    assert "workflow_call:" in package_release
    assert "reusable-python-release.yaml@" in package_release
    assert "workspace: false" in package_release
    assert "workflow_call:" in docs_deploy
    assert "reusable-docs-deploy.yaml@" in docs_deploy
    with (project_dir / "pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)
    assert pyproject["project"]["urls"]["Repository"].startswith("https://github.com/")
    _assert_static_project_valid(project_dir)


def test_template_python_renders_reusable_container_release(tmp_path):
    """Podman-enabled Python projects wire the container release workflow."""
    project_dir = _render_template(
        "template-python",
        tmp_path,
        {"use_podman": "yes", "install_after_generate": "no"},
        accept_hooks=True,
    )

    workflow_dir = project_dir / ".github" / "workflows"
    ci = (workflow_dir / "ci-tests.yaml").read_text(encoding="utf-8")
    package_release = (workflow_dir / "package-release.yaml").read_text(encoding="utf-8")
    container_release = (workflow_dir / "container-release.yaml").read_text(encoding="utf-8")
    assert "test-container: true" in ci
    assert "publish-container: ${{ inputs.publish_container }}" in package_release
    assert "workflow_call:" in container_release
    assert (
        "reusable-container-release.yaml@"
        in container_release
    )
    assert "containerfile: ./container/Dockerfile" in container_release
    assert "push-latest: ${{ inputs.push_latest }}" in container_release
    assert "PYPI_SERVER_PASSWORD: ${{ secrets.PYPI_SERVER_PASSWORD }}" in container_release
    _assert_static_project_valid(project_dir)


def test_template_python_can_render_without_github_actions(tmp_path):
    """Test Python template can omit GitHub Actions and docs."""
    project_dir = _render_template(
        "template-python",
        tmp_path,
        {"use_github_actions": "no", "install_after_generate": "no"},
        accept_hooks=True,
    )

    assert not (project_dir / ".github").exists()
    assert not (project_dir / "docs").exists()
    assert not (project_dir / "mkdocs.yml").exists()
    _assert_static_project_valid(project_dir)


def test_template_uv_workspace_renders(tmp_path):
    """Test uv workspace template renders expected files."""
    project_dir = _render_template("template-uv-workspace", tmp_path)
    package_dir = project_dir / "packages" / "my-uv-workspace-core"

    assert (project_dir / "pyproject.toml").is_file()
    assert (project_dir / "justfile").is_file()
    assert (project_dir / ".github" / "workflows" / "ci-tests.yaml").is_file()
    assert (package_dir / "pyproject.toml").is_file()
    assert (package_dir / "src" / "my_uv_workspace_core" / "__init__.py").is_file()
    assert (package_dir / "tests" / "test_import.py").is_file()

    workflow_dir = project_dir / ".github" / "workflows"
    ci = (workflow_dir / "ci-tests.yaml").read_text(encoding="utf-8")
    version_bump = (workflow_dir / "version-bump.yaml").read_text(encoding="utf-8")
    package_release = (workflow_dir / "package-release.yaml").read_text(encoding="utf-8")
    docs_deploy = (workflow_dir / "docs-deploy.yaml").read_text(encoding="utf-8")
    assert "reusable-python-ci.yaml@" in ci
    assert "workspace: true" in ci
    assert "uses: ./.github/workflows/package-release.yaml" in version_bump
    assert "tag: ${{ needs.release.outputs.tag }}" in version_bump
    assert "workflow_call:" in package_release
    assert "reusable-python-release.yaml@" in package_release
    assert "workspace: true" in package_release
    assert "workflow_call:" in docs_deploy
    assert "reusable-docs-deploy.yaml@" in docs_deploy

    with (project_dir / "pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)
    assert pyproject["tool"]["uv"]["package"] is False
    assert pyproject["tool"]["uv"]["workspace"]["members"] == ["packages/*"]
    assert pyproject["project"]["urls"]["Repository"].startswith("https://github.com/")

    # mkdocstrings discovers workspace packages via sys.path (installed by `uv run --all-packages`),
    # so no explicit `paths` entry is needed — adding new packages requires no mkdocs config change.
    mkdocs = (project_dir / "mkdocs.yml").read_text(encoding="utf-8")
    assert "paths:" not in mkdocs

    _assert_static_project_valid(project_dir)


def test_template_uv_workspace_can_render_without_github_actions(tmp_path):
    """Test uv workspace template can omit GitHub Actions and docs."""
    project_dir = _render_template(
        "template-uv-workspace",
        tmp_path,
        {"use_github_actions": "no", "install_after_generate": "no"},
        accept_hooks=True,
    )

    assert not (project_dir / ".github").exists()
    assert not (project_dir / "docs").exists()
    assert not (project_dir / "mkdocs.yml").exists()
    _assert_static_project_valid(project_dir)


def test_python_post_gen_hook_uses_project_root_and_can_skip_install(monkeypatch, tmp_path):
    """Test Python hook initializes from project root and honors install toggle."""
    monkeypatch.chdir(tmp_path)
    hook_path = Path(get_package_path("templates/template-python/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.project_slug}}"', '"demo"')
    source = source.replace('"{{cookiecutter.min_python_version}}"', '"3.12"')
    source = source.replace('"{{cookiecutter.max_python_version}}"', '"3.12"')
    source = source.replace('"{{cookiecutter.include_cli}}"', '"yes"')
    source = source.replace('"{{cookiecutter.use_github_actions}}"', '"yes"')
    source = source.replace('"{{cookiecutter.use_podman}}"', '"yes"')
    source = source.replace('"{{cookiecutter.install_after_generate}}"', '"no"')

    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    initializer = namespace["ProjectInitializer"]()
    initializer.setup_environment()


def test_python_post_gen_hook_inits_git_on_master(monkeypatch, tmp_path):
    """Test Python hook runs ``git init`` on branch master when init_git is yes."""
    monkeypatch.chdir(tmp_path)
    hook_path = Path(get_package_path("templates/template-python/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.install_after_generate}}"', '"no"')
    source = source.replace('"{{cookiecutter.init_git}}"', '"yes"')

    calls = []

    def fake_run(command, check, **kwargs):
        calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    monkeypatch.setattr(namespace["subprocess"], "run", fake_run)

    namespace["ProjectInitializer"]().init_git_repo()

    assert calls == [["git", "init", "-b", "master"]]


def test_python_post_gen_hook_skips_git_when_disabled(monkeypatch, tmp_path):
    """Test Python hook skips git init entirely when init_git is no."""
    monkeypatch.chdir(tmp_path)
    hook_path = Path(get_package_path("templates/template-python/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.init_git}}"', '"no"')

    calls = []
    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    monkeypatch.setattr(namespace["subprocess"], "run", lambda *a, **k: calls.append(a))

    namespace["ProjectInitializer"]().init_git_repo()

    assert calls == []
    """Test workspace hook invokes uv sync from the current project root."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '0.1.0'\n", encoding="utf-8")
    calls = []

    def fake_run(command, check):
        calls.append((command, check, Path.cwd()))

    hook_path = Path(get_package_path("templates/template-uv-workspace/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.project_slug}}"', '"demo"')
    source = source.replace('"{{cookiecutter.package_slug}}"', '"demo-core"')
    source = source.replace('"{{cookiecutter.package_module}}"', '"demo_core"')
    source = source.replace('"{{cookiecutter.min_python_version}}"', '"3.12"')
    source = source.replace('"{{cookiecutter.max_python_version}}"', '"3.12"')
    source = source.replace('"{{cookiecutter.use_github_actions}}"', '"yes"')
    source = source.replace('"{{cookiecutter.install_after_generate}}"', '"yes"')

    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    monkeypatch.setattr(namespace["subprocess"], "run", fake_run)

    initializer = namespace["ProjectInitializer"]()
    initializer.setup_environment()


def test_python_post_gen_hook_rejects_invalid_version_range():
    """Test Python hook rejects impossible Python support ranges."""
    hook_path = Path(get_package_path("templates/template-python/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.project_slug}}"', '"demo"')
    source = source.replace('"{{cookiecutter.min_python_version}}"', '"3.14"')
    source = source.replace('"{{cookiecutter.max_python_version}}"', '"3.12"')

    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    validator = namespace["ProjectValidator"]()

    try:
        validator.validate()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected invalid version range to exit")


def test_workspace_post_gen_hook_rejects_invalid_module_name():
    """Test workspace hook rejects invalid generated module names."""
    hook_path = Path(get_package_path("templates/template-uv-workspace/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.project_slug}}"', '"demo"')
    source = source.replace('"{{cookiecutter.package_slug}}"', '"demo-core"')
    source = source.replace('"{{cookiecutter.package_module}}"', '"123_bad"')
    source = source.replace('"{{cookiecutter.min_python_version}}"', '"3.12"')
    source = source.replace('"{{cookiecutter.max_python_version}}"', '"3.12"')

    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    validator = namespace["ProjectValidator"]()

    try:
        validator.validate()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected invalid module name to exit")


# ---------------------------------------------------------------------------
# ts-sdk template tests
# ---------------------------------------------------------------------------


def test_template_ts_sdk_renders(tmp_path):
    """Test ts-sdk template renders expected files."""
    project_dir = _render_template(
        "template-ts-sdk",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )

    assert (project_dir / "package.json").is_file()
    assert (project_dir / "vite.config.ts").is_file()
    assert (project_dir / ".github" / "workflows" / "ci.yaml").is_file()
    assert (project_dir / "tsconfig.json").is_file()
    assert (project_dir / ".prettierrc.json").is_file()
    assert (project_dir / "src" / "index.ts").is_file()
    assert (project_dir / "src" / "client.ts").is_file()
    assert (project_dir / "src" / "auth.ts").is_file()
    assert (project_dir / "src" / "logger.ts").is_file()
    assert (project_dir / "src" / "types" / "index.ts").is_file()
    assert (project_dir / ".github" / "workflows" / "ci.yaml").is_file()
    assert (project_dir / "cog.toml").is_file()

    _assert_no_unrendered_markers(project_dir)


def test_template_ts_sdk_can_render_without_github_actions(tmp_path):
    """Test ts-sdk template can omit GitHub Actions."""
    project_dir = _render_template(
        "template-ts-sdk",
        tmp_path,
        {"use_github_actions": "no", "install_after_generate": "no"},
        accept_hooks=True,
    )

    assert not (project_dir / ".github").exists()
    assert not (project_dir / "cog.toml").exists()
    _assert_no_unrendered_markers(project_dir)


# ---------------------------------------------------------------------------
# pnpm-workspace template tests
# ---------------------------------------------------------------------------


def test_template_pnpm_workspace_renders_vue_app(tmp_path):
    """Test pnpm-workspace template renders with vue-app sub-package."""
    project_dir = _render_template(
        "template-pnpm-workspace",
        tmp_path,
        {"initial_package_type": "vue-app", "install_after_generate": "no"},
        accept_hooks=True,
    )

    # Root files
    assert (project_dir / "package.json").is_file()
    assert (project_dir / "pnpm-workspace.yaml").is_file()
    assert (project_dir / "justfile").is_file()
    assert (project_dir / ".prettierrc.json").is_file()

    # Sub-package: vue-app variant selected
    package_dir = project_dir / "packages" / "my-pnpm-workspace-core"
    assert (package_dir / "package.json").is_file()
    config = (project_dir / ".repo-scaffold.toml").read_text(encoding="utf-8")
    justfile = (project_dir / "justfile").read_text(encoding="utf-8")
    assert 'repo_scaffold_version = "1.0.0"' in config
    assert "just add-member" in justfile
    assert 'plan-member name member_type="ts-lib"' in justfile
    assert "repo-scaffold==1.0.0" in justfile
    assert (package_dir / "index.html").is_file()
    assert (package_dir / "src" / "main.ts").is_file()
    assert (package_dir / "src" / "App.vue").is_file()
    assert (package_dir / "vite.config.ts").is_file()
    cog = (project_dir / "cog.toml").read_text(encoding="utf-8")
    assert "[packages.my-pnpm-workspace-core]" in cog
    assert "pnpm --filter my-pnpm-workspace-core version {{version}}" in cog

    _assert_no_unrendered_markers(project_dir)


def test_template_pnpm_workspace_renders_ts_lib(tmp_path):
    """Test pnpm-workspace template renders with ts-lib sub-package."""
    project_dir = _render_template(
        "template-pnpm-workspace",
        tmp_path,
        {"initial_package_type": "ts-lib", "install_after_generate": "no"},
        accept_hooks=True,
    )

    package_dir = project_dir / "packages" / "my-pnpm-workspace-core"
    assert (package_dir / "package.json").is_file()
    assert (package_dir / "tsconfig.json").is_file()
    assert (package_dir / "src" / "index.ts").is_file()

    # vue-app specific files should NOT be present
    assert not (package_dir / "index.html").exists()
    assert not (package_dir / "src" / "App.vue").exists()

    _assert_no_unrendered_markers(project_dir)


def test_template_pnpm_workspace_renders_react_app(tmp_path):
    """Test pnpm-workspace template renders with react-app sub-package."""
    project_dir = _render_template(
        "template-pnpm-workspace",
        tmp_path,
        {"initial_package_type": "react-app", "install_after_generate": "no"},
        accept_hooks=True,
    )

    package_dir = project_dir / "packages" / "my-pnpm-workspace-core"
    assert (package_dir / "package.json").is_file()
    assert (package_dir / "index.html").is_file()
    assert (package_dir / "src" / "main.tsx").is_file()
    assert (package_dir / "src" / "App.tsx").is_file()

    # vue-app specific files should NOT be present
    assert not (package_dir / "src" / "App.vue").exists()

    _assert_no_unrendered_markers(project_dir)


def test_template_pnpm_workspace_can_render_without_github_actions(tmp_path):
    """Test pnpm-workspace template can omit GitHub Actions."""
    project_dir = _render_template(
        "template-pnpm-workspace",
        tmp_path,
        {
            "use_github_actions": "no",
            "initial_package_type": "ts-lib",
            "install_after_generate": "no",
        },
        accept_hooks=True,
    )

    assert not (project_dir / ".github").exists()
    assert not (project_dir / "cog.toml").exists()
    _assert_no_unrendered_markers(project_dir)


def test_template_electron_workspace_renders_web_desktop_and_shared_packages(tmp_path):
    """The Electron workspace template renders the intended app/package boundaries."""
    project_dir = _render_template(
        "template-electron-workspace",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )

    assert (project_dir / "pnpm-workspace.yaml").is_file()
    assert (project_dir / "justfile").is_file()
    assert (project_dir / "cog.toml").is_file()
    assert (project_dir / "apps" / "web" / "package.json").is_file()
    assert (project_dir / "apps" / "desktop" / "main.cjs").is_file()
    assert (project_dir / "packages" / "shared" / "src" / "index.ts").is_file()
    assert (project_dir / "packages" / "ui" / "src" / "index.tsx").is_file()

    workflow = project_dir / ".github" / "workflows" / "ci.yaml"
    assert workflow.is_file()
    config = (project_dir / ".repo-scaffold.toml").read_text(encoding="utf-8")
    justfile = (project_dir / "justfile").read_text(encoding="utf-8")
    assert 'repo_scaffold_version = "1.0.0"' in config
    assert "just add-member" in justfile
    assert 'plan-member name member_type="ts-lib"' in justfile
    assert "repo-scaffold==1.0.0" in justfile
    assert "reusable-electron-ci.yaml" in workflow.read_text(encoding="utf-8")
    assert (project_dir / ".github" / "workflows" / "version-bump.yaml").is_file()
    assert (project_dir / ".github" / "workflows" / "release.yaml").is_file()
    renovate = json5.loads((project_dir / ".github" / "renovate.json5").read_text(encoding="utf-8"))
    assert renovate["$schema"].endswith("renovate-schema.json")
    assert renovate["enabledManagers"] == ["npm", "github-actions"]
    assert any(rule.get("groupName") == "electron packages" for rule in renovate["packageRules"])
    assert (project_dir / "electron-builder.yml").is_file()
    _assert_no_unrendered_markers(project_dir)


def test_template_electron_workspace_can_omit_devops_files(tmp_path):
    """Optional GitHub automation is removed when explicitly disabled."""
    project_dir = _render_template(
        "template-electron-workspace",
        tmp_path,
        {"use_github_actions": "no", "install_after_generate": "no"},
        accept_hooks=True,
    )

    assert not (project_dir / ".github").exists()
    assert not (project_dir / "renovate.json5").exists()
    assert not (project_dir / "cog.toml").exists()


def test_template_electron_workspace_uses_master_default_branch(tmp_path):
    """CI and release triggers use the fixed master default branch."""
    project_dir = _render_template(
        "template-electron-workspace",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )

    ci = (project_dir / ".github" / "workflows" / "ci.yaml").read_text(encoding="utf-8")
    version_bump = (project_dir / ".github" / "workflows" / "version-bump.yaml").read_text(encoding="utf-8")
    assert "branches: [master]" in ci
    assert "branches: [master]" in version_bump


def test_template_electron_workspace_does_not_prompt_for_default_branch():
    """The Electron template keeps master as an implementation default."""
    config = _load_cookiecutter_config("template-electron-workspace")

    assert "default_branch" not in config
    assert "default_branch" not in config["__prompts__"]


def test_template_electron_workspace_hook_resolves_pnpm_command(monkeypatch):
    """The hook executes the resolved pnpm shim so Windows pnpm.cmd works."""
    hook_path = Path(get_package_path("templates/template-electron-workspace/hooks/post_gen_project.py"))
    source = hook_path.read_text(encoding="utf-8")
    source = source.replace('"{{cookiecutter.install_after_generate}}"', '"yes"')

    namespace = {"__name__": "hook_under_test"}
    exec(compile(source, str(hook_path), "exec"), namespace)
    pnpm_path = r"C:\Users\example\AppData\Roaming\npm\pnpm.CMD"
    calls = []
    monkeypatch.setattr(namespace["shutil"], "which", lambda command: pnpm_path)
    monkeypatch.setattr(namespace["subprocess"], "run", lambda command, check: calls.append((command, check)))

    namespace["install"]()

    assert calls == [([pnpm_path, "install"], True)]


# ---------------------------------------------------------------------------
# vue-project template tests
# ---------------------------------------------------------------------------


def _assert_shared_fragments_removed(project_dir: Path) -> None:
    """Shared workflow fragments under ``_shared/`` are cleaned up by the hook."""
    assert not (project_dir / "_shared").exists()


def test_template_vue_project_renders(tmp_path):
    """Test vue-project template renders expected files with full layered structure."""
    project_dir = _render_template(
        "template-vue-project",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )

    # Root files
    assert (project_dir / "package.json").is_file()
    assert (project_dir / "index.html").is_file()
    assert (project_dir / "vite.config.ts").is_file()
    assert (project_dir / ".github" / "workflows" / "ci.yaml").is_file()
    assert (project_dir / "tsconfig.json").is_file()
    assert (project_dir / "tsconfig.app.json").is_file()
    assert (project_dir / "tsconfig.node.json").is_file()
    assert (project_dir / ".prettierrc.json").is_file()

    # src/ entry points
    assert (project_dir / "src" / "main.ts").is_file()
    assert (project_dir / "src" / "App.vue").is_file()
    assert (project_dir / "src" / "style.css").is_file()

    # router + stores
    assert (project_dir / "src" / "router" / "index.ts").is_file()
    assert (project_dir / "src" / "router" / "router.ts").is_file()
    assert (project_dir / "src" / "stores" / "index.ts").is_file()
    assert (project_dir / "src" / "stores" / "app.ts").is_file()

    # components layered structure
    assert (project_dir / "src" / "components" / "ui" / "AppButton.vue").is_file()
    assert (project_dir / "src" / "components" / "ui" / "AppCard.vue").is_file()
    assert (project_dir / "src" / "components" / "layout" / "AppHeader.vue").is_file()
    assert (project_dir / "src" / "components" / "layout" / "AppFooter.vue").is_file()
    assert (project_dir / "src" / "components" / "common" / "EmptyState.vue").is_file()
    assert (project_dir / "src" / "components" / "common" / "FolderTree.vue").is_file()

    # pages
    assert (project_dir / "src" / "pages" / "HomePage" / "index.vue").is_file()
    assert (project_dir / "src" / "pages" / "HomePage" / "HeroSection.vue").is_file()
    assert (project_dir / "src" / "pages" / "HomePage" / "StructureHighlights.vue").is_file()
    assert (project_dir / "src" / "pages" / "AboutPage" / "index.vue").is_file()

    # GitHub Actions + cog
    assert (project_dir / ".github" / "workflows" / "ci.yaml").is_file()
    assert (project_dir / ".github" / "workflows" / "version-bump.yaml").is_file()
    assert (project_dir / "cog.toml").is_file()

    # _shared/ fragments cleaned up by hook
    _assert_shared_fragments_removed(project_dir)
    _assert_no_unrendered_markers(project_dir)


def test_template_vue_project_can_render_without_github_actions(tmp_path):
    """Test vue-project template can omit GitHub Actions."""
    project_dir = _render_template(
        "template-vue-project",
        tmp_path,
        {"use_github_actions": "no", "install_after_generate": "no"},
        accept_hooks=True,
    )

    assert not (project_dir / ".github").exists()
    assert not (project_dir / "cog.toml").exists()
    _assert_shared_fragments_removed(project_dir)
    _assert_no_unrendered_markers(project_dir)


# ---------------------------------------------------------------------------
# shared workflow fragment tests (pnpm templates)
# ---------------------------------------------------------------------------


def test_pnpm_templates_clean_shared_fragments(tmp_path):
    """All pnpm templates must remove the _shared/ directory after rendering."""
    for template_name, extra in (
        ("template-ts-sdk", {}),
        ("template-pnpm-workspace", {"initial_package_type": "ts-lib"}),
        ("template-react", {}),
    ):
        extra_context = {"install_after_generate": "no", **extra}
        project_dir = _render_template(
            template_name,
            tmp_path / template_name,
            extra_context,
            accept_hooks=True,
        )
        assert not (project_dir / "_shared").exists(), template_name


def test_pnpm_templates_workflows_call_shared_ci(tmp_path):
    """Rendered workflows delegate pnpm setup and commands to shared CI."""
    for template_name, extra in (
        ("template-ts-sdk", {}),
        ("template-pnpm-workspace", {"initial_package_type": "ts-lib"}),
    ):
        project_dir = _render_template(
            template_name,
            tmp_path / template_name,
            {"install_after_generate": "no", **extra},
            accept_hooks=True,
        )
        ci = (project_dir / ".github" / "workflows" / "ci.yaml").read_text(encoding="utf-8")
        assert re.search(
            r"^\s*uses: ShawnDen-coder/repo-scaffold/\.github/workflows/"
            r"reusable-node-ci\.yaml@\d+\.\d+\.\d+\s*$",
            ci,
            re.MULTILINE,
        )
        assert "lint-command:" in ci
        assert "build-command:" in ci
        assert "{% include" not in ci
        assert "_shared" not in ci


# ---------------------------------------------------------------------------
# Renovate configuration tests
# ---------------------------------------------------------------------------


def _parse_renovate_config(project_dir: Path) -> dict:
    """Parse the rendered renovate.json5 from a generated project."""
    renovate_path = project_dir / ".github" / "renovate.json5"
    assert renovate_path.is_file(), f"renovate.json5 not found in {project_dir}"
    return json5.loads(renovate_path.read_text(encoding="utf-8"))


def test_python_templates_renovate_config_present(tmp_path):
    """Python and uv-workspace templates render with Renovate config for pep621 + github-actions."""
    for template_name in ("template-python", "template-uv-workspace"):
        project_dir = _render_template(
            template_name,
            tmp_path / template_name,
            {"install_after_generate": "no"},
            accept_hooks=True,
        )
        config = _parse_renovate_config(project_dir)
        assert "pep621" in config.get("enabledManagers", [])
        assert "github-actions" in config.get("enabledManagers", [])
        assert "config:best-practices" in config.get("extends", [])


def test_pnpm_templates_renovate_config_present(tmp_path):
    """pnpm-based templates render with Renovate config for npm + github-actions."""
    for template_name, extra in (
        ("template-ts-sdk", {}),
        ("template-pnpm-workspace", {"initial_package_type": "ts-lib"}),
        ("template-react", {}),
        ("template-vue-project", {}),
    ):
        project_dir = _render_template(
            template_name,
            tmp_path / template_name,
            {"install_after_generate": "no", **extra},
            accept_hooks=True,
        )
        config = _parse_renovate_config(project_dir)
        assert "npm" in config.get("enabledManagers", []), f"{template_name} missing npm manager"
        assert "github-actions" in config.get("enabledManagers", []), f"{template_name} missing github-actions manager"


def test_ts_sdk_uses_js_lib_preset(tmp_path):
    """ts-sdk template uses config:js-lib preset (preserves semver ranges for prod deps)."""
    project_dir = _render_template(
        "template-ts-sdk",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )
    config = _parse_renovate_config(project_dir)
    assert "config:js-lib" in config.get("extends", [])


def test_vue_project_uses_js_app_preset(tmp_path):
    """vue-project template uses config:js-app preset (pins all except peer deps)."""
    project_dir = _render_template(
        "template-vue-project",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )
    config = _parse_renovate_config(project_dir)
    assert "config:js-app" in config.get("extends", [])


def test_rust_template_renovate_config_present(tmp_path):
    """Rust template renders with Renovate config for cargo + github-actions."""
    project_dir = _render_template(
        "template-rust",
        tmp_path,
        {"install_after_generate": "no"},
        accept_hooks=True,
    )
    config = _parse_renovate_config(project_dir)
    assert "cargo" in config.get("enabledManagers", [])
    assert "github-actions" in config.get("enabledManagers", [])
    assert "config:best-practices" in config.get("extends", [])


def test_rust_template_uses_reusable_container_workflows(tmp_path):
    """Docker-enabled Rust projects delegate CI and releases centrally."""
    project_dir = _render_template(
        "template-rust",
        tmp_path,
        {"use_docker": "yes", "install_after_generate": "no"},
        accept_hooks=True,
    )
    workflow_dir = project_dir / ".github" / "workflows"
    ci = (workflow_dir / "ci.yaml").read_text(encoding="utf-8")
    package_release = (workflow_dir / "package-release.yaml").read_text(encoding="utf-8")
    container_release = (workflow_dir / "container-release.yaml").read_text(encoding="utf-8")

    assert "reusable-rust-ci.yaml@" in ci
    assert "test-container: true" in ci
    assert "reusable-rust-release.yaml@" in package_release
    assert "publish-container: true" in package_release
    assert "reusable-container-release.yaml@" in container_release
    _assert_no_unrendered_markers(project_dir)
    _assert_workflows_have_github_expressions(project_dir)
    _assert_version_bump_avoids_self_trigger(project_dir)


def test_renovate_config_removed_without_github_actions(tmp_path):
    """use_github_actions=no removes Renovate config along with .github/ directory."""
    for template_name, extra in (
        ("template-python", {}),
        ("template-ts-sdk", {}),
        ("template-vue-project", {}),
    ):
        project_dir = _render_template(
            template_name,
            tmp_path / template_name,
            {"use_github_actions": "no", "install_after_generate": "no", **extra},
            accept_hooks=True,
        )
        assert not (project_dir / ".github").exists(), (
            f"{template_name} .github/ should be removed when use_github_actions=no"
        )


def test_renovate_config_has_automerge_rules(tmp_path):
    """All template Renovate configs include automerge rules for dev deps and minor/patch actions."""
    for template_name, extra in (
        ("template-python", {}),
        ("template-react", {}),
        ("template-rust", {}),
    ):
        project_dir = _render_template(
            template_name,
            tmp_path / template_name,
            {"install_after_generate": "no", **extra},
            accept_hooks=True,
        )
        config = _parse_renovate_config(project_dir)
        rules = config.get("packageRules", [])
        # At least one rule should enable automerge
        assert any(rule.get("automerge") is True for rule in rules), f"{template_name} has no automerge rules"
        # At least one rule should target github-actions
        assert any("github-actions" in rule.get("matchManagers", []) for rule in rules), (
            f"{template_name} has no github-actions automerge rule"
        )


def test_template_ts_cli_renders_unified_toolchain(tmp_path):
    """Render the standalone CLI with Vite, Biome, Vitest, and Cog ownership."""
    project_dir = _render_template(
        "template-ts-cli",
        tmp_path,
        {"install_after_generate": "no", "init_git": "no"},
        accept_hooks=True,
    )

    manifest = json.loads((project_dir / "package.json").read_text(encoding="utf-8"))
    assert manifest["bin"] == {"my-ts-cli": "./dist/index.cjs"}
    assert manifest["scripts"]["check"] == "biome check ."
    assert manifest["scripts"]["test"] == "vitest run"
    assert (project_dir / "biome.json").is_file()
    assert (project_dir / "vite.config.ts").is_file()
    assert (project_dir / ".github" / "workflows" / "ci.yaml").is_file()
    assert (project_dir / "tests" / "program.test.ts").is_file()
    assert (project_dir / "cog.toml").is_file()
    assert not (project_dir / "CHANGELOG.md").exists()
    assert "cog bump --auto" in (project_dir / "README.md").read_text(encoding="utf-8")
    _assert_no_unrendered_markers(project_dir)
    renovate = json5.loads((project_dir / ".github" / "renovate.json5").read_text(encoding="utf-8"))
    assert "npm" in renovate["enabledManagers"]
    assert "github-actions" in renovate["enabledManagers"]
    assert "config:js-app" in renovate["extends"]
    assert any(rule.get("automerge") is True for rule in renovate["packageRules"])
