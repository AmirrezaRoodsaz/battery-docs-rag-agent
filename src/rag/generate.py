"""Generation: answer a question grounded in retrieved chunks, with citations.

This is the "G" in RAG, and where grounding is enforced. The contract we impose on the LLM:
  - Answer ONLY from the provided context. Do not use outside knowledge.
  - Cite the [n] label of every chunk you draw a claim from.
  - If the context does not contain the answer, say exactly that — never guess.

That last rule is the whole point of the project: for an engineering/safety-document tool,
a confidently wrong answer is a failure, not a rough edge. RAG *reduces* hallucination
(the model is anchored to real text) but does not *eliminate* it (it can still misread the
context), which is why we cite — so a human can verify — and why we evaluate (Phase 4).

This module composes the prompt and calls the provider-agnostic LLM layer. It also handles
the no-retrieval case without ever calling the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.index.vectorstore import SearchHit
from src.llm.provider import LLMProvider, get_provider
from src.rag.cite import Citation, build_context, format_sources
from src.rag.retrieve import Retriever

NOT_FOUND = "Not found in the provided documents."

SYSTEM_PROMPT = (
    "You are a precise assistant for battery and automotive engineers. You answer ONLY "
    "from the provided context passages, which are excerpts from a fixed document corpus.\n"
    "Rules:\n"
    "1. Use only the information in the context. Do NOT use outside knowledge or guess.\n"
    "2. After each claim, cite the passage label(s) it came from, like [1] or [2][3].\n"
    f"3. If the context does not contain the answer, reply exactly: '{NOT_FOUND}' and "
    "nothing else. Do not speculate.\n"
    "4. Be concise and technical. Prefer exact values and conditions from the context.\n"
)

USER_TEMPLATE = (
    "Context passages:\n"
    "------------------\n"
    "{context}\n"
    "------------------\n\n"
    "Question: {question}\n\n"
    "Answer using only the passages above, citing labels inline. If unsupported, reply "
    f"exactly '{NOT_FOUND}'."
)

# Below this top similarity, we treat retrieval as a miss and short-circuit to "not found"
# without spending an LLM call. Tuned conservatively; the LLM's own grounding rule is the
# real guard, this just avoids paying for hopeless queries.
MIN_TOP_SIMILARITY = 0.15


@dataclass
class RAGAnswer:
    question: str
    answer: str
    citations: list[Citation]
    hits: list[SearchHit]
    provider: str
    model: str

    @property
    def is_grounded(self) -> bool:
        """True if the model actually answered (vs. the not-found refusal)."""
        return self.answer.strip().rstrip(".") != NOT_FOUND.rstrip(".")

    def render(self) -> str:
        return f"{self.answer}\n\n{format_sources(self.citations)}"


def answer_question(
    question: str,
    retriever: Retriever,
    k: int = 4,
    use_mmr: bool = False,
    provider: LLMProvider | None = None,
) -> RAGAnswer:
    """Retrieve, then generate a grounded, cited answer (or a 'not found' refusal)."""
    hits = retriever.retrieve(question, k=k, use_mmr=use_mmr)

    # No usable retrieval -> refuse without calling the LLM.
    if not hits or hits[0].score < MIN_TOP_SIMILARITY:
        context, citations = build_context(hits)
        return RAGAnswer(
            question=question,
            answer=NOT_FOUND,
            citations=citations,
            hits=hits,
            provider="(none)",
            model="(retrieval miss — no LLM call)",
        )

    context, citations = build_context(hits)
    llm = provider or get_provider()
    user = USER_TEMPLATE.format(context=context, question=question)
    answer = llm.complete(SYSTEM_PROMPT, user)

    return RAGAnswer(
        question=question,
        answer=answer,
        citations=citations,
        hits=hits,
        provider=llm.name,
        model=llm.model,
    )
