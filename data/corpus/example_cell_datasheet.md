---
title: Example Cell Datasheet — "Aurora AR-2100" 21700 Li-ion Cell (FICTIONAL)
author: Amirreza Roodsaz
type: synthesized datasheet (fictional cell, invented numbers)
license: MIT (this repository)
---

# Aurora AR-2100 — 21700 Cylindrical Li-ion Cell (FICTIONAL EXAMPLE)

> **This is a fictional cell with invented but physically plausible numbers**, written for
> this repository so that the RAG system has a realistic datasheet to retrieve from without
> reproducing any manufacturer's copyrighted document. No real product is described.

## Overview

The **Aurora AR-2100** is a high-energy 21700-format cylindrical lithium-ion cell with an
**NMC811** cathode and a graphite–silicon (Si-blended) anode, intended for electric-vehicle
traction packs.

## Electrical specifications (at 25 °C unless stated)

| Parameter | Symbol | Value | Conditions |
|---|---|---|---|
| Nominal capacity | C_nom | **5.0 Ah** | 0.2C discharge, 25 °C |
| Minimum capacity | C_min | 4.85 Ah | 0.2C discharge, 25 °C |
| Nominal voltage | V_nom | **3.63 V** | average over 0.2C discharge |
| Charge voltage (max) | V_max | **4.20 V** | CC-CV |
| Discharge cut-off voltage | V_min | **2.50 V** | |
| Nominal energy | E_nom | **18.15 Wh** | C_nom x V_nom |
| Internal resistance (AC, 1 kHz) | R_AC | **15 mOhm** | 50 % SOC, 25 °C, fresh cell |
| Internal resistance (DC, 10 s pulse) | R_DC | **22 mOhm** | 50 % SOC, 25 °C, fresh cell |

## Charge specification

- **Standard charge:** constant current at **0.3C (1.5 A)** to 4.20 V, then constant
  voltage until current tapers to 0.05C (250 mA).
- **Fast charge:** up to **1.5C (7.5 A)** between 15 °C and 45 °C.
- **Standard charge time:** approximately 4 hours; fast-charge ~45 minutes to 80 % SOC.

## Discharge specification

- **Continuous discharge current (max):** **2C (10 A)**.
- **Peak discharge current (≤10 s):** 3C (15 A).
- **Discharge cut-off:** 2.50 V.

## Temperature limits

| Mode | Minimum | Maximum |
|---|---|---|
| Charge | **0 °C** | 45 °C |
| Discharge | **-20 °C** | 60 °C |
| Storage (recommended) | -20 °C | 35 °C, at ~30–50 % SOC |

Charging below 0 °C is **not permitted** to avoid lithium plating.

## Cycle life

- **≥ 1000 cycles** to 80 % SOH at **1C/1C, 100 % DOD, 25 °C**.
- **≥ 2000 cycles** to 80 % SOH at **0.5C/0.5C, 80 % DOD, 25 °C**.
- End-of-life is defined here as capacity falling to **80 % of nominal (4.0 Ah)**.

## Mechanical & safety

- Format: **21700** (21 mm diameter, 70 mm length), mass ~70 g.
- Built-in **CID** (current-interrupt device) and **PTC** for overcurrent/overpressure
  protection.
- Cell is declared to meet **UN 38.3** transport-test requirements.

## Notes for the reader

Every value in this datasheet is invented for demonstration and describes no real product.
The pricing, exact cell construction, and supplier information that a real datasheet would
carry are deliberately omitted — questions about them should return "not found", which
makes this document useful for exercising the system's refusal behaviour as well as its
retrieval of the specifications above.
