# Interview notes — the questions a technical interviewer will ask

Crisp answers to the five questions most likely to come up about this RAG system, plus the
design rationale behind each. Written so I can *own* the project, not just describe it.

---

## 1. "How do you stop it hallucinating?"

Three layers, in order of importance:

1. **Grounding prompt.** The system prompt instructs the model to answer *only* from the
   retrieved passages, and — crucially — to reply exactly *"Not found in the provided
   documents"* when the passages don't support an answer. For an engineering/safety tool, a
   confident wrong answer is worse than a refusal, so refusal is a first-class behaviour.
2. **Citations.** Every answer cites the `[n]` labels of the chunks it used, and the CLI/UI
   print the source file and section for each. A human can verify any claim in seconds.
   Citations don't *prevent* hallucination, they make it *detectable* — which is what makes
   the tool trustworthy in practice.
3. **Retrieval backstop.** If the top retrieved chunk's similarity is below a threshold, the
   system refuses *without even calling the LLM* — cheap insurance against garbage queries.

Honest caveat I volunteer: RAG **reduces** hallucination (the model is anchored to real
text) but does not **eliminate** it — the model can still misread or over-generalize from
the context. That's exactly why I evaluate (next answer) and why citations exist.

## 2. "How did you evaluate retrieval, and what are the numbers?"

A small, hand-written eval set (`eval/qa_set.jsonl`): ~17 answerable questions, each tagged
with the source document that should answer it, plus a few deliberately out-of-corpus
questions. I report:

- **hit@1** — is the *first* retrieved chunk from the expected source? (the hard metric)
- **hit@k** — does the expected source appear in the top-k the LLM actually sees?
- **MRR** — mean reciprocal rank of the first correct chunk.
- **Answer correctness** — does the generated answer contain the expected key fact? (a
  transparent keyword proxy for faithfulness, reported as a lower bound, not an LLM-judge).
- **Refusal accuracy** — are out-of-corpus questions correctly refused?

I deliberately separate **retrieval** from **generation**: if the right chunk never comes
back, no prompt can fix it, so retrieval is measured on its own first. I also show the
**failure cases** — e.g. "difference between SOC and SOH" misses hit@1 because that concept
lives in two documents, so the top chunk comes from the related-but-not-tagged one (hit@k
still catches it). Showing a miss and explaining it is where the credibility is.

> ⚠️ I keep the corpus small and the questions self-written, so I do **not** claim these
> numbers generalize — they prove the pipeline works and that I can measure it, not that
> it's a tuned production retriever.

## 3. "Why those chunk settings (size and overlap)?"

~500 tokens with ~60 tokens of overlap, split on structure (heading → paragraph →
sentence). The trade-off:

- **Too small** → context is lost; an answer that spans two chunks gets split and neither
  retrieves well on its own.
- **Too big** → retrieval is diluted; one chunk averages several topics, so its vector
  matches questions only fuzzily.

**Overlap** means a fact sitting on a chunk boundary still appears whole in at least one
chunk. **Structure-aware** splitting keeps chunks aligned with the document's own sections,
which both improves retrieval and makes a citation land on a meaningful unit (a real
section, not an arbitrary 500-token window).

## 4. "Why a thin custom stack instead of LangChain / LlamaIndex?"

Because this repo's *job* is to prove I understand RAG internals. Hiding chunking,
embedding, cosine retrieval, and the grounding prompt behind a framework would defeat that
— I can explain and defend every line here. The honest trade-off: at work, on a real
product, I'd reach for a mature framework for speed and battle-tested components. For a
portfolio piece that has to survive 30 minutes of technical questions, transparency wins.

Same logic for **local embeddings** (sentence-transformers / MiniLM) and **exact FAISS**
(`IndexFlatIP`): free, offline, deterministic, and exact — no approximate-nearest-neighbour
error to reason about at this corpus size. If the corpus grew to millions of chunks I'd
switch to an IVF/HNSW index and trade a little recall for speed.

## 5. "Why cosine similarity, and how does an embedding actually retrieve the right chunk?"

An **embedding** maps text to a vector so that texts with similar *meaning* point in
similar directions. I embed every chunk once at index time and the question at query time
with the **same** model (a query embedded by a different model lives in a different space
and won't match). **Cosine similarity** measures the angle between two vectors — alignment
of meaning — which is the right metric because we care about *direction* (semantics), not
*magnitude* (which for embeddings mostly reflects text length). I L2-normalize the vectors,
so a FAISS inner-product search gives cosine ranking directly. The question's vector
"points toward" the chunks that answer it, and those come back first.

---

## Bonus: "What's the agentic mode, and how is it different from the RAG Q&A?"

(Phase 5.) The RAG path is a **single** retrieve→generate step. The agent path is a
**loop**: given a battery test-report PDF, it calls tools (parse the PDF, extract a field,
convert units) and decides the next step from the previous result, building a structured
diagnostic summary. A single prompt is one shot; an agent can take several, with tool calls
in between. I keep the loop **bounded** (a max step count) and **observable** (every tool
call is logged) so it can't run away and so I can explain exactly what it did.

## Bonus: "Where does it fail / what would you do next?"

- **Tables in datasheets** — text extraction can mangle table structure; a value in a messy
  table is the most likely thing to be retrieved imperfectly.
- **Multi-hop questions** — questions needing two facts from two documents are harder; top-k
  retrieval may bring back one and miss the other.
- **Paraphrased standard clauses** — I summarize standards in my own words, so the system
  can describe scope but must (correctly) refuse exact normative clause text.
- **Next steps:** a re-ranker over the top-k, an LLM-judge faithfulness metric, hybrid
  (keyword + vector) retrieval for exact part numbers, and table-aware ingestion.
