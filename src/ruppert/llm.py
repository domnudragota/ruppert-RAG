from ollama import Client

MODEL = "qwen3.5:4b-q4_K_M"


def ask(
    prompt: str,
    think: bool = False,
    *,
    system_prompt: str | None = None,
) -> str:
    client = Client(host="http://127.0.0.1:11434")

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Ruppert, a local AI assistant specialized in "
                    "software engineering and codebase research. "
                    "You can also discuss general topics naturally. "
                    "Be concise, direct, and conversational. "
                    "Adapt your response to the user's actual question. "
                    "For codebase investigations, prioritize evidence over assumptions. "
                    "Never invent file paths, functions, or implementation details. "
                    "Only claim to have inspected files when their contents "
                    "were explicitly provided to you. "
                    "Clearly distinguish verified facts from hypotheses. "
                    "If you lack the necessary evidence, acknowledge it."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        think=think,
        options={"num_ctx": 8192},
        keep_alive="1m",
    )

    return response.message.content or ""
