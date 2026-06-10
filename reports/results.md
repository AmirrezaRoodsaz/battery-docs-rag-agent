# Evaluation results

Honest evaluation on a small, hand-written question set (`eval/qa_set.jsonl`, 17 answerable + 3 out-of-corpus questions). Regenerate with `make eval`.

_No LLM key configured — retrieval hit-rate only (top-k = 4). Set a provider key in `.env` and re-run for answer correctness + refusal accuracy._


## Metrics

| Metric | Score | What it measures |
|---|---|---|
| Retrieval hit@1 | 16/17 (94%) | the *first* retrieved chunk is from the expected source (the hard metric) |
| Retrieval hit@4 | 17/17 (100%) | expected source appears in the top-4 chunks the LLM actually sees |
| Retrieval MRR | 0.97 | mean reciprocal rank of the first correct chunk |

_No failures on this run._

## Per-question detail

| id | type | rank | hit@1 | hit@k | answer ok | top sim |
|---|---|---|---|---|---|---|
| q01 | answerable | 1 | ✅ | ✅ | — | 0.701 |
| q02 | answerable | 1 | ✅ | ✅ | — | 0.509 |
| q03 | answerable | 1 | ✅ | ✅ | — | 0.691 |
| q04 | answerable | 1 | ✅ | ✅ | — | 0.65 |
| q05 | answerable | 1 | ✅ | ✅ | — | 0.602 |
| q06 | answerable | 1 | ✅ | ✅ | — | 0.363 |
| q07 | answerable | 2 | ❌ | ✅ | — | 0.487 |
| q08 | answerable | 1 | ✅ | ✅ | — | 0.609 |
| q09 | answerable | 1 | ✅ | ✅ | — | 0.745 |
| q10 | answerable | 1 | ✅ | ✅ | — | 0.658 |
| q11 | answerable | 1 | ✅ | ✅ | — | 0.459 |
| q12 | answerable | 1 | ✅ | ✅ | — | 0.402 |
| q13 | answerable | 1 | ✅ | ✅ | — | 0.578 |
| q14 | answerable | 1 | ✅ | ✅ | — | 0.592 |
| q15 | answerable | 1 | ✅ | ✅ | — | 0.396 |
| q16 | answerable | 1 | ✅ | ✅ | — | 0.635 |
| q17 | answerable | 1 | ✅ | ✅ | — | 0.533 |
