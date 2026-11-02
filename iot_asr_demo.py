"""
ASR Simulator — Adaptive Sample-and-Report for IoT Sensor Nodes.
Research paper: "Send Less, Sense Smart"
Authors: Saiyed Rehan Ali, Kratika Mishra (Technovision 2026–27)

Core simulator for comparing battery-powered IoT reporting schemes:
F10, F60, F600, SoD60, and ASR.

Standard library only.
"""

import json
import math
import struct
import sys
from typing import Any, Dict, List, Tuple, Union

# ==============================================================================
# CONSTANTS & ASSUMPTIONS (TRD Section 3)
# All physical, electrical, and radio parameters are documented here.
# ==============================================================================

# Time constants (1-second resolution over 1 week)
DAY = 86400                           # Seconds per day
DAYS = 7                              # Simulation duration in days
N = DAY * DAYS                        # Total simulation steps (604,800 seconds)

# Electrical & battery assumptions
V_SUPPLY = 3.3                        # Supply voltage (Volts)
I_TX = 0.044                          # Radio transmit current (~+14 dBm, 44 mA)
E_RX_WINDOWS = 1.5e-3                 # Energy for two Class-A receive windows (1.5 mJ)
E_SAMPLE = 0.30e-3                    # Energy per sensor reading (0.30 mJ)
E_LOGIC = 0.02e-3                     # Extra MCU compute energy per read for SoD/ASR (0.02 mJ)
I_SLEEP = 10e-6                       # Deep sleep current (10 uA)
BATTERY_J = 2.0 * 3600.0 * 3.0        # Battery capacity: 2000 mAh at 3.0 V = 21,600 Joules

# LoRaWAN and protocol assumptions
LORAWAN_OVERHEAD = 13                 # LoRaWAN header + MIC overhead (bytes): MHDR(1)+FHDR(7)+FPort(1)+MIC(4)
ALARM_BAND = 2.5                      # Detection threshold: deviation from normal profile (°C)

# Default LoRa physical layer parameters (EU868 / US915 standard uplink)
LORA_SF = 7                           # Spreading factor 7
LORA_BW = 125000                      # Bandwidth 125 kHz
LORA_CR = 1                           # Coding rate 4/5 (1 represents 4/5 in Semtech formula)
LORA_PREAMBLE = 8                     # Preamble symbols (default 8)


# ==============================================================================
# CBOR ENCODER (RFC 8949 Minimal Implementation, TRD Section 6)
# Standard library only, no external cbor/cbor2 dependency.
# ==============================================================================

class Uint32:
    """Helper wrapper to encode an integer explicitly as a 32-bit unsigned integer (5 bytes)."""
    def __init__(self, val: int):
        self.val = int(val)


def _encode_uint(val: int, major: int = 0) -> bytes:
    """Encode an unsigned integer with the given CBOR major type (0-7)."""
    prefix = major << 5
    if val < 24:
        return bytes([prefix | val])
    elif val < 256:
        return bytes([prefix | 24]) + struct.pack('>B', val)
    elif val < 65536:
        return bytes([prefix | 25]) + struct.pack('>H', val)
    elif val < 4294967296:
        return bytes([prefix | 26]) + struct.pack('>I', val)
    else:
        return bytes([prefix | 27]) + struct.pack('>Q', val)


