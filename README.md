# Battery Docs RAG Agent

**Ask natural-language questions over a corpus of battery & engineering documents and get
accurate, *cited* answers — and have the system say "not found in the provided documents"
rather than make something up.**

> 🚧 **Status: in active development.** Phase 1 (scaffold) is in. The ingest → index →
> retrieve → generate(+cite) core lands next, then a small honest evaluation, then an optional
> agentic test-report mode and a Streamlit UI. Building in small, reviewable commits.

---

## Why this project

Battery and automotive engineers work against a wall of dense technical documents — cell
**datasheets**, **test reports**, BMS specs, and standards like **ISO 26262** / **UN 38.3** /
**IEC 62660**. Finding the right value or clause is slow and error-prone. A naive "chat with your
PDF" demo doesn't solve it, because a confidently wrong answer about a safety standard is worse
than no answer.

The valuable, defensible problem:

> Let an engineer ask questions over a battery/engineering corpus and get answers that are
> **grounded** (drawn only from the documents), **cited** (every claim points back to its source
> chunk), and **honest** (the system refuses when the answer isn't in the corpus).

This is retrieval-augmented generation done *correctly* — applied to a domain I actually
understand from my Master's work on EV battery **State of Health (SOH)**.

## What it does (target)

- **Grounded, cited Q&A** over a local document corpus — the anti-hallucination centerpiece.
- **"Not found" behavior** when the corpus doesn't support an answer (no guessing).
- **Provider-agnostic** generation — Gemini by default, swappable to Claude / OpenAI / local Ollama.
- **Local, free embeddings** (`sentence-transformers`) and a local **FAISS** index — runs on a laptop, no paid infra.
- **A small, honest evaluation** — hand-written Q&A measuring retrieval hit-rate and answer faithfulness.
- **(Stretch) Agentic mode** — given a battery test-report PDF, an agent extracts key parameters
  (capacity, SOH, internal resistance, temperature range, anomalies) and produces a structured
  diagnostic summary.

## Architecture

```
                 ┌─────────────┐   ┌────────────┐   ┌──────────────┐
  documents ───▶ │   ingest    │──▶│   chunk    │──▶│   embed      │
  (md / pdf)     │ load + clean│   │ ~structure │   │ MiniLM (local)│
                 └─────────────┘   └────────────┘   └──────┬───────┘
                                                            ▼
                                                     ┌──────────────┐
  question ───────────────────────────────────────▶ │   retrieve   │  top-k cosine
                                                     │  (FAISS)     │  + source metadata
                                                     └──────┬───────┘
                                                            ▼
                                                     ┌──────────────┐
                                                     │  generate    │  grounding prompt:
                                                     │  (LLM, any   │  answer ONLY from context,
                                                     │   provider)  │  cite sources, else "not found"
                                                     └──────┬───────┘
                                                            ▼
                                                  answer + inline citations
```

Design choice: a **thin custom stack** (no LangChain/LlamaIndex), so every step — chunking,
embedding, cosine retrieval, the grounding prompt, citation formatting — is plain, readable code
I can explain line by line in an interview. Clever vs. explainable → explainable.

## Corpus

Public / self-authored only. The repo ships self-written notes on SOH methods, Li-ion basics, a
plain-language standards overview, and a **fictional** example datasheet — all unambiguously mine
to publish. Standard texts (ISO/UN/IEC) are summarized in my own words, never copied. Provenance
and licensing per document: [`data/README.md`](data/README.md). Nothing proprietary, no thesis or
AVL data.

## How to run

> Full commands land with the Phase 2–3 code. The intended flow:

```bash
make install                       # venv + pinned deps (Python 3.11)
make index                         # build the local FAISS index from data/corpus/
make ask Q="What is State of Health and how is it measured?"
```

Embeddings run locally and need no key. Generation uses your chosen LLM provider — copy
`.env.example` to `.env` and set the key for the one you use (Gemini's free tier is the default).

## Roadmap

- [x] **Phase 1** — repo scaffold, licensing, secrets hygiene, conventions
- [ ] **Phase 2** — ingest + chunk + embed + FAISS index (`make index`)
- [ ] **Phase 3** — retrieve + generate + cite + "not found"; CLI (`make ask`)
- [ ] **Phase 4** — evaluation set + honest results; full README with screenshot
- [ ] **Phase 5** — agentic test-report mode + Streamlit UI

## License

[MIT](LICENSE) © 2026 Amirreza Roodsaz — code only. Corpus licensing is tracked per document in
[`data/README.md`](data/README.md).

---

> _A personal note: I built this out of curiosity and a wish to learn something new — not for any
> company or university. I had a problem in mind that genuinely interested me, and I wanted to solve
> it while picking up new skills along the way. It is by no means complete or fully professional;
> it's an honest learning project, and I'm sharing it in that spirit._
