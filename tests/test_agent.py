"""Tests for the agent's deterministic pieces — tools and the JSON-step parser.

The LLM planning loop needs a key and isn't unit-tested here, but everything that produces
the actual numbers (the tools) and the protocol glue (JSON extraction) is deterministic and
fully tested without any API call. That's the point of keeping arithmetic in the tools.
"""


import pytest

from src.agent.agent_loop import _extract_json
from src.agent.tools import (
    RESISTANCE_DOUBLED_PCT,
    SOH_EOL_PCT,
    compute_soh,
    evaluate_health,
    resistance_growth_pct,
    run_tool,
    tools_description,
)


def test_compute_soh():
    assert compute_soh(4.0, 5.0)["soh_pct"] == 80.0
    assert compute_soh(3.85, 5.0)["soh_pct"] == 77.0


def test_compute_soh_rejects_bad_rated():
    with pytest.raises(ValueError):
        compute_soh(4.0, 0.0)


def test_resistance_growth():
    assert resistance_growth_pct(44.0, 22.0)["resistance_growth_pct"] == 100.0
    assert resistance_growth_pct(24.0, 22.0)["resistance_growth_pct"] == pytest.approx(9.1, abs=0.1)


def test_evaluate_health_healthy():
    r = evaluate_health(soh_pct=95.6, resistance_growth_pct=9.1, max_temp_c=31.2)
    assert r["verdict"] == "HEALTHY"
    assert not r["capacity_eol"] and not r["power_eol"] and not r["thermal_event"]
    assert r["flags"] == []


def test_evaluate_health_end_of_life_and_thermal():
    r = evaluate_health(soh_pct=77.0, resistance_growth_pct=86.4, max_temp_c=63.4)
    assert r["capacity_eol"] is True  # 77 < 80
    assert r["thermal_event"] is True  # 63.4 > 60
    assert "END-OF-LIFE" in r["verdict"]
    assert any("Capacity below EOL" in f for f in r["flags"])
    assert any("Thermal limit" in f for f in r["flags"])


def test_evaluate_health_power_eol_on_doubled_resistance():
    r = evaluate_health(soh_pct=90.0, resistance_growth_pct=RESISTANCE_DOUBLED_PCT, max_temp_c=30.0)
    assert r["power_eol"] is True
    assert "END-OF-LIFE" in r["verdict"]


def test_thresholds_are_documented_values():
    assert SOH_EOL_PCT == 80.0
    assert RESISTANCE_DOUBLED_PCT == 100.0


def test_run_tool_dispatch_and_unknown():
    assert (
        run_tool("compute_soh", {"measured_capacity_ah": 5.0, "rated_capacity_ah": 5.0})["soh_pct"]
        == 100.0
    )
    with pytest.raises(KeyError):
        run_tool("nope", {})


def test_tools_description_lists_all_tools():
    desc = tools_description()
    for name in ("compute_soh", "resistance_growth_pct", "evaluate_health"):
        assert name in desc


def test_extract_json_plain():
    assert _extract_json('{"action": "finish"}') == {"action": "finish"}


def test_extract_json_with_code_fence_and_prose():
    raw = 'Sure!\n```json\n{"action": "call_tool", "tool": "compute_soh", "args": {"measured_capacity_ah": 4.0, "rated_capacity_ah": 5.0}}\n```'
    msg = _extract_json(raw)
    assert msg["tool"] == "compute_soh"
    assert msg["args"]["measured_capacity_ah"] == 4.0


def test_extract_json_nested_braces():
    raw = '{"action":"finish","metrics":{"soh_pct":77.0,"flags":["a","b"]}}'
    msg = _extract_json(raw)
    assert msg["metrics"]["soh_pct"] == 77.0
    assert msg["metrics"]["flags"] == ["a", "b"]


def test_extract_json_raises_when_absent():
    with pytest.raises(ValueError):
        _extract_json("no json here")