def encode_cbor(obj: Any) -> bytes:
    """
    Encode a Python object into canonical minimal CBOR (RFC 8949).
    
    Supports:
    - Unsigned integers (major 0)
    - Negative integers (major 1)
    - Float32 numbers (major 7, 0xfa)
    - UTF-8 text strings (major 3)
    - Lists / tuples (major 4)
    - Dicts / maps (major 5)
    - Bytes (major 2)
    - Booleans (major 7)
    - Explicit Uint32 wrapper (major 0 with 4-byte uint)
    """
    if isinstance(obj, bool):
        return bytes([0xf5 if obj else 0xf4])
    elif isinstance(obj, Uint32):
        return bytes([(0 << 5) | 26]) + struct.pack('>I', obj.val)
    elif isinstance(obj, int):
        if obj >= 0:
            return _encode_uint(obj, 0)
        else:
            return _encode_uint(-1 - obj, 1)
    elif isinstance(obj, float):
        # RFC 8949 test vector 100000.0 -> fa47c35000 (IEEE 754 single-precision float32)
        return bytes([0xfa]) + struct.pack('>f', obj)
    elif isinstance(obj, str):
        utf8_bytes = obj.encode('utf-8')
        return _encode_uint(len(utf8_bytes), 3) + utf8_bytes
    elif isinstance(obj, (list, tuple)):
        header = _encode_uint(len(obj), 4)
        return header + b''.join(encode_cbor(item) for item in obj)
    elif isinstance(obj, dict):
        header = _encode_uint(len(obj), 5)
        return header + b''.join(encode_cbor(k) + encode_cbor(v) for k, v in obj.items())
    elif isinstance(obj, bytes):
        return _encode_uint(len(obj), 2) + obj
    else:
        raise TypeError(f"Unsupported type for CBOR encoding: {type(obj)}")


# ==============================================================================
# SENML PAYLOAD BUILDERS (TRD Section 6)
# ==============================================================================

def build_senml_json(t: int, v: float) -> str:
    """
    Build a compact SenML-JSON temperature record string.
    
    Format: [{"bt": t, "n": "temp", "u": "Cel", "v": round(v, 2)}]
    Yields approx. 45–50 bytes depending on timestamp length.
    """
    record = [{
        "bt": int(t),
        "n": "temp",
        "u": "Cel",
        "v": round(float(v), 2)
    }]
    return json.dumps(record, separators=(',', ':'))


def build_senml_cbor(t: int, v: float) -> bytes:
    """
    Build a standard 25-byte SenML-CBOR temperature record.
    
    RFC 8428 SenML integer labels:
      Base Time (bt): -3  (stored as 32-bit unsigned int for fixed 5-byte representation)
      Name (n):        0  ("temp", 4 bytes string -> 5 bytes)
      Unit (u):        1  ("Cel",  3 bytes string -> 4 bytes)
      Value (v):       2  (float32 single precision -> 5 bytes)
    Array (1 item) + Map (4 items) = 2 bytes overhead.
    Total: 1 + 1 + (1+5) + (1+5) + (1+4) + (1+5) = 25 bytes.
    """
    record = [{
        -3: Uint32(int(t)),
        0: "temp",
        1: "Cel",
        2: round(float(v), 2)
    }]
    return encode_cbor(record)


# ==============================================================================
# LORAWAN AIRTIME & ENERGY MODEL (Semtech AN1200.13, TRD Section 6)
# ==============================================================================

def lora_airtime(payload_len: int,
                 sf: int = LORA_SF,
                 bw: int = LORA_BW,
                 cr: int = LORA_CR,
                 preamble: int = LORA_PREAMBLE) -> float:
    """
    Calculate LoRa packet Time-on-Air (ToA) in seconds.
    
    Formula from Semtech AN1200.13:
      PL = payload_len + 13 (LoRaWAN MAC overhead)
      Tsym = 2^SF / BW
      Tpre = (preamble + 4.25) * Tsym
      DE = 1 if SF >= 11 else 0 (Low Data Rate Optimization)
      n_pay = 8 + max(ceil((8*PL - 4*SF + 28 + 16) / (4*(SF - 2*DE))) * (CR + 4), 0)
      ToA = Tpre + n_pay * Tsym
    
    For 25-byte payload + 13-byte overhead = 38 bytes at SF7/125 kHz:
      ToA ≈ 0.082176 s (82.18 ms)
    """
    pl = payload_len + LORAWAN_OVERHEAD
    de = 1 if sf >= 11 else 0
    t_sym = (2.0 ** sf) / float(bw)
    t_pre = (preamble + 4.25) * t_sym
    
    term = (8 * pl - 4 * sf + 28 + 16) / (4.0 * (sf - 2 * de))
    n_pay = 8 + max(math.ceil(term) * (cr + 4), 0)
    toa = t_pre + n_pay * t_sym
    return toa


