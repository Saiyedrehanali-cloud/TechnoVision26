# Send Less, Sense Smart: Adaptive Sample-and-Report for Longer-Lived IoT Sensor Nodes

**Authors:** Saiyed Rehan Ali, Kratika Mishra  
**Affiliation:** TechnoVision 2026–27  
**Correspondence:** Department of Computer Science & IoT Engineering  

---

## Abstract
Battery-powered Internet of Things (IoT) sensor nodes deployed in remote environmental and industrial monitoring typically utilize periodic sampling and reporting (e.g., every 60 seconds). Because environmental variables such as temperature change slowly during normal conditions, periodic reporting wastes the majority of battery energy transmitting redundant data. Conversely, lengthening the reporting interval to conserve battery power risks missing critical, rapid excursion events (such as cold-room door openings or thermal runaways). While threshold-based Send-on-Delta (SoD) reporting mitigates redundant transmissions, it remains highly vulnerable to transient sensor noise and single-sample glitches, resulting in spurious false alarms. 

In this paper, we propose **Adaptive Sample-and-Report (ASR)**, a lightweight, standard-compliant algorithm designed for resource-constrained microcontrollers. ASR combines:
1. An adaptive sampling interval that dynamically doubles up to $I_{\text{max}} = 80$ s during quiescent periods and contracts to $I_{\text{min}} = 10$ s upon dynamic activity;
2. A two-stage confirmation filter that rejects transient measurement spikes while reliably capturing genuine excursions; and
3. An RFC 8428 SenML/CBOR compact payload format over LoRaWAN.

Across 30 simulated weeks (seeds 100–129) of high-resolution temperature monitoring featuring diurnal cycles, AR(1) drift, 40 injected ramp events, sensor noise, and glitch spikes, ASR reduces daily energy consumption by **4.6×** compared to standard 60-second periodic reporting (4.9 J/day vs. 22.6 J/day). Furthermore, ASR eliminates false alarms almost entirely ($0.1$ vs. $4.8$ false alarms/week for SoD60) while maintaining a $96.4\%$ event detection rate, a mean latency of $34.7$ seconds, and a lower reconstruction RMSE ($0.330$ °C vs. $0.373$ °C for SoD60).

**Keywords:** Adaptive Sampling, Low-Power IoT, LoRaWAN, SenML, CBOR, Send-on-Delta, Glitch Rejection, Battery Lifetime.

---

## I. Introduction
Battery longevity is the primary design constraint for remote IoT sensing applications. In typical deployments—such as cold-chain logistics, agricultural telemetry, and building HVAC monitoring—nodes rely on non-rechargeable primary batteries expected to last between 3 to 10 years without maintenance.

In conventional sensor architectures, nodes employ **Fixed Periodic Reporting (FPR)**, waking up on a fixed schedule (e.g., $F_{60}$, once every 60 seconds) to sample the transducer and transmit the reading via long-range radios such as LoRaWAN. The physical reality of environmental signals, however, exhibits extreme temporal redundancy: for 95% of their lifetime, monitored variables fluctuate within narrow, predictable diurnal ranges. Transmitting identical readings every minute depletes the battery primarily in the radio power amplifier.

While naive power reduction strategies lengthen the reporting period (e.g., $F_{600}$, once every 10 minutes), this introduces catastrophic monitoring blindness: brief but high-consequence thermal excursion events (such as freezer doors left ajar or industrial overheating) ramp up, peak, and resolve undetected between wake-up cycles.

Threshold-driven schemes like **Send-on-Delta (SoD)** address transmission redundancy by transmitting only when $|x(t) - x_{\text{last}}| \ge \delta$. However, SoD suffers from two critical limitations:
- **Glitch Vulnerability:** Transient electrical noise, EMI spikes, or ADC settling errors trigger immediate transmissions, causing false alarms and wasted energy.
- **Fixed Sampling Inflexibility:** SoD typically samples at a fixed rate, missing subtle pre-event dynamics or burning unnecessary sensor-read energy during calm periods.

To solve this trade-off, we introduce **Adaptive Sample-and-Report (ASR)**.

---

## II. System & Energy Model

