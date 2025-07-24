"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files


nav = mkdocs_gen_files.Nav()

# 排除的目录
EXCLUDES = ["__pycache__"]

for path in sorted(Path("repo-scaffold").rglob("*.py")):
    # 检查路径中是否包含要排除的目录
    if any(exclude in str(path) for exclude in EXCLUDES):
        continue

    module_path = path.relative_to(".").with_suffix("")
    doc_path = path.relative_to(".").with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)

        # 添加模块标题和描述
        module_name = parts[-1] if parts else "repo-scaffold"
        title = module_name.replace("_", " ").title()

        fd.write(f"# {title}\n\n")

        # 添加 mkdocstrings 指令，优化显示效果
        fd.write(f"::: {ident}\n")
        fd.write("    options:\n")
        fd.write("      show_root_heading: false\n")
        fd.write("      show_source: false\n")
        fd.write("      heading_level: 2\n")
        fd.write("      docstring_style: google\n")
        fd.write("      docstring_section_style: table\n")
        fd.write("      show_signature_annotations: true\n")
        fd.write("      separate_signature: true\n")
        fd.write("      filters:\n")
        fd.write("        - '!^_.*'\n")           # 排除私有变量
        fd.write("        - '!^__.*__$'\n")       # 排除双下划线变量
        fd.write("        - '!^[A-Z_]+$'\n")      # 排除全大写常量
        fd.write("        - '^__init__$'\n")      # 但保留 __init__ 方法

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
