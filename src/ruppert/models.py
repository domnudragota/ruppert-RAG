from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Section:
    heading: str | None
    level: int
    heading_path: tuple[str, ...]
    start_line: int  # 1-based, inclusive
    end_line: int  # 1-based, inclusive
    content: str  # Original Markdown


@dataclass(frozen=True, slots=True)
class Document:
    path: Path
    title: str
    sections: tuple[Section, ...]


@dataclass(frozen=True, slots=True)
class SearchHit:
    path: str
    title: str
    heading: str | None
    heading_path: tuple[str, ...]
    start_line: int
    end_line: int
    content: str
    score: float


@dataclass(frozen=True, slots=True)
class ContextResult:
    text: str
    sources: tuple[str, ...]
