# Battery Docs RAG Agent — one command per stage.
# Typical first run:  make install  ->  make index  ->  make ask Q="What is SOH?"
# Everything runs on a laptop CPU. Embeddings are local; only generation calls an LLM.

PYTHON := python3.11
VENV   := .venv
BIN    := $(VENV)/bin
PY     := $(BIN)/python

.DEFAULT_GOAL := help

.PHONY: help venv install index ask eval app agent test format lint clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv:  ## Create the Python 3.11 virtual environment
	$(PYTHON) -m venv $(VENV)

install: venv  ## Install pinned dependencies + the project (editable) into the venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e .  # makes `import src` work everywhere

index:  ## Build the FAISS vector index from data/corpus/ (deterministic)
	$(PY) scripts/build_index.py

ask:  ## Ask a question, e.g. `make ask Q="What is the nominal capacity?"`
	$(PY) -m src.rag.cli ask "$(Q)"

eval:  ## Run the hand-written eval set and write reports/results.md
	$(PY) eval/run_eval.py

agent:  ## Run the agentic test-report mode (Phase 5), e.g. `make agent F=data/test_reports/report_01.md`
	$(PY) -m src.agent.cli "$(F)"

app:  ## Run the optional Streamlit chat UI with visible citations
	$(BIN)/streamlit run app/streamlit_app.py

test:  ## Run the test suite
	$(BIN)/pytest -q

format:  ## Auto-format with black + ruff
	$(BIN)/black src tests scripts eval app
	$(BIN)/ruff check --fix src tests scripts eval app

lint:  ## Lint without modifying files
	$(BIN)/ruff check src tests scripts eval app
	$(BIN)/black --check src tests scripts eval app

clean:  ## Remove caches and the generated index (keeps the corpus)
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__ data/index/*.faiss data/index/*.json
	find . -name '*.pyc' -delete
