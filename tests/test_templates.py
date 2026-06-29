"""Template registry and rendering tests."""

from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner
from cookiecutter.main import cookiecutter

from repo_scaffold.cli import cli
from repo_scaffold.cli import get_package_path
from repo_scaffold.cli import load_templates


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


def test_cli_create_resolves_template_key_and_title(monkeypatch, tmp_path):
    """Test create command resolves both registry key and template title."""
    calls = []
    mock_cookiecutter = Mock(side_effect=lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("repo_scaffold.cli.cookiecutter", mock_cookiecutter)

    runner = CliRunner()
    by_key = runner.invoke(cli, ["create", "template-uv-workspace", "--no-input", "-o", str(tmp_path)])
    by_title = runner.invoke(cli, ["create", "uv-workspace", "--no-input", "-o", str(tmp_path)])

    assert by_key.exit_code == 0
    assert by_title.exit_code == 0
    assert len(calls) == 2
    assert all(call["no_input"] is True for call in calls)
    assert all(call["output_dir"] == str(tmp_path) for call in calls)
    assert all(call["template"].endswith("template-uv-workspace") for call in calls)


def _render_template(template_name: str, tmp_path: Path) -> Path:
    template_dir = Path(get_package_path(f"templates/{template_name}"))
    return Path(
        cookiecutter(
            str(template_dir),
            output_dir=str(tmp_path),
            no_input=True,
            accept_hooks=False,
        )
    )


def _assert_no_unrendered_markers(project_dir: Path) -> None:
    markers = ("{{ cookiecutter", "{{cookiecutter", "{% raw %}", "{% endraw %}")
    for path in project_dir.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert not any(marker in text for marker in markers), path


def _assert_no_task_runner_references(project_dir: Path) -> None:
    assert not (project_dir / "Taskfile.yml").exists()
    assert (project_dir / "justfile").is_file()

    for path in (project_dir / ".github" / "workflows").glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "setup-task" not in text
        assert "run: task" not in text
        assert " task " not in text


def test_template_python_renders_with_justfile(tmp_path):
    """Test existing Python template renders with justfile commands."""
    project_dir = _render_template("template-python", tmp_path)

    assert (project_dir / "pyproject.toml").is_file()
    assert (project_dir / "justfile").is_file()
    assert (project_dir / ".github" / "workflows" / "ci-tests.yaml").is_file()
    _assert_no_task_runner_references(project_dir)
    _assert_no_unrendered_markers(project_dir)


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
    _assert_no_task_runner_references(project_dir)
    _assert_no_unrendered_markers(project_dir)
