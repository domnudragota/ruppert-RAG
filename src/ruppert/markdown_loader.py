from pathlib import Path

from markdown_it import MarkdownIt

from ruppert.models import Document, Section

_PARSER = MarkdownIt("commonmark", {"html": False}).enable("table")


def _heading_text(inline_token) -> str:
    """Extract heading text using Markdown tokens."""
    parts = [
        child.content
        for child in (inline_token.children or [])
        if child.type in {"text", "code_inline", "image"}
    ]

    return "".join(parts).strip() or inline_token.content.strip()


def load_markdown(path: str | Path) -> Document:
    """Read Markdown into non-overlapping sections."""

    source_path = Path(path).expanduser().resolve()

    if source_path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError(f"Not a Markdown file: {source_path}")

    source = source_path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    tokens = _PARSER.parse(source)

    headings: list[tuple[int, int, str]] = []

    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.level != 0 or token.map is None:
            continue

        inline_token = tokens[index + 1]

        headings.append(
            (
                token.map[0],
                int(token.tag[1:]),
                _heading_text(inline_token),
            )
        )

    title = next(
        (text for _, level, text in headings if level == 1),
        source_path.stem,
    )

    sections: list[Section] = []

    # Preserve content before the first heading.
    first_heading = headings[0][0] if headings else len(lines)

    if first_heading > 0:
        sections.append(
            Section(
                heading=None,
                level=0,
                heading_path=(),
                start_line=1,
                end_line=first_heading,
                content="".join(lines[:first_heading]),
            )
        )

    ancestors: list[tuple[int, str]] = []

    for index, (start, level, heading) in enumerate(headings):
        # Maintain the current heading hierarchy.
        while ancestors and ancestors[-1][0] >= level:
            ancestors.pop()

        ancestors.append((level, heading))

        # Each section ends before the next heading.
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)

        sections.append(
            Section(
                heading=heading,
                level=level,
                heading_path=tuple(text for _, text in ancestors),
                start_line=start + 1,
                end_line=end,
                content="".join(lines[start:end]),
            )
        )

    return Document(
        path=source_path,
        title=title,
        sections=tuple(sections),
    )