### A. LoRaWAN Airtime Model
We model a LoRaWAN Class-A end-device operating at EU868 / US915 with Spreading Factor 7 (SF7), 125 kHz bandwidth, and Coding Rate 4/5 ($CR=1$). In accordance with the Semtech AN1200.13 specification:
$$\text{ToA} = T_{\text{pre}} + n_{\text{payload}} \times T_{\text{sym}}$$
where symbol duration $T_{\text{sym}} = \frac{2^{\text{SF}}}{\text{BW}} = \frac{128}{125000} = 1.024\text{ ms}$, preamble duration $T_{\text{pre}} = (8 + 4.25) \times T_{\text{sym}} = 12.544\text{ ms}$, and:
$$n_{\text{payload}} = 8 + \max\left(\left\lceil \frac{8 \cdot PL - 4 \cdot \text{SF} + 28 + 16}{4(\text{SF} - 2\cdot DE)} \right\rceil \times (CR + 4),\, 0\right)$$
where total physical payload $PL = \text{Payload}_{\text{app}} + 13$ bytes (accounting for LoRaWAN MHDR, FHDR, FPort, and MIC).

### B. Payload Serialization: SenML/CBOR vs. JSON
To maximize transmission efficiency without sacrificing semantic interoperability, data is structured as an RFC 8428 Sensor Measurement List (SenML) and encoded using RFC 8949 Concise Binary Object Representation (CBOR):
- Compact SenML-CBOR record: `[{-3: uint32(t), 0: "temp", 1: "Cel", 2: float32(v)}]`
- Size: Exactly **25 bytes** (vs. ~46 bytes for SenML-JSON).
- Combined with 13-byte LoRaWAN MAC overhead ($PL = 38$ bytes), the Time-on-Air is exactly:
  $$\text{ToA}_{38\text{B}} = 82.18\text{ ms}$$

### C. Electrical Energy Model
Node energy per day $E_{\text{day}}$ is calculated from physical parameters:
$$E_{\text{msg}} = V_{\text{supply}} \cdot I_{\text{tx}} \cdot \text{ToA} + E_{\text{rx\_windows}} = (3.3\text{ V} \cdot 44\text{ mA} \cdot 82.18\text{ ms}) + 1.5\text{ mJ} = 13.43\text{ mJ}$$
$$E_{\text{day}} = \frac{N_{\text{reads}} \cdot (E_{\text{sample}} + E_{\text{logic}}) + N_{\text{msgs}} \cdot E_{\text{msg}} + T_{\text{day}} \cdot V_{\text{supply}} \cdot I_{\text{sleep}}}{7}$$
Parameters (TRD §3):
- $V_{\text{supply}} = 3.3\text{ V}$
- $I_{\text{tx}} = 44\text{ mA}$ (~+14 dBm transmit power)
- $E_{\text{rx\_windows}} = 1.5\text{ mJ}$ (two Class-A downlink receive slots)
- $E_{\text{sample}} = 0.30\text{ mJ}$ per sensor acquisition
- $E_{\text{logic}} = 0.02\text{ mJ}$ MCU compute overhead for SoD/ASR
- $I_{\text{sleep}} = 10\ \mu\text{A}$ continuous deep sleep current
- Battery capacity: 2000 mAh at 3.0 V = $21,600\text{ J}$

---

## III. The ASR Algorithm

ASR operates as an event-driven loop executing on the micro-controller:

```
Algorithm 1: ASR Wakeup Execution
Input: Current time t, baseline base, last transmitted x_last, last report time t_last
Parameters: imin=10s, imax=80s, delta=0.5C, heartbeat=900s, jump=2.0C, confirm_gap=2s, confirm_tol=1.5C, look=0.75

1:  t <- t + interval
2:  x <- read_sensor(t); reads <- reads + 1
3:  // Stage 1: Two-stage Glitch Confirmation Filter
4:  if |x - base| >= jump then
5:      t <- t + confirm_gap
6:      x2 <- read_sensor(t); reads <- reads + 1
7:      if |x2 - base| < confirm_tol then
8:          // Transient glitch: discard and sleep
9:          return (interval unchanged)
10:     end if
11:     // Confirmed real excursion event
12:     transmit(x2); x_last <- x2; t_last <- t; base <- x2
13:     interval <- imin; return
14: end if
15: // Stage 2: Slow baseline tracking (EWMA)
16: base <- base + 0.1 * (x - base)
17: // Stage 3: Send-on-Delta & Heartbeat
18: if |x - x_last| >= delta OR (t - t_last) >= heartbeat then
19:     transmit(x); x_last <- x; t_last <- t
20:     interval <- imin
21: else if |x - x_last| >= look * delta then
22:     // Pre-event alert: contract sampling rate
23:     interval <- imin
24: else
25:     // Quiescent relaxation: double sleep period
26:     interval <- min(2 * interval, imax)
27: end if
```

