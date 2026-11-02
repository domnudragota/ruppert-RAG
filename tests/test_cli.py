from pathlib import Path

from ruppert import cli


def test_cli_index_and_search(tmp_path, capsys, monkeypatch):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "workflow.md").write_text(
        "# Workflow\n## Analiză\nInvestigăm problema înainte de implementare.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"

    def forbidden_llm(*args, **kwargs):
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr(cli, "ask", forbidden_llm)

    cli.main(
        [
            "index",
            "--knowledge",
            str(root),
            "--db",
            str(db),
        ]
    )

    assert db.exists()
    assert "Indexed 2 sections" in capsys.readouterr().out

    cli.main(
        [
            "search",
            "analiza",
            "--db",
            str(db),
        ]
    )

    output = capsys.readouterr().out

    assert "workflow.md:L2-3" in output
    assert "Analiză" in output


def test_cli_ask_thinking_flag(monkeypatch, capsys):
    received = {}

    def fake_ask(prompt, think=False):
        received["prompt"] = prompt
        received["think"] = think
        return "Test response"

    monkeypatch.setattr(cli, "ask", fake_ask)

    cli.main(["ask", "Hello Ruppert", "--think"])

    assert received == {
        "prompt": "Hello Ruppert",
        "think": True,
    }

    assert "Test response" in capsys.readouterr().out


def test_cli_search_with_expansion(tmp_path, capsys):
    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "guide.md").write_text(
        "# Ghid\n"
        "## Strategia de testare\n"
        "Introducere.\n"
        "### Piramida practică\n"
        "Teste unitare.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"

    cli.main(
        [
            "index",
            "--knowledge",
            str(root),
            "--db",
            str(db),
        ]
    )
    capsys.readouterr()

    cli.main(
        [
            "search",
            "testare",
            "--db",
            str(db),
            "--limit",
            "1",
            "--expand",
            "--full",
        ]
    )

    output = capsys.readouterr().out

    assert "guide.md:L2-3" in output
    assert "guide.md:L4-5" in output
    assert "Piramida practică" in output
    assert "Teste unitare." in output


def test_cli_research_forwards_options(monkeypatch, capsys):
    received = {}

    def fake_research(**kwargs):
        received.update(kwargs)
        return "Research completed"

    monkeypatch.setattr(cli, "research", fake_research)

    cli.main(
        [
            "research",
            "Cum testam un tichet?",
            "--db",
            "data/test.db",
            "--query",
            "strategia de testare",
            "--limit",
            "1",
            "--descendants",
            "2",
            "--max-chars",
            "6000",
            "--think",
        ]
    )

    assert received == {
        "question": "Cum testam un tichet?",
        "database_path": Path("data/test.db"),
        "retrieval_query": "strategia de testare",
        "limit": 1,
        "max_chars": 6000,
        "max_descendants": 2,
        "think": True,
    }

    assert "Research completed" in capsys.readouterr().out


def test_cli_research_without_evidence_skips_llm(tmp_path, monkeypatch, capsys):
    from ruppert.knowledge_index import build_index

    root = tmp_path / "knowledge"
    root.mkdir()

    (root / "guide.md").write_text(
        "# Ghid\nDocumentatie despre testare.\n",
        encoding="utf-8",
    )

    db = tmp_path / "knowledge.db"
    build_index(root, db)

    def forbidden_llm(*args, **kwargs):
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr("ruppert.rag.ask", forbidden_llm)

    cli.main(
        [
            "research",
            "Ce stim despre subiectul absent?",
            "--db",
            str(db),
            "--query",
            "zephyrox",
        ]
    )

    assert "Nu am găsit informații relevante" in capsys.readouterr().out
