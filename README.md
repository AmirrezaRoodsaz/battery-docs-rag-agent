# Battery Docs RAG Agent

**Ask natural-language questions over a corpus of battery & engineering documents and get
accurate, *cited* answers — and the system says *"not found in the provided documents"*
rather than make something up.**

A domain-anchored Retrieval-Augmented Generation (RAG) system: grounded, cited, and
evaluated. Built as a thin custom stack (no LangChain/LlamaIndex) so every step —
chunking, embedding, cosine retrieval, the grounding prompt, citation formatting — is plain,
readable code. Local embeddings + FAISS run on a laptop with no paid infra; generation is
provider-agnostic (Gemini by default, swappable to Claude / OpenAI / local Ollama).

```text
$ make ask Q="Who won the 2010 FIFA World Cup?"
╭────────────────────────── Answer ──────────────────────────╮
│ Not found in the provided documents.                       │
╰────────────────────────────────────────────────────────────╯
Sources:
  [1] example_cell_datasheet.md — … (similarity 0.02)
provider: (none) · model: (retrieval miss — no LLM call)
```
*An out-of-corpus question is refused — without even calling the LLM. Grounding first,
fluency second.*

---

## Problem & motivation

Battery and automotive engineers work against a wall of dense technical documents — cell
**datasheets**, **test reports**, BMS specs, and standards like **ISO 26262** / **UN 38.3** /
**IEC 62660**. Finding the right value or clause is slow and error-prone, and a naive "chat
with your PDF" demo doesn't help, because a confidently wrong answer about a safety standard
is worse than no answer.

The valuable, defensible problem this solves:

