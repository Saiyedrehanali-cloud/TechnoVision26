# PROMPT.md — Prompts to build the project with AI

## A. MASTER PROMPT (paste this first)

```
You are a senior Python engineer and IoT researcher. Help me build a project called
"ASR Simulator" (Adaptive Sample-and-Report) for a research paper on battery-powered IoT sensor nodes.

READ these files first and follow them strictly: docs/PRD.md, docs/TRD.md, docs/APP_FLOW.md,
docs/UI_UX.md, docs/TASKS.md, docs/TESTING.md, and RULES.md.

GOAL
Build a simulator, using ONLY the Python standard library, that generates one synthetic week of
temperature data (with noise, glitches and injected events) and compares 5 reporting schemes
(F10, F60, F600, SoD60, ASR) on: energy per day, event-detection rate, mean detection delay,
reconstruction RMSE, and false alarms per week. Energy comes from a LoRaWAN airtime model with a
SenML/CBOR payload. Provide CLI modes: demo, experiment, tune.

WORKING STYLE
1. Do NOT write everything at once. Follow docs/TASKS.md milestone by milestone.
2. Before coding each milestone, tell me in 3-5 lines what you will build.
3. After coding, run the tests from docs/TESTING.md and show me the output.
4. If anything in the docs is unclear, ASK me instead of guessing.
5. Never invent or hard-code result numbers. Results must come from running the code.
6. Keep code simple, commented, and readable by a college student.

START NOW with Milestone 1 only (project setup + CBOR encoder + airtime/energy functions).
Stop and wait for my "next" before Milestone 2.
```

## B. PHASE PROMPTS (paste one at a time, after the master prompt)

**Phase 1 — Core maths**
```
Do Milestone 1 and 2 from docs/TASKS.md: constants, CBOR encoder (with RFC 8949 test vectors),
SenML JSON/CBOR payload builders, LoRa airtime function, message_energy(). Run the unit tests and
show that one SenML/CBOR uplink = 25 bytes, ~82 ms airtime, ~13.4 mJ at SF7.
```

**Phase 2 — World generator**
```
Do Milestone 3: make_world(seed) exactly as in docs/TRD.md section 4 (daily profile, drift, noise,
glitches, 40 events with ramps). Add a quick text summary (min/max temperature, number of events,
number of glitches) so I can sanity-check it.
```

**Phase 3 — The five schemes**
```
Do Milestone 4: implement run_fixed, run_sod, run_asr exactly as in docs/TRD.md section 5, with
the ASR parameters in the table (imin=10, imax=80, delta=0.5, heartbeat=900, jump=2.0,
confirm_gap=2, confirm_tol=1.5, look=0.75). Include the confirm=False ablation flag.
```

**Phase 4 — Metrics + experiment**
```
Do Milestone 5 and 6: evaluate() with detection by alarm band (2.5 C from the normal profile),
RMSE on a 10 s grid, false alarms, energy, lifetime; then the `experiment` mode over seeds 100-129
and `tune` mode over seeds 1-5. Save results.json. Compare against docs/TESTING.md expected values.
```

**Phase 5 — Demo + CLI polish**
```
Do Milestone 7: the `demo` mode (5-minute story: one event, what each scheme reports), clean
tables in the terminal (docs/UI_UX.md section 1), and --help text.
```

**Phase 6 (optional) — Web dashboard**
```
Do Milestone 8: build a single-file dashboard (index.html, vanilla JS, no frameworks) following
docs/UI_UX.md section 2. Port the ASR/SoD/fixed logic to JavaScript, same parameters as TRD.
Sliders for delta, Imax, event size; live chart of true signal vs reports; stat cards for energy,
messages/day, events caught. Must work offline by double-clicking the file.
```

**Phase 7 — Figures + report numbers**
```
Do Milestone 9: with matplotlib (optional dependency) generate 3 figures from results.json:
(1) energy breakdown stacked bars, (2) trade-off: energy vs delay and energy vs RMSE for ASR and
SoD sweeps, (3) ASR block diagram. Use the colour palette in docs/UI_UX.md.
```

## C. SHORT PROMPT (for tools that cannot read files — paste everything in one go)

```
Build a Python (standard library only) simulator for a battery-powered IoT temperature sensor.
Simulate 7 days at 1-second resolution: normal profile 24 + 4*sin(2*pi*(t/86400 - 0.25)) C,
AR(1) drift (a=0.9999, sd=0.003), sensor noise sd 0.1 C, glitches (p=5e-4, +/-U(6,12) C),
and 40 events (+/-U(4,8) C, 20 s ramp up, hold 5-60 s or 240-1700 s, 60 s ramp down).
Compare schemes: F10/F60/F600 (read+send every 10/60/600 s), SoD60 (read every 60 s, send if
|x-last|>=0.5 or 900 s since last send), and ASR: (1) if |x-base|>=2.0 re-read after 2 s and send
only if still >=1.5 away, else discard as glitch; (2) send if |x-last|>=0.5 or 900 s passed;
(3) read interval starts 10 s, doubles up to 80 s when calm, resets to 10 s when |x-last|>=0.375
or after a send; base = EWMA(0.1).
Energy per day = reads*(0.3 mJ [+0.02 mJ logic for SoD/ASR]) + messages*E_msg + 86400*3.3 V*10 uA,
E_msg = 3.3 V*44 mA*airtime + 1.5 mJ, LoRa SF7/125 kHz airtime (Semtech formula) for
(25-byte SenML-CBOR + 13-byte LoRaWAN overhead). Metrics: msgs/day, J/day, % events detected
(a report >=2.5 C from the normal profile while the event |change|>=2 C is active), mean delay,
RMSE of last-value hold on a 10 s grid, false alarms/week (glitch messages). Run 30 weeks
(seeds 100-129) and print a table of mean values. Add CLI modes: demo, experiment, tune.
Expected: ASR ~4.9 J/day, ~97% detected, 0 false alarms; F60 ~22.6 J/day.
```

## D. DEBUGGING PROMPTS
- "The ASR energy is not ~4.9 J/day. Re-read TRD section 5.3 and list every difference between the spec and the code."
- "Add a unit test for this function and show me it failing before you fix it."
- "Explain this function line by line in simple words so I can present it."
