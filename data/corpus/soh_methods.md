---
title: State of Health (SOH) Determination Methods for Li-ion Traction Batteries
author: Amirreza Roodsaz
type: self-authored notes
license: MIT (this repository)
---

# State of Health (SOH) determination methods

State of Health (SOH) quantifies how much a battery has aged relative to its
beginning-of-life (BOL) condition. It is a *relative* figure of merit, normally expressed
as a percentage, where 100 % means a fresh cell and a lower value means a degraded one.
There is no single universal definition; the right definition depends on what the
application cares about — usable energy, deliverable power, or internal condition.

## Capacity-based SOH

The most common definition compares present usable capacity to rated (or
beginning-of-life) capacity:

    SOH_capacity = Q_present / Q_rated x 100 %

where `Q_present` is the capacity measured today under a defined test (a full
constant-current discharge between defined voltage limits at a defined temperature and
C-rate) and `Q_rated` is the nameplate or BOL capacity. For automotive traction
batteries, the conventional **end-of-life (EOL) threshold is 80 % SOH** — below this the
range loss is usually considered unacceptable for the original application, and the pack
may be a candidate for second-life use.

Capacity-based SOH is intuitive and maps directly to driving range, but measuring it
properly requires a slow, controlled full cycle, which is impractical to do often in the
field.

## Energy-based SOH

Energy-based SOH compares deliverable energy (the integral of power over a discharge)
rather than charge:

    SOH_energy = E_present / E_rated x 100 %

Because energy folds in the voltage drop caused by rising internal resistance, energy
fade is generally *faster* than capacity fade for the same cell. Energy-based SOH is the
more honest figure when the application is range- or work-limited, since it captures both
lithium loss and resistance growth at once.

## Resistance- / power-based SOH

Power capability is limited by internal resistance. As a cell ages, its internal
resistance (often reported as DC internal resistance, DCIR) rises, reducing the power it
can source or sink. A resistance-based SOH is sometimes defined as:

    SOH_resistance = R_EOL_criterion - R_present  /  R_EOL_criterion - R_BOL  x 100 %

or more simply tracked as the percentage increase of DCIR over its BOL value. A common
power-fade EOL criterion is a **doubling of internal resistance (a 100 % increase)** from
BOL. Resistance-based SOH matters most for power-limited duty cycles (e.g. hybrid or
high-rate applications) and for thermal behaviour, since higher resistance means more
ohmic heating.

## Incremental Capacity Analysis (ICA) and Differential Voltage Analysis (DVA)

ICA and DVA are *non-destructive* techniques that read degradation mechanisms from the
shape of a slow charge/discharge curve, not just its endpoint capacity.

- **ICA** plots dQ/dV against voltage. Plateaus in the voltage curve (two-phase
  transitions in the electrode materials) become **peaks** in the dQ/dV curve. The
  position, height, and area of these peaks shift as the cell ages, and the shifts can be
  attributed to specific mechanisms — loss of lithium inventory (LLI) versus loss of
  active material (LAM).
- **DVA** plots dV/dQ against capacity. Features in dV/dQ relate to the electrodes' own
  open-circuit characteristics, and the spacing between features tracks how each
  electrode's usable capacity is shrinking.

Both require a **slow, low-C-rate** measurement (typically C/20 to C/3) so that the curve
approximates near-equilibrium behaviour; at high rates the peaks smear out and the
diagnostic value is lost. ICA/DVA are powerful because they separate *why* a cell is
ageing, not just *how much* — which is exactly what is needed to predict the remaining
trajectory rather than just report the present number.

## Degradation mechanisms in one paragraph

The three families that the methods above try to detect: **loss of lithium inventory
(LLI)** — cyclable lithium consumed by side reactions such as SEI growth; **loss of
active material (LAM)** — electrode material that becomes electrically or
electrochemically disconnected; and **conductivity / resistance increase** — growth of
interfacial and contact resistances. LLI and LAM mostly reduce capacity; resistance
increase mostly reduces power. A good SOH scheme reports the dimension the application
actually cares about, and ideally attributes the fade to a mechanism.

## Practical takeaways

- Always state the **test conditions** with any SOH number — temperature, C-rate, and
  voltage window. A capacity measured at 0 °C and 1C is not comparable to one at 25 °C and
  C/3.
- **80 % SOH** is the conventional automotive EOL for capacity; **2x internal resistance**
  is a common power-fade EOL.
- Capacity-based SOH answers "how much range is left"; resistance-based SOH answers "how
  much power is left"; ICA/DVA answer "why".
- Field SOH estimation trades accuracy for practicality — onboard estimators infer SOH
  from partial cycles and models because a full reference cycle is rarely available.
