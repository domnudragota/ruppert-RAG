import re
from collections.abc import Iterable
from dataclasses import dataclass

# Supported formats:
# [file:L10-20]
# `file:L10-20`
# [Label](source:file:L10-20)
#
# Single-line and L-prefixed ranges are also detected,
# but only exact manifest matches are accepted.
CITATION_PATTERN = re.compile(
    r"\[([^\[\]`\n]+:L\d+(?:-L?\d+)?)\]"
    r"|`([^`\n]+:L\d+(?:-L?\d+)?)`"
    r"|\[[^\]\n]+\]\(source:([^)\n]+:L\d+(?:-L?\d+)?)\)"
)


@dataclass(frozen=True, slots=True)
class CitationReport:
    valid: tuple[str, ...]
    invalid: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return bool(self.valid) and not self.invalid

    @property
    def missing(self) -> bool:
        return not self.valid and not self.invalid


def validate_citations(
    answer: str,
    allowed_sources: Iterable[str],
) -> CitationReport:
    """Validate citations against trusted source identifiers."""

    allowed = set(allowed_sources)

    citations = [
        match.group(1) or match.group(2) or match.group(3)
        for match in CITATION_PATTERN.finditer(answer)
    ]

    valid: list[str] = []
    invalid: list[str] = []

    for citation in dict.fromkeys(citations):
        if citation in allowed:
            valid.append(citation)
        else:
            invalid.append(citation)

    return CitationReport(
        valid=tuple(valid),
        invalid=tuple(invalid),
    )
