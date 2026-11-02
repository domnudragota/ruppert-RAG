import pytest

from ruppert import rag
from ruppert.knowledge_index import build_index


def test_research_uses_retrieved_context(tmp_path, monkeypatch):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "guide.md").write_text(
        "# Ghid\n"
        "## Testare\n"
        "Verificăm regresiile.\n"
        "### Integrare\n"
        "Verificăm statusul HTTP și body-ul.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    received = {}

    def fake_ask(prompt, think=False, *, system_prompt=None):
        received["prompt"] = prompt
        received["think"] = think
        received["system_prompt"] = system_prompt
        return "Testare documentată [guide.md:L2-3]"

    monkeypatch.setattr(rag, "ask", fake_ask)

    answer = rag.research(
        "Cum testăm un endpoint?",
        db,
        retrieval_query="testare",
        think=False,
    )

    # Verify the generated answer.
    assert "Testare documentată" in answer
    assert "[AVERTISMENT RUPPERT]" not in answer

    # Verify retrieved context reaches the LLM.
    assert "guide.md:L2-3" in received["prompt"]
    assert "guide.md:L4-5" in received["prompt"]
    assert "statusul HTTP" in received["prompt"]

    # Verify the trusted citation manifest reaches the LLM.
    assert "Allowed citations (copy exactly):" in received["prompt"]
    assert "- [guide.md:L2-3]" in received["prompt"]
    assert "- [guide.md:L4-5]" in received["prompt"]

    # Verify LLM configuration.
    assert received["think"] is False
    assert received["system_prompt"] == rag.RAG_SYSTEM_PROMPT


def test_research_without_evidence_skips_llm(tmp_path, monkeypatch):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "guide.md").write_text(
        "# Ghid\nInformații despre testare.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    def forbidden_llm(*args, **kwargs):
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr(rag, "ask", forbidden_llm)

    answer = rag.research(
        "Ce știm despre un subiect absent?",
        db,
        retrieval_query="zephyrox",
    )

    assert "Nu am găsit informații relevante" in answer


@pytest.mark.parametrize(
    ("model_output", "expected_warning"),
    [
        (
            "Raspuns fara citari.",
            "Lipsesc citări valide",
        ),
        (
            "Raspuns cu sursa [invented.md:L1-99].",
            "Citări neverificate",
        ),
    ],
)
def test_research_warns_about_invalid_citations(
    tmp_path,
    monkeypatch,
    model_output,
    expected_warning,
):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "guide.md").write_text(
        "# Ghid\n## Testare\nVerificam regresiile.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    monkeypatch.setattr(
        rag,
        "ask",
        lambda *args, **kwargs: model_output,
    )

    answer = rag.research(
        "Cum testam?",
        db,
        retrieval_query="testare",
        limit=1,
    )

    assert "[AVERTISMENT RUPPERT]" in answer
    assert expected_warning in answer
