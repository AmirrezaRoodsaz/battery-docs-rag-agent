# Corpus provenance & licensing

This directory holds the document corpus the RAG system reasons over, plus the synthesized
test reports used by the agentic mode. **Every document here is public, redistributable, or
self-authored.** Nothing proprietary — no thesis data, no AVL HV-Check material, no
manufacturer PDFs that forbid redistribution.

> **Hard rule for contributors (and for me):** if a document's license does not clearly permit
> redistribution, *link to it* rather than committing it, and record that here. The `.gitignore`
> blocks `*.pdf` in `corpus/` and `test_reports/` by default for exactly this reason.

## Layout

```
data/
├── corpus/            # the searchable knowledge base (self-authored Markdown notes ship here)
├── test_reports/      # synthesized battery test reports for the agentic demo (Phase 5)
└── index/             # generated FAISS index (gitignored, rebuilt by `make index`)
```

## What ships in this repo

| Document | Type | Source / author | License |
|---|---|---|---|
| `corpus/soh_methods.md` | Self-authored notes | Amirreza Roodsaz, written for this repo | MIT (this repo) |
| `corpus/li_ion_basics.md` | Self-authored notes | Amirreza Roodsaz, written for this repo | MIT (this repo) |
| `corpus/standards_overview.md` | Self-authored paraphrase/summary | Amirreza Roodsaz | MIT (this repo) |
| `corpus/example_cell_datasheet.md` | Synthesized (fictional cell) | Amirreza Roodsaz | MIT (this repo) |
| `test_reports/*.md` | Synthesized test reports | Amirreza Roodsaz | MIT (this repo) |

These are written fresh for the repo specifically so they are unambiguously mine to publish.
The "example cell datasheet" describes a **fictional** cell with realistic-but-invented numbers,
so it carries no manufacturer copyright.

## Standards (ISO 26262 / UN 38.3 / IEC 62660)

The full text of these standards is **copyrighted** and is **not** included. `corpus/standards_overview.md`
contains only my own plain-language summary of each standard's *scope and purpose* — the kind of
description freely available in public abstracts — written in my own words. For authoritative text,
consult the official standard via ISO / your national standards body. Links, not text:

- ISO 26262 (road-vehicle functional safety): https://www.iso.org/standard/68383.html
- UN 38.3 (transport of lithium batteries): UN Manual of Tests and Criteria, Part III, 38.3
- IEC 62660 (Li-ion cells for EV propulsion): https://webstore.iec.ch/

## Adding manufacturer datasheets locally

If you want to test retrieval against a real datasheet, drop the PDF into `data/corpus/`. It will be
**gitignored** (so you never accidentally redistribute it), indexed locally, and citable in answers.
Record what you added — and confirm its license permits your use — but do not commit it unless the
license clearly allows redistribution.
