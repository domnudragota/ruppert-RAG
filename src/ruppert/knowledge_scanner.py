from pathlib import Path

from ruppert.markdown_loader import load_markdown
from ruppert.models import Document

MARKDOWN_EXTENSIONS = {".md", ".markdown"}


def scan_knowledge(root: str | Path) -> tuple[Document, ...]:
    """Discover and load Markdown documents from a knowledge directory."""
    root_path = Path(root).expanduser().resolve()

    if not root_path.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_path}")

    paths = []

    for path in root_path.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue

        relative_path = path.relative_to(root_path)

        if any(part.startswith(".") for part in relative_path.parts):
            continue

        if path.suffix.lower() not in MARKDOWN_EXTENSIONS:
            continue

        paths.append(path)

    paths.sort(key=lambda path: path.relative_to(root_path).as_posix())

    return tuple(load_markdown(path) for path in paths)
