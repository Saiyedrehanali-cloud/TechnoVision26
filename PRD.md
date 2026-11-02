# PRD — Product Requirements Document
**Project:** ASR Simulator ("Send Less, Sense Smart")  
**Owner:** Saiyed Rehan Ali, Kratika Mishra · **Context:** Technovision 2026–27 paper & presentation

## 1. Problem
Battery-powered IoT sensors usually send a reading at a fixed period (e.g. every minute). Most messages
repeat the previous one, and the radio uses most of the battery. A longer period saves energy but misses
short events (e.g. a cold-room door left open).

## 2. Goal
Prove, with a reproducible simulation, that a node can **send less and still catch events**, using the
ASR scheme, and show the results honestly (including where ASR is *not* better).

## 3. Users
| User | Need |
|------|------|
| Student/author (primary) | Reproduce paper numbers; live demo in front of teachers |
| Teacher/judge | Understand quickly; trust the numbers; see honest limits |
| Other students | Run it easily, change parameters, learn |

## 4. Scope
**In scope (MVP)**
- Synthetic data generator (daily profile, drift, noise, glitches, events).
- 5 schemes: F10, F60, F600, SoD60, ASR (+ ablations SoD10, ASR no-confirm).
- Energy model using LoRaWAN airtime and SenML/CBOR payload.
- Metrics: msgs/day, J/day, lifetime (model), detection %, mean delay, RMSE, false alarms/week.
- CLI modes: `demo`, `experiment`, `tune`. Output `results.json`.
- Standard library only. Runs on Python 3.9+ with no installs.

**Stretch**
- Single-file interactive web dashboard (sliders + live chart).
- Figure generation script (matplotlib, optional).

**Out of scope**
- Real hardware, real radio, packet loss, multi-node networks, security/encryption.

## 5. Functional requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | Generate one week of 1-s temperature data from a seed | Must |
| F2 | Inject 40 events/week with ramps and glitches | Must |
| F3 | Implement fixed-period, send-on-delta, and ASR schemes | Must |
| F4 | Compute energy/day with the TRD formulas | Must |
| F5 | Compute detection %, delay, RMSE, false alarms | Must |
| F6 | `experiment` mode: seeds 100–129, mean ± SD table, saves JSON | Must |
| F7 | `tune` mode: seeds 1–5 parameter sweep | Should |
| F8 | `demo` mode: short readable story of one event | Must |
| F9 | Unit tests incl. CBOR RFC 8949 test vectors | Must |
| F10 | Web dashboard with sliders and live chart | Could |
| F11 | Figures (energy breakdown, trade-off, block diagram) | Could |

## 6. Non-functional requirements
- **Reproducible:** same seed → same output.
- **Fast:** full `experiment` < 3 minutes on a laptop; `demo` < 10 s.
- **Readable:** commented, simple functions (student-level).
- **Honest:** no hard-coded results; assumptions listed at top of the code.
- **Portable:** no external dependencies for the core.

## 7. Success metrics (acceptance)
Running `experiment` reproduces (within ±3%): ASR ≈ 4.9 J/day, ≈ 97% events detected, ≈ 33 s delay,
0 false alarms/week; F60 ≈ 22.6 J/day; F600 ≈ 54% detected. (Full table in `TESTING.md`.)

## 8. Risks
| Risk | Mitigation |
|------|-----------|
| AI invents numbers | Rule: results only from running code; compare to TESTING.md |
| Random sequence differs → small number drift | Accept ±3%; fix seed & RNG order |
| Over-claiming | Paper/demo must state ASR ≈ SoD in energy; wins are RMSE & false alarms |

## 9. Deliverables
`iot_asr_demo.py`, `results.json`, tests, (optional) `dashboard/index.html`, `figures/*.png`, README.
