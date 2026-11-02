# Send Less, Sense Smart — ASR Simulator

**Research Paper:** *"Send Less, Sense Smart: Adaptive Sample-and-Report for Longer-Lived IoT Sensor Nodes"*  
**Authors:** Saiyed Rehan Ali, Kratika Mishra  
**Context:** TechnoVision 2026–27

An IoT reporting simulator built using **strictly the Python standard library** (no third-party dependencies required). It models a battery-powered sensor node over 1 synthetic week (604,800 seconds) with diurnal temperature cycles, AR(1) drift, sensor noise, injected ramp events, and transient glitches.

It evaluates 5 reporting schemes:
1. **F10** (Fixed 10-second period)
2. **F60** (Fixed 60-second period — industry baseline)
3. **F600** (Fixed 10-minute period)
4. **SoD60** (Send-on-Delta 60-second sampling, $\delta = 0.5$ °C)
5. **ASR** (Adaptive Sample-and-Report — proposed scheme with two-stage glitch rejection)

---

## 1. Quick Start

Ensure you have Python 3.9+ installed. No `pip install` required!

### A. Live Presentation Demo (< 1 second)
```powershell
python iot_asr_demo.py demo
```
*Tells the story of an injected temperature excursion event, comparing how F60 reports periodically while ASR adapts sleep intervals and uses confirmation to reject glitches.*

### B. Full 30-Week Research Experiment
```powershell
python iot_asr_demo.py experiment
```
*Evaluates seeds 100–129 across all schemes and sweeps over $I_{\text{max}} \in \{20, 40, 80, 160, 320\}$ seconds. Outputs the research summary table and saves `results.json`.*

### C. Parameter Tuning Grid Search
```powershell
python iot_asr_demo.py tune
```
*Sweeps $I_{\text{max}} \in \{20, 40, 80, 160, 320\}$, $\delta \in \{0.25, 0.5, 1.0\}$, and $\text{look} \in \{0.4, 0.5, 0.6, 0.75, 1.0\}$ on training seeds 1–5.*

### D. Run Unit Test Suite
```powershell
python -m unittest discover -s tests
```
*Runs all 18 automated unit tests verifying RFC 8949 CBOR encoding vectors, SenML 25-byte records, Semtech LoRa airtime, message energy, world generation reproducibility, and glitch rejection.*

---

## 2. Research Results Summary (30 Test Weeks, Seeds 100–129)

| Scheme | Msgs/day | Daily Energy (J/day) | Detected % | Mean Delay (s) | RMSE (°C) | False Alarms/week |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **F10** | 8,640.0 | 121.5 J | 100.0% | 6.2 s | 0.227 | 28.9 |
| **F60** | 1,440.0 | 22.6 J | 99.3% | 30.9 s | 0.356 | 4.8 |
| **F600** | 144.0 | 4.8 J | 54.3% | 246.3 s | 0.925 | 0.4 |
| **SoD60** | 110.5 | 4.8 J | 99.1% | 30.8 s | 0.373 | 4.8 |
| **ASR** | **118.1** | **4.9 J** | **96.4%** | **34.7 s** | **0.330** | **0.1** |

### Key Takeaways:
- **4.6× Energy Reduction**: ASR consumes only 4.9 J/day compared to 22.6 J/day for standard 1-minute fixed reporting (F60).
- **Glitch Rejection**: While F60, F10, and SoD suffer from false alarms due to transient spikes, ASR's two-stage confirmation filter eliminates almost 100% of glitch false alarms (0.1/wk vs 4.8/wk).
- **High Detection Quality**: Catches >96% of events with a tight 34-second delay and superior signal reconstruction RMSE (0.330 °C).

---

## 3. Interactive Web Dashboard (Offline)

An interactive, single-file dashboard is included in `dashboard/index.html`.

- **To run**: Simply double-click `dashboard/index.html` or open it in any web browser (Chrome, Edge, Firefox, Safari).
- **Features**:
  - Live canvas chart with 6-hour simulated temperature excursions.
  - Interactive sliders for $\delta$ threshold, $I_{\text{max}}$ interval, event magnitude, and glitch frequency.
  - Live metric cards updating in real time.
  - Toggle individual schemes on/off.
  - Works completely offline with zero external CDNs or JavaScript libraries.

---

## 4. Publication Figures

To generate publication figures for the research paper:
```powershell
python generate_figures.py
```
Outputs standalone SVG vector files in `figures/`:
1. `fig1_energy_breakdown.svg` — Stacked bars of sleep floor, sensing reads, and radio transmissions.
2. `fig2_tradeoff_curves.svg` — Two-panel trade-off curves (Delay vs Energy & RMSE vs Energy).
3. `fig3_block_diagram.svg` — ASR Node architecture and adaptive timer feedback loop.

---

## 5. Project Architecture & Standards

- **CBOR Encoder**: Compliant with RFC 8949 (test vectors passed).
- **Payload Format**: RFC 8428 SenML/CBOR temperature records (integer labels: `bt=-3`, `n=0`, `u=1`, `v=2`) yielding 25 bytes.
- **Radio & Physical Layer**: Semtech AN1200.13 Time-on-Air (ToA) model for LoRaWAN SF7 / 125 kHz / CR 4/5 (82.18 ms, 13.43 mJ per message at 3.3 V / 44 mA).
