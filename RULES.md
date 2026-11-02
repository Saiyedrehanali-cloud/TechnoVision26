# RULES.md — Instructions for the AI coding assistant
(Rename this file to `CLAUDE.md`, `.cursorrules`, or `AGENTS.md` depending on your tool.)

## Project
ASR Simulator — Python standard-library simulator for battery-powered IoT reporting schemes.
Source of truth: `docs/PRD.md`, `docs/TRD.md`, `docs/APP_FLOW.md`, `docs/UI_UX.md`, `docs/TASKS.md`, `docs/TESTING.md`.

## Must do
- Follow `docs/TASKS.md` milestone by milestone. Finish and test one before starting the next.
- Use **only the Python standard library** for the core. Ask before adding any dependency.
- Match the constants, formulas and algorithms in `docs/TRD.md` exactly.
- Keep RNG call order as in TRD §4 so results are reproducible.
- Put all assumptions (energy values etc.) in one constants block with comments.
- Write simple, commented code a college student can explain.
- After each change: run tests, show output, then summarise what changed.

## Must NOT do
- Do not invent, estimate, or hard-code result numbers. Results come only from running the code.
- Do not tune parameters on test seeds (100–129). Tuning uses seeds 1–5 only.
- Do not silently change the spec. If the spec seems wrong, stop and ask.
- Do not add features outside PRD scope.
- Do not use frameworks/CDNs in the dashboard.

## Style
- PEP 8; docstring on each public function; functions short and single-purpose.
- Clear names (`run_asr`, `evaluate`, `message_energy`).
- Print tables with aligned columns; mark the ASR row.

## Communication
- Before coding: 3–5 line plan. After coding: what was done, how to run, what to check next.
- If unsure, ask a question instead of guessing.
