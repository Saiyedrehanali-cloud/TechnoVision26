# UI_UX — Interface design

## 0. Design tokens (same palette as the paper figures and slides)
| Token | Hex | Use |
|-------|-----|-----|
| navy | #1F3A5F | titles, headers, dark backgrounds |
| teal | #0E9F8E | ASR, primary highlight |
| orange | #F28C28 | send-on-delta, warnings |
| red | #E4572E | radio/energy cost, F60 |
| green | #3BA55D | success, "good" |
| purple | #7E57C2 | timer rule, cloud |
| blue | #4A90D9 | sensor, sleep floor |
| bg | #F4F8FC | page background |
| ink | #1B2A41 | body text |
| muted | #6B7C93 | captions |
Fonts: headings Cambria/serif; body Calibri/Inter/system-ui; code Courier New/monospace.  
Rules: body text ≥ 14 px, strong contrast, never colour-only meaning (add labels/markers).

## 1. CLI output design
```
=== ASR Simulator — experiment (30 weeks, seeds 100–129) ===
..............................
Scheme   Msgs/day  J/day  Detected%  Delay(s)  RMSE   FalseAl/wk
F10        8640.0  121.5   100.0±0.0   6.1±0.6  0.227   28.9
F60        1440.0   22.6    99.3±1.1  30.7±2.4  0.356    4.8
F600        144.0    4.8    54.2±6.6 245.8±34.7 0.925    0.4
SoD60       110.5    4.8    99.1±1.2  30.6±2.4  0.373    4.8
ASR         118.5    4.9    97.2±3.3  33.1±3.5  0.325    0.0   ← proposed
Saved results.json
```
- Fixed-width columns, aligned numbers, one line per scheme, ASR line marked.
- `demo` prints short sentences ("Event starts at 12:41, lasts ~3 min") before the numbers.

## 2. Web dashboard (optional) — wireframe
```
┌──────────────────────────────────────────────────────────────┐
│ Send Less, Sense Smart — ASR Simulator          [New week ⟳] │  header (navy)
├───────────────┬──────────────────────────────────────────────┤
│ CONTROLS      │  CHART: true signal (grey line)              │
│ δ  [──●───] 0.5│        + report dots per scheme             │
│ Imax[──●──] 80 │        + shaded event windows (light red)   │
│ Event size ... │        x: time (6 h)   y: °C                │
│ Glitch rate .. │                                              │
│ Schemes:       ├──────────┬──────────┬──────────┬─────────────┤
│ ☑ F60  ☑ F600  │ Messages │ Energy   │ Events   │ False       │
│ ☑ SoD60 ☑ ASR  │ per day  │ J/day    │ caught % │ alarms      │
│               │  (cards, colour = scheme)                     │
└───────────────┴──────────────────────────────────────────────┘
```
- Desktop first; below 800 px stack controls above chart.
- Cards: big number (40 px bold), label (14 px), scheme-colour left border.
- Interactions: sliders update live (debounce 100 ms); hover on chart shows value + time; legend toggles.
- Empty/loading: show "Simulating…" skeleton for < 1 s.
- Accessibility: slider labels, aria-live on stat cards, alt text on chart, keyboard operable.

## 3. Figures (for the paper)
1. Energy breakdown stacked bars (blue sleep, yellow reads, red radio), totals on top.
2. Two-panel trade-off: (a) delay vs energy (log y), (b) RMSE vs energy; ASR teal solid, SoD orange dashed, F600 red triangle; chosen setting ringed green.
3. Block diagram: Read → (1) glitch filter → (2) report → uplink → cloud; (3) timer loop.
Size 3.3 in wide (single IEEE column), 300 dpi, labels ≥ 6 pt.
