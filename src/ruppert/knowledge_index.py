import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from ruppert.knowledge_scanner import scan_knowledge
from ruppert.models import SearchHit, Section


def build_index(
    knowledge_root: str | Path,
    database_path: str | Path,
) -> int:
    """Rebuild the FTS5 knowledge index transactionally."""

    root = Path(knowledge_root).expanduser().resolve()
    database = Path(database_path).expanduser().resolve()

    documents = scan_knowledge(root)
    database.parent.mkdir(parents=True, exist_ok=True)

    rows = (
        (
            document.path.relative_to(root).as_posix(),
            document.title,
            section.heading,
            json.dumps(section.heading_path, ensure_ascii=False),
            section.start_line,
            section.end_line,
            section.content,
        )
        for document in documents
        for section in document.sections
    )

    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute("BEGIN")

        conn.execute("DROP TABLE IF EXISTS sections")

        conn.execute("""
                CREATE VIRTUAL TABLE sections USING fts5(
                    path UNINDEXED,
                    title UNINDEXED,
heading,
heading_path UNINDEXED,
                    start_line UNINDEXED,
                    end_line UNINDEXED,
                    content,
                    tokenize = 'unicode61 remove_diacritics 2'
                )
            """)

        conn.executemany(
            """
                INSERT INTO sections (
                    path, title, heading, heading_path,
                    start_line, end_line, content
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            rows,
        )

    return sum(len(document.sections) for document in documents)


def search_index(
    database_path: str | Path,
    query: str,
    limit: int = 5,
) -> tuple[SearchHit, ...]:
    """Search indexed Markdown sections using FTS5 BM25."""

    if limit < 1:
        raise ValueError("Search limit must be positive")

    database = Path(database_path).expanduser().resolve()

    if not database.is_file():
        raise FileNotFoundError(f"Knowledge index not found: {database}")

    # Build a safe FTS5 expression from ordinary user text.
    terms = list(dict.fromkeys(re.findall(r"[^\W_]+", query)))

    if not terms:
        return ()

    expression = " OR ".join(f'"{term}"' for term in terms)

    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                path,
                title,
                heading,
                heading_path,
                start_line,
                end_line,
                content,
               bm25(sections, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 1.0) AS score
            FROM sections
            WHERE sections MATCH ?
            ORDER BY score ASC
            LIMIT ?
            """,
            (expression, limit),
        ).fetchall()

    return tuple(
        SearchHit(
            path=row["path"],
            title=row["title"],
            heading=row["heading"],
            heading_path=tuple(json.loads(row["heading_path"])),
            start_line=int(row["start_line"]),
            end_line=int(row["end_line"]),
            content=row["content"],
            score=float(row["score"]),
        )
        for row in rows
    )


def get_descendant_sections(
    database_path: str | Path,
    hit: SearchHit,
    limit: int = 3,
) -> tuple[Section, ...]:
    """Retrieve descendant sections from the indexed document."""

    if limit < 1:
        raise ValueError("Section limit must be positive")

    if not hit.heading_path:
        return ()

    database = Path(database_path).expanduser().resolve()

    if not database.is_file():
        raise FileNotFoundError(f"Knowledge index not found: {database}")

    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as conn:
        rows = conn.execute(
            """
            SELECT heading, heading_path, start_line, end_line, content
            FROM sections
            WHERE path = ?
              AND CAST(start_line AS INTEGER) > ?
            ORDER BY CAST(start_line AS INTEGER)
            """,
            (hit.path, hit.start_line),
        ).fetchall()

    descendants = []
    prefix = hit.heading_path

    for heading, path_json, start, end, content in rows:
        heading_path = tuple(json.loads(path_json))

        # Stop at the next sibling or ancestor.
        if len(heading_path) <= len(prefix) or heading_path[: len(prefix)] != prefix:
            break

        descendants.append(
            Section(
                heading=heading,
                level=len(heading_path),
                heading_path=heading_path,
                start_line=int(start),
                end_line=int(end),
                content=content,
            )
        )

        if len(descendants) >= limit:
            break

    return tuple(descendants)
