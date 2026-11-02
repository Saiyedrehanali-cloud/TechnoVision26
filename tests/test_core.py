"""
Comprehensive Unit Test Suite for ASR Simulator.
Covers all requirements from docs/TESTING.md and docs/TRD.md.
"""

import unittest
from iot_asr_demo import (
    encode_cbor,
    build_senml_cbor,
    build_senml_json,
    lora_airtime,
    message_energy,
    daily_energy,
    make_world,
    run_fixed,
    run_sod,
    run_asr,
    evaluate,
    V_SUPPLY,
    I_TX,
    E_RX_WINDOWS,
    E_SAMPLE,
    E_LOGIC,
    I_SLEEP,
    BATTERY_J,
    LORAWAN_OVERHEAD,
    N,
    DAYS
)


class TestCBORandEnergy(unittest.TestCase):
    """Section 1: RFC 8949 vectors, SenML records, and LoRaWAN energy model."""

    def test_rfc8949_float32(self):
        """CBOR vector: 100000.0 -> fa47c35000"""
        self.assertEqual(encode_cbor(100000.0).hex(), "fa47c35000")

    def test_rfc8949_string(self):
        """CBOR vector: 'IETF' -> 6449455446"""
        self.assertEqual(encode_cbor("IETF").hex(), "6449455446")

    def test_rfc8949_list(self):
        """CBOR vector: [1, 2, 3] -> 83010203"""
        self.assertEqual(encode_cbor([1, 2, 3]).hex(), "83010203")

    def test_rfc8949_dict(self):
        """CBOR vector: {1: 2, 3: 4} -> a201020304"""
        self.assertEqual(encode_cbor({1: 2, 3: 4}).hex(), "a201020304")

    def test_rfc8949_negative_int(self):
        """CBOR vector: -1 -> 20"""
        self.assertEqual(encode_cbor(-1).hex(), "20")

    def test_senml_cbor_length(self):
        """SenML-CBOR record length must be exactly 25 bytes."""
        payload_1 = build_senml_cbor(100000, 24.12)
        payload_0 = build_senml_cbor(0, 24.12)
        payload_end = build_senml_cbor(604800, 31.85)
        self.assertEqual(len(payload_1), 25)
        self.assertEqual(len(payload_0), 25)
        self.assertEqual(len(payload_end), 25)

    def test_senml_json_length(self):
        """SenML-JSON record length should be approx 45-50 bytes."""
        json_payload = build_senml_json(100000, 24.12)
        self.assertTrue(40 <= len(json_payload) <= 55, f"Unexpected length: {len(json_payload)}")

    def test_lora_airtime_38b(self):
        """Airtime for 38 B (25B payload + 13B overhead) at SF7/125kHz should be ~82 ms."""
        toa_s = lora_airtime(25)
        toa_ms = toa_s * 1000.0
        self.assertAlmostEqual(toa_ms, 82.176, delta=0.5)

    def test_message_energy(self):
        """message_energy(25) at SF7 should be ~13.4 mJ."""
        e_j = message_energy(25)
        e_mj = e_j * 1000.0
        self.assertAlmostEqual(e_mj, 13.432, delta=0.1)


class TestWorldGenerator(unittest.TestCase):
    """Section 2: World data generation, reproducibility, and event injection."""

    def test_reproducibility(self):
        """Calling make_world with identical seed must yield identical data."""
        w1 = make_world(7)
        w2 = make_world(7)
        self.assertEqual(w1['truth'][:100], w2['truth'][:100])
        self.assertEqual(w1['event_windows'], w2['event_windows'])
        self.assertEqual(w1['glitches'], w2['glitches'])

    def test_event_count(self):
        """Each simulated week must have exactly 40 injected events."""
        w = make_world(42)
        self.assertEqual(len(w['event_windows']), 40)

    def test_glitch_frequency(self):
        """Glitches should be a few hundred per week (p=5e-4 on 604,800 steps ≈ 300)."""
        w = make_world(42)
        self.assertTrue(200 <= len(w['glitches']) <= 450)

    def test_temperature_range(self):
        """Truth temperatures should stay within realistic bounds (~10 °C to ~40 °C)."""
        w = make_world(42)
        min_t = min(w['truth'])
        max_t = max(w['truth'])
        self.assertTrue(10.0 <= min_t <= 22.0)
        self.assertTrue(28.0 <= max_t <= 42.0)


class TestSchemesAndMetrics(unittest.TestCase):
    """Section 3: Scheme execution logic, message counts, and metric evaluation."""

    @classmethod
    def setUpClass(cls):
        cls.world = make_world(100)

    def test_fixed_period_message_counts(self):
        """F10, F60, and F600 must generate exact message counts over 1 week."""
        reps_10, rds_10 = run_fixed(self.world, 10)
        self.assertEqual(len(reps_10), 60480)
        self.assertEqual(rds_10, 60480)

        reps_60, rds_60 = run_fixed(self.world, 60)
        self.assertEqual(len(reps_60), 10080)
        self.assertEqual(rds_60, 10080)

        reps_600, rds_600 = run_fixed(self.world, 600)
        self.assertEqual(len(reps_600), 1008)
        self.assertEqual(rds_600, 1008)

    def test_f10_detection_quality(self):
        """F10 samples every 10s and should detect ~100% of events with short delay."""
        reps, rds = run_fixed(self.world, 10)
        m = evaluate(self.world, reps, rds, has_logic=False)
        self.assertAlmostEqual(m['detected_pct'], 100.0, delta=1.0)
        self.assertTrue(m['delay'] <= 10.0)

    def test_f600_misses_events(self):
        """F600 samples only every 10 minutes and should miss short events (50-75% detection)."""
        reps, rds = run_fixed(self.world, 600)
        m = evaluate(self.world, reps, rds, has_logic=False)
        self.assertTrue(45.0 <= m['detected_pct'] <= 80.0)
        self.assertTrue(m['delay'] >= 100.0)

    def test_asr_glitch_rejection(self):
        """ASR with confirmation filter rejects transient glitches (false alarms ~0)."""
        reps, rds = run_asr(self.world, confirm=True)
        m = evaluate(self.world, reps, rds, has_logic=True)
        self.assertTrue(m['false_alarms'] <= 1)

    def test_asr_no_confirm_ablation(self):
        """Disabling ASR confirmation (confirm=False) causes false alarms to rise."""
        reps, rds = run_asr(self.world, confirm=False)
        m = evaluate(self.world, reps, rds, has_logic=True)
        self.assertTrue(m['false_alarms'] >= 3)


if __name__ == '__main__':
    unittest.main()
