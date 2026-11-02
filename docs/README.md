# AI Project Kit — "Send Less, Sense Smart" (ASR Simulator)

This kit lets you rebuild the project from the paper
**"Send Less, Sense Smart: Adaptive Sample-and-Report for Longer-Lived IoT Sensor Nodes"**
using any AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, Gemini, Lovable, Bolt, Replit…).

## What the project is
A **simulator** (not hardware) that compares five ways a battery-powered IoT sensor can report data,
and computes battery energy, event-detection quality, error, and false alarms.
Optional stretch: an **interactive web dashboard** to demo it live.

## Files (read / paste in this order)
| # | File | Purpose |
|---|------|---------|
| 1 | `PROMPT.md` | The master prompt + phase prompts to paste into the AI tool |
| 2 | `PRD.md` | Product Requirements: what to build and why |
| 3 | `TRD.md` | Technical Requirements: formulas, parameters, modules, data |
| 4 | `APP_FLOW.md` | User flow + program flow (step by step) |
| 5 | `UI_UX.md` | CLI output design + dashboard wireframes, colours, fonts |
| 6 | `TASKS.md` | Small build steps (milestones) with "done when" checks |
| 7 | `TESTING.md` | Test cases + expected numbers to verify correctness |
| 8 | `RULES.md` | Rules for the AI (rename to `CLAUDE.md` / `.cursorrules` / `AGENTS.md`) |

## How to use (vibe-coding workflow)
1. Create an empty project folder. Put all these `.md` files in a `docs/` folder (put `RULES.md` in the root).
2. Open your AI tool in that folder.
3. Paste the **Master Prompt** from `PROMPT.md`. Then run the **phases** one at a time.
4. After each phase, run the checks in `TESTING.md`. Commit to git. Only then go to the next phase.
5. If the AI drifts, say: *"Re-read docs/TRD.md section X and fix to match."*

## Golden rules
- Build **small steps**, test each, commit often.
- The numbers in `TESTING.md` are your truth. If they don't match, the code is wrong (not the numbers).
- Never let the AI invent results. Results must come from running the code.
