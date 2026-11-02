# TRD — Technical Requirements Document

## 1. Stack
- Language: Python 3.9+. **Standard library only** for the core (`math, random, json, struct, statistics, bisect, sys, platform`).
- Optional: `matplotlib` for figures only. Optional dashboard: plain HTML + vanilla JS (no frameworks, no build step).

## 2. Project structure
```
asr-simulator/
├─ RULES.md
├─ docs/               (these .md files)
├─ iot_asr_demo.py     (single-file core; or split into the modules below)
├─ tests/test_core.py
├─ results.json        (generated)
├─ figures/            (generated, optional)
└─ dashboard/index.html (optional)
```
Optional split: `payload.py` (CBOR/SenML/airtime/energy), `world.py`, `schemes.py`, `metrics.py`, `cli.py`.

## 3. Constants (put at top of code, with comments marking them as ASSUMPTIONS)
| Name | Value | Meaning |
|------|-------|---------|
| DAY, DAYS, N | 86400, 7, 604800 | one week, 1 s resolution |
| V_SUPPLY | 3.3 V | supply |
| I_TX | 0.044 A | radio at about +14 dBm (assumed) |
| E_RX_WINDOWS | 1.5e-3 J | two Class-A receive windows |
| E_SAMPLE | 0.30e-3 J | per sensor read |
| E_LOGIC | 0.02e-3 J | extra per read for SoD and ASR only |
| I_SLEEP | 10e-6 A | whole node deep sleep |
| BATTERY_J | 2.0*3600*3.0 = 21,600 J | 2000 mAh at 3 V |
| LORAWAN_OVERHEAD | 13 bytes | MHDR+FHDR+FPort+MIC |
| ALARM_BAND | 2.5 °C | alarm if report is this far from the normal profile |

## 4. Data generation — `make_world(seed)`
Use `random.Random(seed)`. Keep this exact order of RNG use (so results are reproducible):
1. `normal[t] = 24 + 4*sin(2π(t/86400 − 0.25))`.
2. For t in 0..N−1: `drift = drift*0.9999 + gauss(0, 0.003)`; `truth[t] = normal[t] + drift`.
3. Events: pick 40 start times `randint(3600, N−3600)`, accept only if > 2000 s from all previous; sort.
   For each: `m = uniform(4,8) * choice([−1,+1])`; `hold = randint(5,60)` with prob 0.5 else `randint(240,1700)`;
   ramp up 20 s, hold, ramp down 60 s (linear factor f in [0,1]); `truth[s+k] += m*f`.
   Event **window** = times where `|m*f| ≥ 2.0` → store `(window_start, window_end)`.
4. `noise[t] = gauss(0, 0.10)` for all t.
5. `glitch`: dict `t → choice([−1,1])*uniform(6,12)` for each t with `random() < 5e-4`.
`read(t) = truth[t] + noise[t] + glitch.get(t,0)` and a flag if it was a glitch.

## 5. Schemes
### 5.1 Fixed period `run_fixed(period)` — F10, F60, F600
Read and send at t = 0, period, 2·period…; reads = messages.

### 5.2 Send-on-delta `run_sod(period=60, delta=0.5, heartbeat=900)`
Read every `period`; send if first, or `|x − last_sent| ≥ delta`, or `t − last_t ≥ heartbeat`.

### 5.3 ASR `run_asr(...)` — parameters
| Param | Value |
|-------|-------|
| imin / imax | 10 s / 80 s |
| delta | 0.5 °C |
| heartbeat | 900 s |
| jump | 2.0 °C (glitch/event trigger vs slow average `base`) |
| confirm_gap / confirm_tol | 2 s / 1.5 °C |
| look | 0.75 (restart timer if `|x−last| ≥ look*delta`) |
| EWMA weight | 0.1 |

Algorithm (one wake-up, loop until end of week):
```
t += interval; x = read(t); reads += 1
if |x − base| ≥ jump:
    x2 = read(t+2); reads += 1; t = t+2
    if |x2 − base| < confirm_tol: continue        # glitch → ignore (interval unchanged)
    send(x2); last = x2; base = x2; interval = imin; continue
base += 0.1*(x − base)
if |x − last| ≥ delta or (t − last_t) ≥ heartbeat: send(x); interval = imin
elif |x − last| ≥ look*delta: interval = imin
else: interval = min(2*interval, imax)
```
Start: read at t=0, send it, `last=base=x`, `interval=imin`.
Ablation flag `confirm=False`: on jump, send `x` immediately (no re-read).

## 6. Payload and energy
- SenML record: `[{"bt": t, "n":"temp", "u":"Cel", "v": round(v,2)}]`.
- JSON size ≈ 50 B; CBOR (integer labels bt=−3, n=0, u=1, v=2, value as float32) = **25 B**.
- Minimal CBOR encoder must pass RFC 8949 vectors: `100000.0→fa47c35000`, `"IETF"→6449455446`, `[1,2,3]→83010203`, `{1:2,3:4}→a201020304`, `-1→20`.
- LoRa airtime (Semtech AN1200.13), SF7, BW 125 kHz, CR 4/5, preamble 8, explicit header, CRC on:
  `Tsym = 2^SF/BW; Tpre = (8+4.25)*Tsym; n_pay = 8 + max(ceil((8PL − 4SF + 28 + 16)/(4(SF − 2DE)))*(CR+4), 0); ToA = Tpre + n_pay*Tsym`, with `PL = payload + 13`, `DE=1` only if SF≥11.
- `E_msg = V*I_TX*ToA + E_RX_WINDOWS`. Expected: 38 B → ToA ≈ 82 ms → **E_msg ≈ 13.4 mJ**.
- **Energy/day** `= [reads*(E_SAMPLE + E_LOGIC if logic) + msgs*E_msg + N*V*I_SLEEP] / DAYS`.
- **Lifetime (years)** `= BATTERY_J / energy_per_day / 365` (model only; ignores self-discharge).

## 7. Metrics `evaluate(world, run, e_msg)`
- **msgs/day, reads/day.**
- **RMSE & P95:** receiver holds last reported value; compare to `truth` every 10 s.
- **Detection:** a report is an *alarm* if `|v − normal[t]| ≥ 2.5`. An event is detected if an alarm arrives at
  `t ∈ [window_start − 2, window_end]`; delay = `max(0, t − window_start)` for the first alarm.
  Detection % = detected/40. Mean delay is over detected events only.
- **False alarms/week:** alarm reports that carry a glitch and are not inside an event window.

## 8. Experiments
- `experiment`: seeds 100–129 (30 weeks). Report mean ± SD for 7 schemes (F10, F60, F600, SoD60, ASR, SoD10, ASR no-confirm) and sweeps `Imax ∈ {20,40,80,160,320}` for ASR and SoD period equivalent. Save `results.json`.
- `tune`: seeds 1–5; grid `imax ∈ {20,40,80,160,320} × delta ∈ {0.25,0.5,1.0}` and `look ∈ {0.4,0.5,0.6,0.75,1.0}`.
- **Never tune on test seeds.**

## 9. Performance
Pure Python lists (604,800 floats ×3). One world ≈ 1–2 s. Whole experiment < 3 min.

## 10. Dashboard (optional) technical notes
- Port the three schemes to JS; generate a **shorter world** (e.g. 6 hours) for speed.
- Canvas or inline SVG chart; no external CDN. Recompute on slider `input` with debounce 100 ms.

## 11. Code quality
Type hints optional; docstrings on every public function; no global mutable state besides constants; functions < 40 lines where possible.
