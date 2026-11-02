# APP_FLOW — User flow and program flow

## 1. User flow (CLI)
```
Start
 └─ python iot_asr_demo.py [mode]
      ├─ demo        → prints story of ONE event: what each scheme reported + energy per uplink   (≈5 s)
      ├─ experiment  → progress dots (30 weeks) → results table → saves results.json            (≈1–3 min)
      └─ tune        → parameter sweeps on training seeds → printed tables
 (no mode)          → defaults to `experiment`
```
Errors: unknown mode → print usage and exit code 2.

## 2. Presenter flow (live demo in front of teachers)
1. Open terminal in project folder.
2. Run `python iot_asr_demo.py demo` → show that F60 reports every minute, ASR only on change, and both catch the event.
3. (Optional) Open `dashboard/index.html` → move the δ slider → watch messages/day change.
4. Return to slides; show the results table (from `experiment`).

## 3. Program flow — `experiment`
```
for seed in 100..129:
    world = make_world(seed)                      # truth, noise, glitches, events
    for scheme in [F10,F60,F600,SoD60,ASR,SoD10,ASR-no-confirm]:
        reports, reads = run_scheme(world)        # list of (t, value, is_glitch)
        metrics = evaluate(world, reports, reads) # energy, detection, delay, RMSE, FA
        collect(metrics)
    for Imax in [20..320]: also run ASR and SoD sweeps
aggregate mean ± SD → print table → write results.json
```

## 4. Program flow — one ASR wake-up
```
wake → read x
  ├─ |x − base| ≥ 2.0 ?
  │     ├─ yes → wait 2 s → read x2
  │     │         ├─ |x2 − base| < 1.5 → GLITCH: discard, go to sleep
  │     │         └─ else → SEND x2, base = x2, interval = 10 s, sleep
  │     └─ no  ↓
  ├─ update base (EWMA 0.1)
  ├─ |x − last| ≥ 0.5  OR  15 min since last send ?
  │     └─ yes → SEND x, interval = 10 s, sleep
  ├─ |x − last| ≥ 0.375 ? → interval = 10 s, sleep
  └─ else → interval = min(2·interval, 80 s), sleep
```

## 5. Dashboard flow (optional)
```
Open page → default scenario auto-runs → chart + 3 stat cards
 → user moves slider (δ, Imax, event size, glitch rate) → recompute → chart/cards update
 → user toggles schemes on/off (F60, F600, SoD60, ASR) → legend + cards update
 → "New random week" button → new seed → rerun
```
