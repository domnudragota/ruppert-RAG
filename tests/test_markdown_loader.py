import pytest

from ruppert.markdown_loader import load_markdown


def test_nested_sections(tmp_path):
    source = (
        "# Backend\n"
        "Overview.\n"
        "\n"
        "## VAT\n"
        "Validation logic.\n"
        "\n"
        "### Errors\n"
        "```rust\n"
        "# Not a real heading\n"
        "```\n"
        "\n"
        "## Coupons\n"
        "Coupon logic.\n"
    )

    path = tmp_path / "backend.md"
    path.write_text(source, encoding="utf-8")

    document = load_markdown(path)

    assert document.title == "Backend"

    assert [s.heading for s in document.sections] == [
        "Backend",
        "VAT",
        "Errors",
        "Coupons",
    ]

    assert document.sections[2].heading_path == (
        "Backend",
        "VAT",
        "Errors",
    )

    assert "# Not a real heading" in document.sections[2].content


def test_line_references(tmp_path):
    source = "# Title\nIntro\n\n## Section\nContent\n"
    path = tmp_path / "document.md"
    path.write_text(source, encoding="utf-8")

    document = load_markdown(path)

    assert document.sections[0].start_line == 1
    assert document.sections[0].end_line == 3
    assert document.sections[1].start_line == 4
    assert document.sections[1].end_line == 5


def test_nested_blockquote_heading_is_ignored(tmp_path):
    path = tmp_path / "document.md"
    path.write_text(
        "# Main\n\n> ## Quoted\n\n## Actual\n",
        encoding="utf-8",
    )

    document = load_markdown(path)

    assert [s.heading for s in document.sections] == [
        "Main",
        "Actual",
    ]


def test_document_without_headings(tmp_path):
    path = tmp_path / "plain.md"
    path.write_text("Just a paragraph.\n", encoding="utf-8")

    document = load_markdown(path)

    assert document.title == "plain"
    assert len(document.sections) == 1
    assert document.sections[0].heading is None


def test_invalid_extension(tmp_path):
    path = tmp_path / "code.rs"
    path.write_text("fn main() {}", encoding="utf-8")

    with pytest.raises(ValueError):
        load_markdown(path)


def test_preserves_blank_lines_before_first_heading(tmp_path):
    source = "\n\n# Title\nContent\n"

    path = tmp_path / "document.md"
    path.write_text(source, encoding="utf-8")

    document = load_markdown(path)

    assert len(document.sections) == 2

    preamble, section = document.sections

    assert preamble.content == "\n\n"
    assert preamble.start_line == 1
    assert preamble.end_line == 2

    assert section.heading == "Title"
    assert section.start_line == 3
    assert section.end_line == 4

    assert "".join(section.content for section in document.sections) == source
