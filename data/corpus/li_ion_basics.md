---
title: Lithium-ion Cell Fundamentals for Battery Engineers
author: Amirreza Roodsaz
type: self-authored notes
license: MIT (this repository)
---

# Lithium-ion cell fundamentals

A short, self-authored reference on the terms and quantities that show up in datasheets
and test reports, written so a retrieval system has clean, citable definitions to ground
on.

## How a Li-ion cell works

A lithium-ion cell shuttles Li+ ions between two intercalation electrodes through an
electrolyte and a separator. On **discharge**, lithium leaves the negative electrode
(anode, usually graphite), moves through the electrolyte, and inserts into the positive
electrode (cathode); electrons travel the external circuit, doing work. On **charge**, an
external source drives the process in reverse. Because the lithium is *intercalated*
(hosted) rather than plated, the process is reversible over many cycles — that
reversibility, and how it slowly degrades, is what battery engineering is about.

## Common cell chemistries

- **LFP (LiFePO4)**: nominal voltage ~3.2 V, very flat discharge curve, excellent cycle
  life and thermal/safety stability, lower energy density. Common in traction and storage.
- **NMC (LiNiMnCoO2)**: nominal voltage ~3.6–3.7 V, higher energy density, widely used in
  EVs; safety and cycle life depend strongly on the Ni:Mn:Co ratio.
- **NCA (LiNiCoAlO2)**: similar high-energy niche to high-nickel NMC.

The flat voltage curve of LFP makes voltage-based state estimation harder (small voltage
change per unit charge), which is one reason capacity- and model-based SOH methods matter
for LFP packs.

## Key quantities (the datasheet vocabulary)

- **Nominal capacity (Ah)**: the rated charge a cell delivers under specified conditions.
  A "1.1 Ah" cell delivers ~1.1 amp-hours from full to empty at the rated rate.
- **Nominal voltage (V)**: a representative average voltage over a discharge; used with
  capacity to state energy.
- **Energy (Wh)** = capacity (Ah) x average voltage (V). A 1.1 Ah cell at 3.3 V holds
  ~3.6 Wh.
- **C-rate**: current normalized to capacity. **1C** discharges the rated capacity in one
  hour; **2C** in half an hour; **C/2 (0.5C)** in two hours. For a 1.1 Ah cell, 1C = 1.1 A.
- **State of Charge (SOC)**: how full the cell is *right now*, 0–100 %. Distinct from SOH:
  SOC is "how full", SOH is "how aged".
- **Depth of Discharge (DOD)**: the fraction of capacity removed in a cycle; DOD = 100 % - SOC
  at the end of discharge. Cycling at shallow DOD generally extends cycle life.
- **Cut-off voltages**: the upper charge limit and lower discharge limit (e.g. 3.6 V and
  2.0 V for many LFP cells). Operating outside them accelerates degradation or is unsafe.
- **Internal resistance (DCIR / ACIR)**: opposition to current; DC internal resistance is
  measured from the voltage step under a current pulse, AC internal resistance typically at
  1 kHz. Rises with age and falls with temperature.
- **Cycle life**: number of full charge/discharge cycles until capacity reaches the EOL
  threshold (commonly 80 % of nominal). Strongly dependent on DOD, C-rate, and temperature.
- **Calendar life**: ageing that occurs over time even without cycling, driven mainly by
  temperature and storage SOC.

## Temperature

Temperature is the dominant external ageing factor. High temperature accelerates side
reactions (faster SEI growth, more LLI); low temperature raises internal resistance and,
during charging, risks **lithium plating** — metallic lithium deposited on the anode
instead of intercalating, which is both a capacity-loss and a safety hazard. Most cells
specify a narrower temperature window for charging than for discharging for this reason.

## Why these definitions matter for RAG

A retrieval system answering battery questions needs unambiguous, self-consistent
definitions to cite. Mixing up SOC and SOH, or quoting a capacity without its C-rate and
temperature, is exactly the kind of subtle error that makes a "chat with PDF" tool
untrustworthy. Grounding answers in definitions like these — and citing them — is what
separates a usable engineering assistant from a plausible-sounding one.
