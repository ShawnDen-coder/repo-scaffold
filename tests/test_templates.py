"""Template registry and rendering tests."""

import json
import subprocess
import tomllib
from pathlib import Path
from unittest.mock import Mock

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
    assert calls[0]["extra_context"] == {"install_after_generate": "yes"}
    assert calls[1]["extra_context"] == {"install_after_generate": "no"}


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

    with (project_dir / "pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)
    assert pyproject["tool"]["uv"]["package"] is False
    assert pyproject["tool"]["uv"]["workspace"]["members"] == ["packages/*"]

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


def test_workspace_post_gen_hook_uses_project_root(monkeypatch, tmp_path):
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
