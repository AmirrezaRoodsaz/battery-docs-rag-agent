---
title: Battery Cell Test Report — AR-2100 sample #A17 (SYNTHESIZED)
author: Amirreza Roodsaz
type: synthesized test report (fictional data for the agentic demo)
license: MIT (this repository)
---

# Cell Test Report — Aurora AR-2100, sample #A17

> Synthesized report with invented data, for the agentic test-report demo. Not a real test.

## Test setup

- Cell under test: Aurora AR-2100 (21700, NMC811), nominal capacity 5.0 Ah, nominal voltage 3.63 V.
- Rated (beginning-of-life) capacity: 5.0 Ah.
- Test equipment: bench cycler, 4-wire sense.
- Ambient temperature setpoint: 25 °C.
- Charge: CC-CV, 0.3C to 4.20 V, taper to 0.05C. Discharge: 1C to 2.50 V.

## Measurements

- Measured discharge capacity (0.2C reference): 4.78 Ah
- Measured nominal voltage: 3.62 V
- DC internal resistance (10 s pulse, 50 % SOC, 25 °C): 24 mOhm
- Beginning-of-life DCIR (from datasheet/commissioning): 22 mOhm
- Coulombic efficiency: 99.4 %
- Cycle number at test: 180
- Minimum cell temperature during test: 24.6 °C
- Maximum cell temperature during test: 31.2 °C

## Observations

- Discharge voltage curve nominal; no abnormal plateaus.
- No overvoltage, undervoltage, or overtemperature events logged.
- Capacity slightly below nominal, consistent with ~180 cycles of normal use.
