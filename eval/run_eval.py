"""Evaluate the RAG system honestly, and write reports/results.md.

A lightweight, transparent eval beats none — and is a strong interview talking point.
We measure three things on a small, hand-written question set (eval/qa_set.jsonl):

1. Retrieval hit-rate (NO LLM needed)
   For each answerable question, did the EXPECTED source document appear among the top-k
   retrieved chunks? This isolates the retriever from the generator: if the right chunk
   never comes back, no amount of prompting will produce a grounded answer.

2. Answer correctness (needs an LLM)
   Did the generated answer contain the expected key fact (a substring check)? This is a
   deliberately simple, transparent *proxy* for faithfulness — not an LLM-judge. It can
   miss paraphrases, so we report it as a lower bound and show every miss for inspection.

3. Refusal accuracy (needs an LLM)
   For out-of-corpus questions, did the system correctly say "not found" instead of
   inventing an answer? This is the anti-hallucination behaviour, measured directly.

Run with `make eval`. Without an LLM key, only retrieval hit-rate is computed (still useful).
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from src.llm.provider import LLMError, get_provider
from src.rag.generate import answer_question
from src.rag.retrieve import Retriever

load_dotenv()

QA_PATH = Path("eval/qa_set.jsonl")
OUT_PATH = Path("reports/results.md")
TOP_K = 4
RANK_POOL = 10  # retrieve this many to locate the rank of the first correct chunk for MRR


def load_qa() -> list[dict]:
    return [
        json.loads(line)
        for line in QA_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def llm_available() -> bool:
    try:
        get_provider()
        return True
    except LLMError:
        return False


def evaluate() -> dict:
    qa = load_qa()
    retriever = Retriever.from_index()
    have_llm = llm_available()

    answerable = [q for q in qa if q["type"] == "answerable"]
    not_found = [q for q in qa if q["type"] == "not_found"]

    rows: list[dict] = []

    # --- 1. Retrieval metrics (answerable only; no LLM) ---
    # With only a handful of documents, file-in-top-k is nearly trivial, so we report the
    # harder, more informative metrics too: hit@1 (is the FIRST chunk from the expected
    # source?) and MRR (mean reciprocal rank of the first correct chunk). We retrieve a
    # wider pool than TOP_K so we can locate the rank even when it's beyond k.
    hits_at_1 = 0
    hits_at_k = 0
    reciprocal_ranks: list[float] = []
    for q in answerable:
        pool = retriever.retrieve(q["question"], k=RANK_POOL)
        sources = [h.chunk.source for h in pool]
        # rank (1-based) of the first chunk from the expected source, or None if absent
        rank = next((i + 1 for i, s in enumerate(sources) if s == q["expected_source"]), None)
        at_1 = rank == 1
        at_k = rank is not None and rank <= TOP_K
        hits_at_1 += int(at_1)
        hits_at_k += int(at_k)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
        rows.append(
            {
                "id": q["id"],
                "type": "answerable",
                "question": q["question"],
                "expected_source": q["expected_source"],
                "retrieved_sources": sources[:TOP_K],
                "top_score": round(pool[0].score, 3) if pool else None,
                "rank": rank,
                "retrieval_hit": at_k,
                "hit_at_1": at_1,
                "answer": None,
                "answer_correct": None,
            }
        )

    # --- 2 & 3. Generation: answer correctness + refusal accuracy (need an LLM) ---
    answer_correct = 0
    refusal_correct = 0
    if have_llm:
        provider = get_provider()
        # answerable: generate and check the key fact is present and the answer is grounded
        row_by_id = {r["id"]: r for r in rows}
        for q in answerable:
            res = answer_question(q["question"], retriever, k=TOP_K, provider=provider)
            text_lc = res.answer.lower()
            correct = res.is_grounded and all(s.lower() in text_lc for s in q["answer_contains"])
            answer_correct += int(correct)
            row_by_id[q["id"]]["answer"] = res.answer
            row_by_id[q["id"]]["answer_correct"] = correct
        # not_found: correct iff the system refused
        for q in not_found:
            res = answer_question(q["question"], retriever, k=TOP_K, provider=provider)
            refused = not res.is_grounded
            refusal_correct += int(refused)
            rows.append(
                {
                    "id": q["id"],
                    "type": "not_found",
                    "question": q["question"],
                    "expected_source": None,
                    "retrieved_sources": [h.chunk.source for h in res.hits],
                    "top_score": round(res.hits[0].score, 3) if res.hits else None,
                    "retrieval_hit": None,
                    "answer": res.answer,
                    "answer_correct": refused,
                }
            )

    n = len(answerable)
    return {
        "have_llm": have_llm,
        "provider": get_provider().name if have_llm else None,
        "model": get_provider().model if have_llm else None,
        "n_answerable": n,
        "n_not_found": len(not_found),
        "hits_at_1": hits_at_1,
        "hits_at_k": hits_at_k,
        "mrr": sum(reciprocal_ranks) / n if n else 0.0,
        "answer_correct": answer_correct,
        "refusal_correct": refusal_correct,
        "top_k": TOP_K,
        "rows": rows,
    }


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} ({100 * num / den:.0f}%)" if den else "n/a"


def write_report(r: dict) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Evaluation results\n")
    lines.append(
        "Honest evaluation on a small, hand-written question set "
        f"(`eval/qa_set.jsonl`, {r['n_answerable']} answerable + {r['n_not_found']} "
        "out-of-corpus questions). Regenerate with `make eval`.\n"
    )
    if r["have_llm"]:
        lines.append(
            f"_Generation provider: **{r['provider']}** · model: `{r['model']}` · top-k = {r['top_k']}._\n"
        )
    else:
        lines.append(
            f"_No LLM key configured — retrieval hit-rate only (top-k = {r['top_k']}). "
            "Set a provider key in `.env` and re-run for answer correctness + refusal accuracy._\n"
        )

    lines.append("\n## Metrics\n")
    lines.append("| Metric | Score | What it measures |")
    lines.append("|---|---|---|")
    lines.append(
        f"| Retrieval hit@1 | {_pct(r['hits_at_1'], r['n_answerable'])} | "
        "the *first* retrieved chunk is from the expected source (the hard metric) |"
    )
    lines.append(
        f"| Retrieval hit@{r['top_k']} | {_pct(r['hits_at_k'], r['n_answerable'])} | "
        f"expected source appears in the top-{r['top_k']} chunks the LLM actually sees |"
    )
    lines.append(
        f"| Retrieval MRR | {r['mrr']:.2f} | mean reciprocal rank of the first correct chunk |"
    )
    if r["have_llm"]:
        lines.append(
            f"| Answer correctness (key-fact) | {_pct(r['answer_correct'], r['n_answerable'])} | "
            "grounded answer contains the expected fact (proxy for faithfulness) |"
        )
        lines.append(
            f"| Refusal accuracy | {_pct(r['refusal_correct'], r['n_not_found'])} | "
            "out-of-corpus questions correctly refused (anti-hallucination) |"
        )
    lines.append("")

    # Failures first — the honest part.
    fails = [
        row for row in r["rows"] if row["retrieval_hit"] is False or row["answer_correct"] is False
    ]
    if fails:
        lines.append("## Failures (shown deliberately — this is where the credibility is)\n")
        for row in fails:
            why = []
            if row["retrieval_hit"] is False:
                why.append(
                    f"expected `{row['expected_source']}` not in top-k {row['retrieved_sources']}"
                )
            if row["answer_correct"] is False and row["type"] == "answerable":
                why.append("answer missing the expected key fact")
            if row["answer_correct"] is False and row["type"] == "not_found":
                why.append("should have refused but answered")
            lines.append(f"- **{row['id']}** — _{row['question']}_  \n  {'; '.join(why)}")
            if row.get("answer"):
                lines.append(f"  \n  > {row['answer']}")
        lines.append("")
    else:
        lines.append("_No failures on this run._\n")

    lines.append("## Per-question detail\n")
    lines.append("| id | type | rank | hit@1 | hit@k | answer ok | top sim |")
    lines.append("|---|---|---|---|---|---|---|")
    mark = {True: "✅", False: "❌", None: "—"}
    for row in r["rows"]:
        h1 = mark[row.get("hit_at_1")]
        rh = mark[row["retrieval_hit"]]
        ao = mark[row["answer_correct"]]
        rank = row.get("rank") if row.get("rank") is not None else "—"
        lines.append(
            f"| {row['id']} | {row['type']} | {rank} | {h1} | {rh} | {ao} | {row['top_score']} |"
        )
    lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    r = evaluate()
    write_report(r)
    print(f"Retrieval hit@1:    {_pct(r['hits_at_1'], r['n_answerable'])}")
    print(f"Retrieval hit@{r['top_k']}:    {_pct(r['hits_at_k'], r['n_answerable'])}")
    print(f"Retrieval MRR:      {r['mrr']:.2f}")
    if r["have_llm"]:
        print(f"Answer correctness: {_pct(r['answer_correct'], r['n_answerable'])}")
        print(f"Refusal accuracy:   {_pct(r['refusal_correct'], r['n_not_found'])}")
    else:
        print("No LLM key — set one in .env for answer correctness + refusal accuracy.")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
