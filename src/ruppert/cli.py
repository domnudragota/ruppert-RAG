import argparse
from pathlib import Path

from ruppert.knowledge_index import (
    build_index,
    get_descendant_sections,
    search_index,
)
from ruppert.llm import ask
from ruppert.rag import research


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Ruppert — local codebase research assistant"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ruppert ask
    ask_parser = commands.add_parser("ask", help="Ask the local LLM")
    ask_parser.add_argument("prompt")
    ask_parser.add_argument("--think", action="store_true")

    # ruppert index
    index_parser = commands.add_parser(
        "index", help="Build the Markdown knowledge index"
    )
    index_parser.add_argument(
        "--knowledge",
        type=Path,
        default=Path("knowledge"),
    )
    index_parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/knowledge.db"),
    )

    # ruppert search
    search_parser = commands.add_parser(
        "search", help="Search indexed Markdown sections"
    )
    search_parser.add_argument("query")
    search_parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/knowledge.db"),
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )
    search_parser.add_argument(
        "--full",
        action="store_true",
        help="Display complete section content",
    )
    search_parser.add_argument(
        "--expand",
        action="store_true",
        help="Include up to three descendant sections per result",
    )

    # ruppert research
    research_parser = commands.add_parser(
        "research",
        help="Answer questions using indexed documentation",
    )
    research_parser.add_argument("question")
    research_parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/knowledge.db"),
    )
    research_parser.add_argument(
        "--query",
        default=None,
        help="Optional lexical retrieval query",
    )
    research_parser.add_argument(
        "--limit",
        type=int,
        default=3,
    )
    research_parser.add_argument(
        "--descendants",
        type=int,
        default=3,
    )
    research_parser.add_argument(
        "--max-chars",
        type=int,
        default=8000,
    )
    research_parser.add_argument(
        "--think",
        action="store_true",
    )

    args = parser.parse_args(argv)

    if args.command == "ask":
        print(ask(args.prompt, think=args.think))
        return

    if args.command == "research":
        answer = research(
            question=args.question,
            database_path=args.db,
            retrieval_query=args.query,
            limit=args.limit,
            max_chars=args.max_chars,
            max_descendants=args.descendants,
            think=args.think,
        )
        print(answer)
        return

    if args.command == "index":
        count = build_index(args.knowledge, args.db)
        print(f"Indexed {count} sections into {args.db}")
        return

    if args.command == "search":
        hits = search_index(args.db, args.query, args.limit)

        if not hits:
            print("No matching sections found.")
            return

        for index, hit in enumerate(hits, start=1):
            heading = " > ".join(hit.heading_path) or "(Preamble)"

            print(f"\n[{index}] {hit.path}:L{hit.start_line}-{hit.end_line}")
            print(f"Heading: {heading}")
            print(f"BM25: {hit.score:.4f}")

            if args.full:
                print(hit.content.rstrip())
            else:
                excerpt = " ".join(hit.content.split())
                print(excerpt[:300] + ("..." if len(excerpt) > 300 else ""))

            # Expand the result with its descendant sections.
            if args.expand:
                children = get_descendant_sections(
                    args.db,
                    hit,
                    limit=3,
                )

                for child in children:
                    print(f"\n  ↳ {hit.path}:L{child.start_line}-{child.end_line}")
                    print(f"  Heading: {' > '.join(child.heading_path)}")

                    if args.full:
                        print(child.content.rstrip())
                    else:
                        excerpt = " ".join(child.content.split())
                        print(excerpt[:300] + ("..." if len(excerpt) > 300 else ""))


if __name__ == "__main__":
    main()
