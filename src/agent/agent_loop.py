"""A bounded, observable test-report agent.

Given a battery test-report document, the agent produces a structured diagnostic summary
(Markdown + JSON). It is a ReAct-style loop:

    read report  ->  [ LLM picks a tool  ->  tool runs  ->  observation ]*  ->  LLM finishes

How it differs from the RAG Q&A (an interview question): the RAG path is ONE
retrieve→generate step. This is a LOOP — the model decides the next action from the previous
observation, calling tools (compute SOH, compute resistance growth, evaluate thresholds) in
sequence. The model reads values from the report and orchestrates; the *tools* do the
arithmetic and threshold logic, so numbers are never hallucinated.

Two safety properties, by design:
  - BOUNDED: a hard `max_steps` cap — the loop cannot run away.
  - OBSERVABLE: every step (thought, tool, args, observation) is logged and returned, so you
    can see exactly what the agent did and why.

Provider-agnostic: the loop only needs text completion, so it works with any provider in
src/llm/provider.py. It needs an LLM key to run (set in .env or passed to the UI).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.agent.tools import run_tool, tools_description
from src.ingest.load import load_document
from src.llm.provider import LLMProvider, get_provider

MAX_STEPS = 8

SYSTEM_PROMPT = f"""You are a battery test-report diagnostic agent. You are given the full \
text of one cell test report. Your job: extract the key measurements, use TOOLS to compute \
State of Health, resistance growth, and a health verdict, then write a structured diagnostic \
summary.

You must NOT do arithmetic yourself or decide thresholds yourself — call the tools for that.
Read the numeric values from the report and pass them to the tools.

Available tools:
{tools_description()}

Respond with EXACTLY ONE JSON object per turn, and nothing else. Two shapes:

To call a tool:
{{"thought": "<brief reasoning>", "action": "call_tool", "tool": "<name>", "args": {{...}}}}

To finish (only after you have SOH, resistance growth, and an evaluate_health verdict):
{{"thought": "<brief>", "action": "finish",
  "metrics": {{"soh_pct": <num>, "resistance_growth_pct": <num>, "max_temp_c": <num>,
               "verdict": "<from evaluate_health>", "flags": [<from evaluate_health>]}},
  "summary_markdown": "<a concise Markdown diagnostic summary for an engineer>"}}

Rules: one JSON object only, no code fences, no prose outside the JSON. Use exact tool output \
values in your metrics and summary."""


@dataclass
class AgentStep:
    n: int
    thought: str
    action: str
    tool: str | None = None
    args: dict | None = None
    observation: str | None = None


@dataclass
class DiagnosticReport:
    report_name: str
    verdict: str
    metrics: dict
    summary_markdown: str
    steps: list[AgentStep] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {"report": self.report_name, "verdict": self.verdict, "metrics": self.metrics},
            indent=2,
        )


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model response, tolerating code fences/prose."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    # Find the first balanced {...} span.
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("no JSON object in response")
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start : i + 1])
    raise ValueError("unbalanced JSON in response")


def diagnose_report(
    report_path: Path,
    provider: LLMProvider | None = None,
    max_steps: int = MAX_STEPS,
) -> DiagnosticReport:
    """Run the agent loop on a test report and return a structured diagnostic."""
    doc = load_document(report_path)
    report_text = doc.text
    llm = provider or get_provider()

    history: list[str] = [f"REPORT TEXT:\n{report_text}"]
    steps: list[AgentStep] = []

    for n in range(1, max_steps + 1):
        user = "\n\n".join(history) + "\n\nRespond with one JSON object."
        raw = llm.complete(SYSTEM_PROMPT, user)
        try:
            msg = _extract_json(raw)
        except (ValueError, json.JSONDecodeError):
            history.append(
                "OBSERVATION: your last reply was not valid JSON. Reply with ONE JSON object."
            )
            steps.append(
                AgentStep(n=n, thought="(unparseable)", action="error", observation=raw[:200])
            )
            continue

        thought = str(msg.get("thought", ""))
        action = msg.get("action")

        if action == "finish":
            metrics = msg.get("metrics", {})
            summary = msg.get("summary_markdown", "")
            steps.append(AgentStep(n=n, thought=thought, action="finish"))
            return DiagnosticReport(
                report_name=report_path.name,
                verdict=str(metrics.get("verdict", "unknown")),
                metrics=metrics,
                summary_markdown=summary,
                steps=steps,
            )

        if action == "call_tool":
            tool = msg.get("tool")
            args = msg.get("args", {}) or {}
            try:
                result = run_tool(tool, args)
                observation = json.dumps(result)
            except Exception as e:  # tool errors are observations the agent can recover from
                observation = f"ERROR: {e}"
            steps.append(
                AgentStep(
                    n=n,
                    thought=thought,
                    action="call_tool",
                    tool=tool,
                    args=args,
                    observation=observation,
                )
            )
            history.append(json.dumps({"action": "call_tool", "tool": tool, "args": args}))
            history.append(f"OBSERVATION: {observation}")
            continue

        # Unknown action -> nudge.
        history.append("OBSERVATION: unknown action. Use 'call_tool' or 'finish'.")
        steps.append(AgentStep(n=n, thought=thought, action="unknown", observation=str(action)))

    # Ran out of steps without finishing — return what we have, honestly labelled.
    return DiagnosticReport(
        report_name=report_path.name,
        verdict="inconclusive (step budget exhausted)",
        metrics={},
        summary_markdown="The agent did not converge within the step budget. See the step log.",
        steps=steps,
    )
