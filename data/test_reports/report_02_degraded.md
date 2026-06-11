---
title: Battery Cell Test Report — AR-2100 sample #B04 (SYNTHESIZED)
author: Amirreza Roodsaz
type: synthesized test report (fictional data for the agentic demo)
license: MIT (this repository)
---

# Cell Test Report — Aurora AR-2100, sample #B04

> Synthesized report with invented data, for the agentic test-report demo. Not a real test.
> This sample is deliberately degraded so the agent has anomalies to flag.

## Test setup

- Cell under test: Aurora AR-2100 (21700, NMC811), nominal capacity 5.0 Ah, nominal voltage 3.63 V.
- Rated (beginning-of-life) capacity: 5.0 Ah.
- Test equipment: bench cycler, 4-wire sense.
- Ambient temperature setpoint: 25 °C.
- Charge: CC-CV, 0.3C to 4.20 V, taper to 0.05C. Discharge: 1C to 2.50 V.

## Measurements

- Measured discharge capacity (0.2C reference): 3.85 Ah
- Measured nominal voltage: 3.58 V
- DC internal resistance (10 s pulse, 50 % SOC, 25 °C): 41 mOhm
- Beginning-of-life DCIR (from datasheet/commissioning): 22 mOhm
- Coulombic efficiency: 98.1 %
- Cycle number at test: 1240
- Minimum cell temperature during test: 23.9 °C
- Maximum cell temperature during test: 63.4 °C

## Observations

- One overtemperature excursion logged at cycle 1187 (peak 63.4 °C, above the 60 °C
  discharge limit).
- Discharge voltage curve shows an earlier knee than at beginning of life.
- Capacity well below nominal; resistance substantially elevated versus commissioning.