---

## IV. Experimental Evaluation

### A. Synthetic World Generation
We evaluate all schemes over 30 test weeks (seeds 100–129) at 1-second resolution (604,800 steps/week). The true signal comprises:
1. Normal diurnal cycle: $24 + 4 \sin(2\pi(t/86400 - 0.25))$ °C;
2. Auto-regressive drift: $d_t = 0.9999 d_{t-1} + \mathcal{N}(0, 0.003^2)$;
3. 40 injected excursion events per week: amplitudes $\pm \mathcal{U}(4, 8)$ °C, 20-second linear ramp-up, variable hold (5–60s or 240–1700s), and 60-second ramp-down;
4. Measurement noise: $\mathcal{N}(0, 0.10^2)$ °C;
5. Glitches: transient spikes $\pm \mathcal{U}(6, 12)$ °C injected with probability $p = 5 \times 10^{-4}$.

### B. Benchmark Schemes
- **F10**: Read and send every 10 seconds.
- **F60**: Read and send every 60 seconds (standard IoT baseline).
- **F600**: Read and send every 600 seconds (10 minutes).
- **SoD60**: Sample every 60 seconds; send if $\Delta \ge 0.5$ °C or heartbeat 900 s.
- **ASR**: Proposed adaptive scheme ($I_{\text{min}}=10$ s, $I_{\text{max}}=80$ s, $\delta=0.5$ °C).

### C. Experimental Results (30-Week Average)

| Scheme | Uplinks/day | Daily Energy | Event Detection % | Mean Delay (s) | RMSE (°C) | False Alarms/week |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **F10** | 8,640.0 | 121.5 J | $100.0 \pm 0.0\%$ | $6.2 \pm 0.6$ | 0.227 | 28.9 |
| **F60** | 1,440.0 | 22.6 J | $99.3 \pm 1.1\%$ | $30.9 \pm 2.7$ | 0.356 | 4.8 |
| **F600** | 144.0 | 4.8 J | $54.3 \pm 6.8\%$ | $246.3 \pm 35.0$ | 0.925 | 0.4 |
| **SoD60** | 110.5 | 4.8 J | $99.1 \pm 1.4\%$ | $30.8 \pm 2.7$ | 0.373 | 4.8 |
| **ASR** | **118.1** | **4.9 J** | **$96.4 \pm 3.8\%$** | **$34.7 \pm 3.7$** | **0.330** | **0.1** |

---

## V. Key Findings & Discussion

1. **4.6× Energy Reduction vs. F60**:  
   ASR cuts energy from 22.6 J/day to 4.9 J/day, extending battery lifetime on a 2000 mAh cell from 2.6 years to **12.1 years** (theoretical model).
2. **False Alarm Immunity**:  
   While SoD60 and F60 transmit false alarms whenever a sensor glitch occurs (~4.8 false alarms/week), ASR’s two-stage re-read filter drops false alarms to **0.1/week** (a 98% reduction).
3. **Signal Reconstruction Superiority**:  
   ASR achieves an RMSE of **0.330 °C**, superior to SoD60 (0.373 °C), because ASR dynamically tightens its sampling rate to 10 seconds during rapid transients.
4. **Honest Limitations**:  
   Compared to F10, ASR exhibits a slight detection latency penalty (34.7s vs 6.2s), but saves **96% of total energy**.

---

## VI. Conclusion
Adaptive Sample-and-Report (ASR) resolves the classic trade-off between energy conservation and event responsiveness in battery-powered IoT sensing. By combining adaptive sampling relaxation with two-stage glitch rejection and SenML/CBOR compact serialization, ASR delivers the energy benefits of aggressive duty cycling while maintaining high detection fidelity and near-zero false alarms.

---

## References
1. Semtech Corporation, *SX1272/73/76/77/78: LoRa Modem Designer’s Guide*, AN1200.13, 2013.
2. C. Bormann et al., *RFC 8428: Sensor Measurement Lists (SenML)*, IETF RFC, 2018.
3. C. Bormann and P. Hoffman, *RFC 8949: Concise Binary Object Representation (CBOR)*, IETF RFC, 2020.
4. J. M. M. et al., "Event-Triggered and Self-Triggered Control: A Review," *IEEE Trans. Automat. Contr.*, 2012.

