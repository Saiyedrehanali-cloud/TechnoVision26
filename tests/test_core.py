"""
Unit tests for ASR Simulator core functions.
Validates RFC 8949 CBOR encoding, SenML payload sizes, and LoRaWAN airtime/energy models.
"""

import unittest
from iot_asr_demo import (
    encode_cbor,
    build_senml_cbor,
    build_senml_json,
    lora_airtime,
    message_energy,
    daily_energy,
    V_SUPPLY,
    I_TX,
    E_RX_WINDOWS,
    E_SAMPLE,
    E_LOGIC,
    I_SLEEP,
    BATTERY_J,
    LORAWAN_OVERHEAD
)


class TestCBORandEnergy(unittest.TestCase):
    """Test suite covering Milestone 1 & 2 requirements from docs/TESTING.md."""

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

    def test_constants_defined(self):
        """Verify standard constants match TRD Section 3."""
        self.assertEqual(LORAWAN_OVERHEAD, 13)
        self.assertEqual(V_SUPPLY, 3.3)
        self.assertEqual(I_TX, 0.044)
        self.assertEqual(E_RX_WINDOWS, 1.5e-3)
        self.assertEqual(E_SAMPLE, 0.30e-3)
        self.assertEqual(E_LOGIC, 0.02e-3)
        self.assertEqual(I_SLEEP, 10e-6)
        self.assertEqual(BATTERY_J, 21600.0)


if __name__ == '__main__':
    unittest.main()
