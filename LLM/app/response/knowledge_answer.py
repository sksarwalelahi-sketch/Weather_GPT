"""Lazy RAG entry point for general weather-knowledge questions."""


def generate_knowledge_answer(
    question: str,
    language: str,
) -> str | None:
    """Use the existing RAG answer generator when it is available."""

    try:
        from rag.rag_answer import generate_answer

        return generate_answer(
            question,
            language=language,
        )

    except Exception:
        # Live weather and intelligence routes must continue to work
        # when the local vector database or Ollama is unavailable.
        return None
