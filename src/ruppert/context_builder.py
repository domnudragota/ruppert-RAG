from collections.abc import Sequence
from pathlib import Path

from ruppert.knowledge_index import get_descendant_sections
from ruppert.models import ContextResult, SearchHit


def build_context_result(
    database_path: str | Path,
    hits: Sequence[SearchHit],
    *,
    max_chars: int = 8000,
    max_descendants: int = 3,
) -> ContextResult:
    """Build context and an independent source manifest."""

    if max_chars < 1:
        raise ValueError("Context budget must be positive")

    if max_descendants < 0:
        raise ValueError("Descendant limit cannot be negative")

    blocks: list[str] = []
    sources: list[str] = []
    seen: set[tuple[str, int, int]] = set()
    used_chars = 0

    def add_section(
        path: str,
        start_line: int,
        end_line: int,
        heading_path: tuple[str, ...],
        content: str,
    ) -> None:
        nonlocal used_chars

        key = (path, start_line, end_line)

        if key in seen:
            return

        source = f"{path}:L{start_line}-{end_line}"
        heading = " > ".join(heading_path) or "(Preamble)"

        block = f"Source: {source}\nHeading: {heading}\nMarkdown:\n{content.rstrip()}"

        separator = "\n\n---\n\n" if blocks else ""
        candidate = separator + block

        if used_chars + len(candidate) > max_chars:
            return

        seen.add(key)
        blocks.append(candidate)
        sources.append(source)
        used_chars += len(candidate)

    for hit in hits:
        add_section(
            hit.path,
            hit.start_line,
            hit.end_line,
            hit.heading_path,
            hit.content,
        )

        if max_descendants == 0:
            continue

        children = get_descendant_sections(
            database_path,
            hit,
            limit=max_descendants,
        )

        for child in children:
            add_section(
                hit.path,
                child.start_line,
                child.end_line,
                child.heading_path,
                child.content,
            )

    return ContextResult(
        text="".join(blocks),
        sources=tuple(sources),
    )


def build_context(
    database_path: str | Path,
    hits: Sequence[SearchHit],
    *,
    max_chars: int = 8000,
    max_descendants: int = 3,
) -> str:
    """Preserve the original text-only Context Builder API."""

    return build_context_result(
        database_path,
        hits,
        max_chars=max_chars,
        max_descendants=max_descendants,
    ).text