def message_energy(payload_len: int,
                   sf: int = LORA_SF,
                   v_supply: float = V_SUPPLY,
                   i_tx: float = I_TX,
                   e_rx: float = E_RX_WINDOWS) -> float:
    """
    Calculate the total electrical energy consumed per uplink message (Joules).
    
    Formula:
      E_msg = V_supply * I_tx * ToA + E_rx_windows
    
    For 25-byte payload at SF7:
      ToA ≈ 82.18 ms
      E_tx = 3.3 V * 44 mA * 82.18 ms ≈ 11.93 mJ
      E_rx = 1.50 mJ
      E_msg ≈ 13.43 mJ
    """
    toa = lora_airtime(payload_len, sf=sf)
    return (v_supply * i_tx * toa) + e_rx


def daily_energy(reads: int,
                 messages: int,
                 has_logic: bool = False,
                 e_msg: float = None,
                 days: int = DAYS) -> float:
    """
    Calculate the average energy consumption per day in Joules (TRD Section 6).
    
    Energy/day = [ reads * (E_SAMPLE + (E_LOGIC if has_logic else 0))
                   + messages * E_msg
                   + N * V_SUPPLY * I_SLEEP ] / DAYS
    """
    if e_msg is None:
        e_msg = message_energy(25)
    e_read = E_SAMPLE + (E_LOGIC if has_logic else 0.0)
    total_sleep_energy = N * V_SUPPLY * I_SLEEP
    total_joules = (reads * e_read) + (messages * e_msg) + total_sleep_energy
    return total_joules / float(days)


# ==============================================================================
# MAIN ENTRY POINT (Milestone 1 self-test verification)
# ==============================================================================

if __name__ == '__main__':
    print("=== ASR Simulator (TechnoVision 2026-27) ===")
    print("Milestone 1 & 2 verification:")
    
    # Check CBOR vectors
    assert encode_cbor(100000.0).hex() == "fa47c35000", "CBOR float32 vector failed"
    assert encode_cbor("IETF").hex() == "6449455446", "CBOR string vector failed"
    assert encode_cbor([1, 2, 3]).hex() == "83010203", "CBOR list vector failed"
    assert encode_cbor({1: 2, 3: 4}).hex() == "a201020304", "CBOR map vector failed"
    assert encode_cbor(-1).hex() == "20", "CBOR negative int vector failed"
    print("[OK] All RFC 8949 CBOR test vectors passed.")
    
    # Check SenML CBOR payload length
    cbor_rec = build_senml_cbor(100000, 24.12)
    print(f"[OK] SenML-CBOR record length: {len(cbor_rec)} bytes (expected: 25 bytes)")
    assert len(cbor_rec) == 25, f"Expected 25 bytes, got {len(cbor_rec)}"
    
    # Check SenML JSON payload length
    json_rec = build_senml_json(100000, 24.12)
    print(f"[OK] SenML-JSON record length: {len(json_rec)} bytes (expected: ~50 bytes)")
    
    # Check LoRa airtime and energy
    toa = lora_airtime(25)
    print(f"[OK] LoRa ToA (38B at SF7): {toa * 1000.0:.2f} ms (expected: ~82 ms)")
    assert 81.5 <= toa * 1000.0 <= 82.5, "Airtime out of expected range"
    
    e_msg = message_energy(25)
    print(f"[OK] Message energy E_msg: {e_msg * 1000.0:.2f} mJ (expected: ~13.4 mJ)")
    assert 13.0 <= e_msg * 1000.0 <= 13.8, "Energy out of expected range"
    
    print("\nMilestone 1 & 2 complete! iot_asr_demo.py ready.")
