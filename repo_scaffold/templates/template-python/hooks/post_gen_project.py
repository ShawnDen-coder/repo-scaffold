import os
import shutil
import subprocess


def remove_cli():
    """Remove CLI related files if not needed."""
    cli_file = os.path.join("{{cookiecutter.project_slug}}", "cli.py")
    if os.path.exists(cli_file):
        os.remove(cli_file)


def remove_github_actions():
    """Remove GitHub Actions configuration if not needed."""
    github_dir = os.path.join("{{cookiecutter.project_slug}}", ".github")
    if os.path.exists(github_dir):
        shutil.rmtree(github_dir)


def remove_mkdocs():
    """Remove MkDocs related files if not needed."""
    files_to_remove = [
        "mkdocs.yml",
        os.path.join("docs"),
    ]
    for file in files_to_remove:
        path = os.path.join("{{cookiecutter.project_slug}}", file)
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)


def init_project_depends():
    """Initialize project dependencies using uv."""
    project_dir = os.path.abspath("{{cookiecutter.project_slug}}")
    os.chdir(project_dir)
    
    # 安装基础开发依赖
    subprocess.run(["uv", "sync", "--extra", "dev"], check=True)
    
    # 如果启用了文档功能，安装文档依赖
    if "{{cookiecutter.use_mkdocs}}" == "yes":
        subprocess.run(["uv", "sync", "--extra", "docs"], check=True)


if __name__ == "__main__":
    if "{{cookiecutter.include_cli}}" == "no":
        remove_cli()
        
    if "{{cookiecutter.use_github_actions}}" == "no":
        remove_github_actions()
        
    if "{{cookiecutter.use_mkdocs}}" == "no":
        remove_mkdocs()
        
    init_project_depends()