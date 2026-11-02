import pytest

from ruppert.knowledge_scanner import scan_knowledge


def test_scan_discovers_markdown_recursively(tmp_path):
    root = tmp_path / "knowledge"
    architecture = root / "architecture"
    workflows = root / "workflows"

    architecture.mkdir(parents=True)
    workflows.mkdir()

    (architecture / "backend.md").write_text(
        "# Backend\nRust and Axum.\n", encoding="utf-8"
    )
    (workflows / "tickets.markdown").write_text(
        "# Workflow\nInvestigate first.\n", encoding="utf-8"
    )
    (root / "ignored.txt").write_text("Not Markdown", encoding="utf-8")

    documents = scan_knowledge(root)

    assert len(documents) == 2
    assert [doc.title for doc in documents] == [
        "Backend",
        "Workflow",
    ]
    assert documents[0].sections[0].heading == "Backend"


def test_scan_empty_directory(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    assert scan_knowledge(root) == ()


def test_scan_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        scan_knowledge(tmp_path / "missing")


def test_scan_ignores_hidden_files(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / ".private.md").write_text("# Secret\n", encoding="utf-8")
    (root / ".hidden").mkdir()
    (root / ".hidden" / "notes.md").write_text("# Hidden\n", encoding="utf-8")

    assert scan_knowledge(root) == ()


def test_scan_ignores_symlinks(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")

    (root / "linked.md").symlink_to(outside)

    assert scan_knowledge(root) == ()
