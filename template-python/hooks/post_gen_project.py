import os
import subprocess


def remove_cli():
    cli_file = os.path.join("{{cookiecutter.project_slug}}", "cli.py")
    if os.path.exists(cli_file):
        os.remove(cli_file)


def init_poetry():
    project_dir = os.path.abspath("{{cookiecutter.project_slug}}")
    os.chdir(project_dir)
    subprocess.run(["poetry", "install"], check=True)

if __name__ == "__main__":
    if "{{cookiecutter.project_slug}}" == "n":
        remove_cli()
    init_poetry()