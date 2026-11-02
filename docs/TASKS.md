# TASKS — Build plan (one milestone at a time)
Mark each as done only when its **Done when** check passes.

| # | Milestone | Done when |
|---|-----------|-----------|
| 1 | Project setup: folder, git init, constants block, `RULES.md` in root | `python iot_asr_demo.py` runs without error |
| 2 | Payload + energy: CBOR encoder, SenML JSON/CBOR, `lora_airtime`, `message_energy` | RFC 8949 vectors pass; CBOR payload = 25 B; E_msg ≈ 13.4 mJ |
| 3 | `make_world(seed)` per TRD §4 | Same seed → same world; 40 events; a few hundred glitches/week; temp range ≈ 18–36 °C |
| 4 | Schemes: `run_fixed`, `run_sod`, `run_asr` | F60 → 10,080 msgs/week; F600 → 1,008; SoD60 ≈ 110/day; ASR ≈ 118/day |
| 5 | `evaluate()` metrics | Detection/delay/RMSE/FA computed; F10 detects ≈ 100% |
| 6 | `experiment` + `tune` + `results.json` | Table matches TESTING.md within ±3% |
| 7 | `demo` mode + nice CLI output | Runs in < 10 s and tells the event story |
| 8 | (Optional) Dashboard `index.html` | Sliders update chart live, works offline |
| 9 | (Optional) Figures script | 3 PNGs in `figures/` match UI_UX §3 |
| 10 | Unit tests + README | `python -m unittest` passes; README explains run steps |

## Tips for vibe coding each milestone
- Ask the AI to **explain its plan first**, then code, then run tests.
- Keep one file until it works; split into modules only after Milestone 6.
- Commit after every green milestone: `git commit -m "M4: schemes done"`.
