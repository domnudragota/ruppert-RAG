import pytest

from ruppert.knowledge_index import build_index, get_descendant_sections, search_index


def test_index_and_search_with_diacritics(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "workflow.md").write_text(
        "# Workflow\n## Analiză\nInvestigăm înainte de implementare.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"

    assert build_index(root, db) == 2

    hits = search_index(db, "analiza")

    assert hits
    assert hits[0].heading == "Analiză"
    assert hits[0].path == "workflow.md"
    assert hits[0].start_line == 2
    assert hits[0].end_line == 3
    assert "Investigăm" in hits[0].content


def test_rebuild_removes_stale_sections(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    path = root / "test.md"
    db = tmp_path / "knowledge.db"

    path.write_text("# Old\nlegacytoken\n", encoding="utf-8")

    assert build_index(root, db) == 1
    assert search_index(db, "legacytoken")

    path.write_text("# New\nfreshterm\n", encoding="utf-8")

    assert build_index(root, db) == 1
    assert search_index(db, "legacytoken") == ()
    assert search_index(db, "freshterm")


def test_search_handles_punctuation(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "test.md").write_text(
        "# VAT\nValidation errors.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    assert search_index(db, 'VAT: (errors) "validation"?')
    assert search_index(db, "!!!") == ()


def test_empty_knowledge_directory(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    db = tmp_path / "knowledge.db"

    assert build_index(root, db) == 0
    assert search_index(db, "anything") == ()


def test_missing_index(tmp_path):
    with pytest.raises(FileNotFoundError):
        search_index(tmp_path / "missing.db", "test")


def test_invalid_limit(tmp_path):
    with pytest.raises(ValueError):
        search_index(tmp_path / "missing.db", "test", limit=0)


def test_document_title_does_not_match_every_section(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "checkout.md").write_text(
        "# Checkout\n"
        "General overview.\n"
        "## VAT\n"
        "Company registration validation.\n"
        "## Coupons\n"
        "Discount eligibility.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    hits = search_index(db, "checkout")

    assert [hit.heading for hit in hits] == ["Checkout"]


def test_hierarchical_expansion_stops_at_sibling(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "workflow.md").write_text(
        "# Workflow\n"
        "## Strategia de testare\n"
        "Introducere.\n"
        "### Piramida practică\n"
        "Teste unitare și de integrare.\n"
        "### Regresii\n"
        "Verificări suplimentare.\n"
        "## Implementare\n"
        "Altă etapă.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    hits = search_index(db, "testare")
    parent = next(hit for hit in hits if hit.heading == "Strategia de testare")

    children = get_descendant_sections(db, parent)

    assert [child.heading for child in children] == [
        "Piramida practică",
        "Regresii",
    ]

    assert children[0].start_line == 4
    assert children[0].end_line == 5

    # Never include the next sibling section.
    assert all(child.heading != "Implementare" for child in children)

    # Leaf sections must not expand.
    leaf = next(
        hit
        for hit in search_index(db, "piramida")
        if hit.heading == "Piramida practică"
    )
    assert get_descendant_sections(db, leaf) == ()

    # Respect the requested limit.
    assert len(get_descendant_sections(db, parent, limit=1)) == 1
