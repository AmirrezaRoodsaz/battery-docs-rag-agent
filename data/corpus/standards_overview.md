---
title: Plain-language Overview of Battery-Relevant Standards
author: Amirreza Roodsaz
type: self-authored summary (own words; no standard text reproduced)
license: MIT (this repository)
---

# Battery-relevant standards — plain-language overview

> **Important:** this document contains **my own plain-language summaries** of the *scope
> and purpose* of each standard, written from public abstracts and general engineering
> knowledge. It does **not** reproduce any copyrighted standard text. For authoritative
> requirements, consult the official standard. Links are in `data/README.md`.

These summaries exist so the RAG system can answer "what is standard X about / which one
applies to Y" with a citable, non-infringing source — and correctly say "not found" when
asked for specific clause text it does not contain.

## ISO 26262 — Functional safety of road vehicles

ISO 26262 is the automotive adaptation of the general functional-safety standard IEC
61508. It addresses hazards caused by **malfunctioning behaviour of electrical and
electronic (E/E) systems** in production road vehicles. Its core ideas:

- A **safety lifecycle** spanning concept, development, production, and operation.
- **ASIL (Automotive Safety Integrity Level)** — a risk classification from **ASIL A
  (lowest) to ASIL D (highest)**, plus QM (quality-managed, no safety requirement),
  derived from a hazard analysis and risk assessment over three factors: severity,
  exposure, and controllability.
- Requirements flow down from a vehicle-level **safety goal** to hardware and software.

For a battery system, ISO 26262 is what governs the **functional safety of the BMS** —
e.g. ensuring the system safely detects and reacts to overvoltage, overcurrent, or
overtemperature. It is about *safe behaviour of the electronics*, not about the cell's
intrinsic chemistry or transport safety.

## UN 38.3 — Transport of lithium batteries

UN 38.3 (UN Manual of Tests and Criteria, Part III, sub-section 38.3) defines the
**tests a lithium battery must pass to be shipped** safely. It is a transport-safety
gate, not a performance standard. It comprises a series of abuse and environmental tests,
including:

- **T1 Altitude simulation** (low pressure), **T2 Thermal test** (temperature cycling),
  **T3 Vibration**, **T4 Shock**, **T5 External short circuit**, **T6 Impact / crush**,
  **T7 Overcharge**, and **T8 Forced discharge**.

Passing UN 38.3 is mandatory for air, sea, and road transport of lithium cells and
batteries. It answers "is this battery safe to *ship*", which is distinct from "is the
BMS functionally safe" (ISO 26262) or "how long does the cell *last*" (IEC 62660).

## IEC 62660 — Secondary lithium-ion cells for EV propulsion

IEC 62660 is the series concerned with **performance and reliability testing of
lithium-ion cells for the propulsion of electric road vehicles**. Notably:

- **IEC 62660-1** covers **performance testing** — capacity, power, energy, and **cycle-
  life** and **calendar-life** test procedures.
- **IEC 62660-2** covers **reliability and abuse testing**.

This is the standard most relevant to **cycle-life and SOH characterization** of traction
cells: it defines how to measure capacity and how to run ageing tests so that results are
comparable. When a question is about *how cell ageing is tested*, IEC 62660 is the
relevant reference.

## How to tell them apart (quick mapping)

| Question | Relevant standard |
|---|---|
| Is the BMS electronics functionally safe? | ISO 26262 |
| Can this battery be shipped by air/sea/road? | UN 38.3 |
| How is cell cycle-life / capacity tested? | IEC 62660 |

These three answer different questions and are routinely confused. A grounded assistant
should map the *intent* of a question to the right standard, cite this overview, and — if
asked for the exact normative text or a specific clause number — state that the full
standard text is not in the corpus.
