# TESTING — Verify the project is correct

## 1. Unit tests (must pass)
| Test | Expected |
|------|----------|
| CBOR `100000.0` | `fa47c35000` |
| CBOR `"IETF"` | `6449455446` |
| CBOR `[1,2,3]` | `83010203` |
| CBOR `{1:2,3:4}` | `a201020304` |
| CBOR `-1` | `20` |
| SenML-CBOR record length | 25 bytes |
| SenML-JSON record length | ≈ 50 bytes |
| Airtime for 38 B at SF7/125 kHz | ≈ 82 ms |
| `message_energy(25)` | ≈ 13.4 mJ |
| `make_world(7)` twice | identical data |
| Event count per world | 40 |

## 2. Sanity checks
- F10 detection ≈ 100%; delay a few seconds.
- F600 misses many short events (detection ≈ 50–60%).
- ASR false alarms ≈ 0; SoD/F schemes show glitch false alarms.
- ASR `confirm=False` → false alarms rise to ≈ 4–5/week.

## 3. Expected experiment output (30 test weeks, seeds 100–129; accept ±3%)
| Scheme | Msgs/day | J/day | Detected % | Delay (s) | RMSE | False al./wk |
|--------|---------:|------:|-----------:|----------:|-----:|-------------:|
| F10 | 8,640 | 121.5 | 100.0 | 6.1 | 0.227 | 28.9 |
| F60 | 1,440 | 22.6 | 99.3 | 30.7 | 0.356 | 4.8 |
| F600 | 144 | 4.8 | 54.2 | 245.8 | 0.925 | 0.4 |
| SoD60 | 110.5 | 4.8 | 99.1 | 30.6 | 0.373 | 4.8 |
| **ASR** | **118.5** | **4.9** | **97.2** | **33.1** | **0.325** | **0.0** |

Ablations: SoD10 → 7.73 J/day, 8,640 reads/day, RMSE 0.249, 28.9 false alarms; ASR no-confirm → 4.92 J/day, 4.5 false alarms.  
Derived: F60/ASR energy ratio ≈ 4.6×; JSON vs CBOR energy per message: 18.6 vs 13.4 mJ (−28%).

> If exact decimals differ slightly, check RNG call order in TRD §4. Do **not** edit expected values to match the code.

## 4. Dashboard checks (if built)
- Moving δ up → ASR/SoD messages/day goes down, RMSE goes up.
- Imax = 320 → fewer reads, lower detection %.
- Works offline; no console errors; keyboard-operable sliders.

## 5. Final checklist before presenting
- [ ] `experiment` table matches §3  [ ] `demo` runs in < 10 s  [ ] README steps work on a clean machine
- [ ] No hard-coded results in code  [ ] Assumptions stated in code comments and in the paper
