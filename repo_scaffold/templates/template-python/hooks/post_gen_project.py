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
    if "{{cookiecutter.use_github_actions}}" == "no":
        github_dir = os.path.join(".github")
        if os.path.exists(github_dir):
            shutil.rmtree(github_dir)


def remove_docs():
    """Remove documentation related files if GitHub Actions is not used."""
    if "{{cookiecutter.use_github_actions}}" == "no":
        # 删除 mkdocs.yml
        if os.path.exists("mkdocs.yml"):
            os.remove("mkdocs.yml")
        # 删除 docs 目录
        docs_dir = "docs"
        if os.path.exists(docs_dir):
            shutil.rmtree(docs_dir)


def init_project_depends():
    """Initialize project dependencies using uv."""
    project_dir = os.path.abspath("{{cookiecutter.project_slug}}")
    os.chdir(project_dir)
    
    # 安装基础开发依赖
    subprocess.run(["uv", "sync", "--extra", "dev"], check=True)


if __name__ == "__main__":
    if "{{cookiecutter.include_cli}}" == "no":
        remove_cli()
        
    if "{{cookiecutter.use_github_actions}}" == "no":
        remove_github_actions()
        remove_docs()
        
    init_project_depends()