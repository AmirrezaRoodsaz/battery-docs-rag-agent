"""Deterministic tools the test-report agent can call.

Design choice (and an interview talking point): the LLM **plans** and **reads** — it decides
which tool to call and pulls the raw numbers out of the report text — but the tools do all
the **arithmetic and the threshold logic**. That split is the whole point of giving an LLM
tools: models are unreliable at exact computation, so we never let the model *compute* SOH or
decide a pass/fail threshold; it only *extracts* values and *orchestrates*. Every tool here is
a pure function with no LLM inside, which is why they're all unit-tested without any API key.

EOL thresholds used (documented, defensible, from the corpus notes):
  - Capacity EOL: SOH < 80 %  (the conventional automotive end-of-life).
  - Power EOL:    internal resistance growth >= 100 % (a doubling from BOL).
  - Thermal flag: any temperature above the cell's 60 °C discharge limit.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

SOH_EOL_PCT = 80.0
RESISTANCE_DOUBLED_PCT = 100.0
DISCHARGE_TEMP_LIMIT_C = 60.0


def compute_soh(measured_capacity_ah: float, rated_capacity_ah: float) -> dict[str, Any]:
    """Capacity-based SOH = measured / rated x 100 %."""
    if rated_capacity_ah <= 0:
        raise ValueError("rated_capacity_ah must be positive")
    soh = 100.0 * measured_capacity_ah / rated_capacity_ah
    return {"soh_pct": round(soh, 1)}


def resistance_growth_pct(measured_mohm: float, bol_mohm: float) -> dict[str, Any]:
    """Percentage increase of internal resistance over its beginning-of-life value."""
    if bol_mohm <= 0:
        raise ValueError("bol_mohm must be positive")
    growth = 100.0 * (measured_mohm - bol_mohm) / bol_mohm
    return {"resistance_growth_pct": round(growth, 1)}


def evaluate_health(
    soh_pct: float, resistance_growth_pct: float, max_temp_c: float
) -> dict[str, Any]:
    """Apply documented thresholds and return structured flags + an overall verdict."""
    capacity_eol = soh_pct < SOH_EOL_PCT
    power_eol = resistance_growth_pct >= RESISTANCE_DOUBLED_PCT
    thermal_event = max_temp_c > DISCHARGE_TEMP_LIMIT_C

    flags: list[str] = []
    if capacity_eol:
        flags.append(f"Capacity below EOL: SOH {soh_pct:.1f}% < {SOH_EOL_PCT:.0f}%")
    if power_eol:
        flags.append(
            f"Power-fade EOL: resistance up {resistance_growth_pct:.0f}% "
            f"(>= {RESISTANCE_DOUBLED_PCT:.0f}% = doubled)"
        )
    if thermal_event:
        flags.append(
            f"Thermal limit exceeded: {max_temp_c:.1f} °C > {DISCHARGE_TEMP_LIMIT_C:.0f} °C "
            "discharge limit"
        )

    if capacity_eol or power_eol:
        verdict = "END-OF-LIFE for original automotive use"
    elif thermal_event or resistance_growth_pct >= 50:
        verdict = "DEGRADED — monitor / investigate"
    else:
        verdict = "HEALTHY"

    return {
        "capacity_eol": capacity_eol,
        "power_eol": power_eol,
        "thermal_event": thermal_event,
        "flags": flags,
        "verdict": verdict,
    }


# --- Tool registry ----------------------------------------------------------------------
# Each entry: the callable plus a one-line description and an arg list, used to build the
# planner prompt so the LLM knows exactly what it can call and with which arguments.


class Tool:
    def __init__(self, func: Callable[..., dict], description: str, args: dict[str, str]):
        self.func = func
        self.description = description
        self.args = args  # arg name -> type/description, for the planner prompt


TOOLS: dict[str, Tool] = {
    "compute_soh": Tool(
        compute_soh,
        "Compute capacity-based State of Health (%) from measured and rated capacity.",
        {"measured_capacity_ah": "float", "rated_capacity_ah": "float"},
    ),
    "resistance_growth_pct": Tool(
        resistance_growth_pct,
        "Compute internal-resistance growth (%) over the beginning-of-life value.",
        {"measured_mohm": "float", "bol_mohm": "float"},
    ),
    "evaluate_health": Tool(
        evaluate_health,
        "Apply EOL/thermal thresholds; return flags and an overall verdict.",
        {"soh_pct": "float", "resistance_growth_pct": "float", "max_temp_c": "float"},
    ),
}


def run_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name with keyword args. Raises on unknown tool / bad args."""
    if name not in TOOLS:
        raise KeyError(f"Unknown tool '{name}'. Available: {', '.join(TOOLS)}")
    return TOOLS[name].func(**args)


def tools_description() -> str:
    """Human/LLM-readable catalogue of tools for the planner prompt."""
    lines = []
    for name, tool in TOOLS.items():
        arglist = ", ".join(f"{a}: {t}" for a, t in tool.args.items())
        lines.append(f"- {name}({arglist}) — {tool.description}")
    return "\n".join(lines)
