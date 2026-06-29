"""Generate the code reference pages for workspace packages."""

from pathlib import Path

import mkdocs_gen_files


nav = mkdocs_gen_files.Nav()
excludes = {"__pycache__"}

for src_root in sorted(Path("packages").glob("*/src")):
    for path in sorted(src_root.rglob("*.py")):
        if any(part in excludes for part in path.parts):
            continue

        module_path = path.relative_to(src_root).with_suffix("")
        doc_path = module_path.with_suffix(".md")
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
            fd.write(f"::: {'.'.join(parts)}")

        mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
