"""Streamlit UI — grounded RAG Q&A with VISIBLE citations, plus the agentic report mode.

Transparency sells this project, so the UI deliberately shows the machinery: every answer
displays its citations and lets you expand the exact retrieved chunks it was grounded on,
and the agent tab shows its tool-by-tool trace.

API key: paste it in the sidebar (it lives only in this session's memory — it is never
written to disk or committed). Embeddings are local and need no key; only generation does.

Run with:  make app   (or)   streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

# Map each provider to the env var its key goes in (ollama is keyless).
KEY_ENV = {
    "gemini": "GOOGLE_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "ollama": None,
}

st.set_page_config(page_title="Battery Docs RAG Agent", page_icon="🔋", layout="wide")


@st.cache_resource(show_spinner="Loading index + embedding model…")
def get_retriever():
    """Load the FAISS index + local embedder once per session (heavy to build)."""
    from src.rag.retrieve import Retriever

    return Retriever.from_index()


def configure_provider(provider: str, api_key: str, model: str):
    """Push the UI's provider/key/model into the environment for get_provider()."""
    os.environ["LLM_PROVIDER"] = provider
    env = KEY_ENV.get(provider)
    if env and api_key:
        os.environ[env] = api_key
    if model:
        os.environ[
            {
                "gemini": "GEMINI_MODEL",
                "claude": "CLAUDE_MODEL",
                "openai": "OPENAI_MODEL",
                "ollama": "OLLAMA_MODEL",
            }[provider]
        ] = model


# --- Sidebar: provider + key ------------------------------------------------------------

st.sidebar.title("🔋 Settings")
provider = st.sidebar.selectbox("LLM provider", list(KEY_ENV), index=0)
needs_key = KEY_ENV[provider] is not None
api_key = st.sidebar.text_input(
    f"{provider.title()} API key" if needs_key else "API key (not needed for Ollama)",
    type="password",
    help="Stored only in this session's memory — never written to disk or committed.",
    disabled=not needs_key,
)
default_model = {
    "gemini": "gemini-1.5-flash",
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "ollama": "llama3.1:8b",
}[provider]
model = st.sidebar.text_input("Model", value=default_model)
top_k = st.sidebar.slider("Chunks to retrieve (k)", 1, 8, 4)
use_mmr = st.sidebar.checkbox("MMR re-ranking (more diverse chunks)", value=False)
st.sidebar.caption("Embeddings run locally — no key needed. Only generation calls the LLM.")

configure_provider(provider, api_key, model)

# Guard: index must be built.
try:
    retriever = get_retriever()
except FileNotFoundError:
    st.error("No index found. Run `make index` first to build it from data/corpus/.")
    st.stop()


st.title("Battery Docs RAG Agent")
st.caption(
    "Grounded, cited answers over battery & engineering documents — and a refusal when the answer isn't in the corpus."
)

tab_ask, tab_agent = st.tabs(["💬 Ask (RAG)", "🩺 Diagnose a test report (agent)"])

# --- Tab 1: grounded Q&A ----------------------------------------------------------------

with tab_ask:
    st.subheader("Ask a question")
    st.caption(
        "Try: *What is the maximum charge voltage of the AR-2100?* · *Difference between SOC and SOH?* · *What is the price of the AR-2100?* (watch it refuse)"
    )
    question = st.text_input(
        "Question", key="q", placeholder="What is State of Health and how is it measured?"
    )
    if st.button("Ask", type="primary") and question:
        from src.llm.provider import LLMError, get_provider
        from src.rag.generate import answer_question

        with st.spinner("Retrieving + generating…"):
            try:
                provider_obj = None if not needs_key else get_provider()
                result = answer_question(
                    question,
                    retriever,
                    k=top_k,
                    use_mmr=use_mmr,
                    provider=provider_obj if needs_key else None,
                )
            except LLMError as e:
                st.warning(f"{e}")
                st.info(
                    "Tip: paste your API key in the sidebar, or switch provider to Ollama (keyless, local)."
                )
                result = None

        if result is not None:
            if result.is_grounded:
                st.success(result.answer)
            else:
                st.warning(result.answer + "  \n_(refused — not supported by the corpus)_")
            st.caption(f"provider: {result.provider} · model: {result.model}")

            st.markdown("**Sources**")
            for c in result.citations:
                st.markdown(
                    f"- `[{c.label}]` **{c.source}** — {c.locator}  ·  similarity `{c.score:.2f}`"
                )

            with st.expander("Show the exact retrieved chunks (what the answer was grounded on)"):
                for c, hit in zip(result.citations, result.hits, strict=False):
                    st.markdown(f"**[{c.label}] {c.source} — {c.locator}**  ·  sim `{c.score:.2f}`")
                    st.text(hit.chunk.text)
                    st.divider()

# --- Tab 2: agentic test-report diagnostics ---------------------------------------------

with tab_agent:
    st.subheader("Diagnose a battery test report")
    st.caption(
        "A bounded, observable agent loop: it reads the report, calls tools to compute SOH / resistance growth / a verdict, and writes a structured diagnostic. Needs an LLM key."
    )

    reports_dir = Path("data/test_reports")
    report_files = sorted(p.name for p in reports_dir.glob("*.md")) if reports_dir.exists() else []
    chosen = st.selectbox("Test report", report_files) if report_files else None

    if st.button("Run diagnostic agent", type="primary") and chosen:
        from src.agent.agent_loop import diagnose_report
        from src.llm.provider import LLMError

        with st.spinner("Agent running (reading report, calling tools)…"):
            try:
                result = diagnose_report(reports_dir / chosen)
            except LLMError as e:
                st.warning(f"{e}")
                st.info("Paste your API key in the sidebar (the agent needs a generation model).")
                result = None

        if result is not None:
            verdict = result.verdict
            (
                st.error
                if "END-OF-LIFE" in verdict
                else st.warning if "DEGRADED" in verdict else st.success
            )(f"Verdict: {verdict}")
            st.markdown(result.summary_markdown)
            st.markdown("**Structured output (JSON)**")
            st.code(result.to_json(), language="json")

            with st.expander("Show the agent's tool-call trace (bounded + observable)"):
                for s in result.steps:
                    line = f"**[{s.n}] {s.action}**"
                    if s.tool:
                        line += f" → `{s.tool}({s.args})`"
                    st.markdown(line)
                    if s.observation:
                        st.caption(f"obs: {s.observation}")