> Let an engineer ask questions over a battery/engineering corpus and get answers that are
> **grounded** (drawn only from the documents), **cited** (every claim points back to its
> source chunk), and **honest** (the system refuses when the answer isn't in the corpus).

This is retrieval-augmented generation done *correctly* — applied to a domain I understand
from my Master's work on EV battery **State of Health (SOH)**.

## Architecture

```
                 ┌─────────────┐   ┌────────────┐   ┌──────────────┐
  documents ───▶ │   ingest    │──▶│   chunk    │──▶│   embed      │
  (md / pdf)     │ load + clean│   │ structure- │   │ MiniLM (local)│
                 │  + locators │   │  aware     │   │ L2-normalized │
                 └─────────────┘   └────────────┘   └──────┬───────┘
                                                            ▼
                                                     ┌──────────────┐
  question ───────────────────────────────────────▶ │   retrieve   │  top-k cosine
                                                     │  (FAISS,     │  (+ optional MMR)
                                                     │   exact IP)  │  → chunks + metadata
                                                     └──────┬───────┘
                                                            ▼
                                                     ┌──────────────┐
                                                     │  generate    │  grounding prompt:
                                                     │ (any provider│  answer ONLY from context,
                                                     │  via one env)│  cite [n], else "not found"
                                                     └──────┬───────┘
                                                            ▼
                                                  answer + inline citations
```

| Stage | File | What it does |
|---|---|---|
| Ingest | [`src/ingest/load.py`](src/ingest/load.py) | Markdown (heading-path locators) + PDF (page locators) → blocks that remember their source |
| Chunk | [`src/ingest/chunk.py`](src/ingest/chunk.py) | structure-aware ~500-token chunks, ~60 overlap |
| Embed | [`src/index/embed.py`](src/index/embed.py) | local `all-MiniLM-L6-v2`, L2-normalized (so inner product = cosine) |
| Store | [`src/index/vectorstore.py`](src/index/vectorstore.py) | exact FAISS `IndexFlatIP` + JSON metadata sidecar |
| Retrieve | [`src/rag/retrieve.py`](src/rag/retrieve.py) | top-k cosine, optional MMR re-ranking |
| Generate | [`src/rag/generate.py`](src/rag/generate.py) | grounding prompt + "not found" refusal |
| Cite | [`src/rag/cite.py`](src/rag/cite.py) | label chunks `[n]`, render Sources list |
| LLM layer | [`src/llm/provider.py`](src/llm/provider.py) | provider-agnostic: gemini \| claude \| openai \| ollama |

## Corpus

Public / self-authored only — provenance and license per document in
[`data/README.md`](data/README.md). Ships: self-written notes on
[SOH methods](data/corpus/soh_methods.md) and [Li-ion basics](data/corpus/li_ion_basics.md),
a [plain-language standards overview](data/corpus/standards_overview.md) (my own words — no
copyrighted standard text), and a **fictional** [example datasheet](data/corpus/example_cell_datasheet.md)
with invented numbers. **Nothing proprietary** — no thesis or AVL data. Any real manufacturer
PDF you add locally is gitignored so it's never accidentally redistributed.

## Anti-hallucination design

This is the part a skeptical senior engineer cares about most. Three layers:

1. **Grounding prompt** — answer *only* from the retrieved passages; reply exactly *"Not
   found in the provided documents"* when unsupported. Refusal is a first-class behaviour,
   not an error.
2. **Citations** — every answer cites the `[n]` of each chunk it used; the Sources list maps
   `[n]` → file, section, and similarity score. This makes any claim checkable in seconds.
   Citations don't prevent hallucination, they make it *detectable* — which is what makes the
   tool trustworthy.
3. **Retrieval backstop** — if the top chunk's similarity is below a threshold, the system
   refuses *without calling the LLM* (cheap insurance against garbage queries).

> RAG **reduces** hallucination (the model is anchored to real text) but does not
> **eliminate** it (it can misread context) — which is exactly why this repo also evaluates.

## Evaluation

Honest, transparent eval on a small hand-written set (`eval/qa_set.jsonl`: 17 answerable +
3 out-of-corpus questions). Retrieval is measured **separately** from generation — if the
right chunk never comes back, no prompt can fix it. Full results + per-question detail in
[`reports/results.md`](reports/results.md); regenerate with `make eval`.

| Metric | Score | What it measures |
|---|---|---|
| Retrieval **hit@1** | **16/17 (94%)** | the *first* chunk is from the expected source (the hard metric) |
| Retrieval **hit@4** | **17/17 (100%)** | expected source appears in the top-4 the LLM sees |
| Retrieval **MRR** | **0.97** | mean reciprocal rank of the first correct chunk |
| Answer correctness | _run with a key_ | grounded answer contains the expected fact (faithfulness proxy) |
| Refusal accuracy | _run with a key_ | out-of-corpus questions correctly refused |

**The honest failure** (the credible part): `q07 — "difference between SOC and SOH"` misses
hit@1, because that concept lives in *two* documents, so the top chunk comes from the
related-but-not-tagged one. hit@4 still catches it. I keep the corpus small and the questions
self-written, so I do **not** claim these numbers generalize — they prove the pipeline works
and that I can measure it, not that it's a tuned production retriever.

> Answer-correctness and refusal-accuracy require a generation call, so they're computed when
> an LLM key is set in `.env`. Set one and run `make eval` to fill those rows in
> `reports/results.md`.

## How to run

**Prerequisites:** Python 3.11. Embeddings run locally (no key). Generation needs one provider
key — Gemini's free tier is the default.

```bash
make install                       # venv + pinned deps (Python 3.11)
make index                         # build the local FAISS index from data/corpus/ (~7 s)

cp .env.example .env               # then add your GOOGLE_API_KEY (free: aistudio.google.com)
make ask Q="What is the maximum charge voltage of the AR-2100?"
make ask Q="What is the difference between SOC and SOH?"
make eval                          # retrieval + answer correctness + refusal accuracy
make test                          # 33 tests: chunking, retrieval, citations, grounding, agent
make app                           # Streamlit UI (paste your key in the sidebar — no .env needed)
make agent F=data/test_reports/report_02_degraded.md   # agentic diagnostic on a test report
```

Two things work **with no key at all**: building/querying the index for retrieval
(`python -m src.rag.cli retrieve "..."`) and the "not found" refusal path. Cost is near-zero:
local embeddings are free; with Gemini Flash the full 20-question eval is a handful of cheap
calls.

To swap providers, set `LLM_PROVIDER` in `.env` to `claude`, `openai`, or `ollama` (local,
also keyless) — no code change.

## Demo (Streamlit UI)

`make app` opens a browser UI at `http://localhost:8501`. **Paste your API key in the
sidebar** — it lives only in that session's memory and is never written to disk or committed
(so you don't need a `.env` to try it). Two tabs:

- **💬 Ask (RAG)** — type a question, get a grounded answer with a **Sources** list, and
  expand *"Show the exact retrieved chunks"* to see precisely what the answer was grounded on.
  Transparency is the point: you can watch it cite, and watch it refuse.
- **🩺 Diagnose a test report (agent)** — pick a synthesized test report and run the agent
  (below); the verdict, the structured summary, the JSON, and the full tool-call trace are all
  shown.

Embeddings run locally, so retrieval works the moment the app loads; only generation uses your key.

## Agentic test-report mode

Beyond Q&A, the repo includes a **bounded, observable agent** that turns a battery
test-report into a structured diagnosis. It differs from the RAG path in shape: RAG is one
`retrieve → generate` step; the agent is a **loop** ([`src/agent/agent_loop.py`](src/agent/agent_loop.py)):

```
read report → [ LLM picks a tool → tool runs → observation ]* → LLM writes the diagnosis
```

The LLM **reads** values from the report and **decides** which tool to call; the
[**tools**](src/agent/tools.py) do the arithmetic and threshold logic — `compute_soh`,
`resistance_growth_pct`, `evaluate_health` — so the numbers are **never hallucinated**. The loop
is **bounded** (a hard `max_steps` cap, it can't run away) and **observable** (every step is
logged and shown). On the deliberately-degraded sample it flags capacity-EOL (SOH 77 %), the
resistance growth, and a thermal limit excursion, and emits both Markdown and JSON.

```bash
make agent F=data/test_reports/report_02_degraded.md   # or report_01_healthy.md
```

## What I learned / limitations / next steps

- **Grounding + citations matter more than the model.** The defensible engineering here is
  the refusal behaviour and verifiable sources, not the choice of LLM — which is exactly why
  the LLM is swappable behind one interface.
- **Separate retrieval from generation when you evaluate.** hit@1 vs hit@k told me *where*
  the system is weak (multi-document concepts) in a way an end-to-end score would have hidden.
- **Small clean corpus inflates easy metrics.** File-level hit-rate was 100% and meaningless
  with 4 docs; hit@1 and MRR are the honest metrics, and they surfaced a real miss.
- **Where it fails:** tables in datasheets (extraction can mangle them), multi-hop questions,
  and exact normative clause text (correctly refused, since I only summarize standards).
- **Next steps:** a re-ranker over top-k, an LLM-judge faithfulness metric, hybrid
  (keyword + vector) retrieval for exact part numbers, table-aware ingestion, and letting the
  agent pull rated values from the datasheet corpus via retrieval rather than from the report alone.

## Repository layout

```
data/corpus/        self-authored, publishable corpus (+ data/README.md provenance)
src/ingest/         load.py, chunk.py
src/index/          embed.py, vectorstore.py
src/rag/            retrieve.py, generate.py, cite.py, cli.py
src/llm/            provider.py (gemini | claude | openai | ollama)
src/agent/          (Phase 5) tool-using test-report mode
eval/               qa_set.jsonl + run_eval.py
reports/            results.md (eval) + interview_notes.md
tests/              pytest: chunking, retrieval, citations, grounding
app/                (Phase 5) Streamlit chat UI with visible citations
```

## Citation & acknowledgements

An independent, self-authored learning project. The corpus is written specifically for this
repo or synthesized (the example datasheet is fictional); no proprietary or third-party
copyrighted material is redistributed. Standard summaries are paraphrased in my own words —
consult the official ISO/UN/IEC documents for authoritative requirements.

## License

[MIT](LICENSE) © 2026 Amirreza Roodsaz — code only. Corpus licensing is tracked per document
in [`data/README.md`](data/README.md).

---

> _A personal note: I built this out of curiosity and a wish to learn something new — not for any
> company or university. I had a problem in mind that genuinely interested me, and I wanted to solve
> it while picking up new skills along the way. It is by no means complete or fully professional;
> it's an honest learning project, and I'm sharing it in that spirit._
