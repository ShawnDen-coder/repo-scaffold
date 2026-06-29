"""Generate the home pages."""

from pathlib import Path

import mkdocs_gen_files


readme_path = Path(__file__).resolve().parents[1] / "README.md"
content = readme_path.read_text(encoding="utf-8")

with mkdocs_gen_files.open("index.md", "w") as f:
    f.write(content)
