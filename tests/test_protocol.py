"""
Unit Tests for Smart Rider HMI - BLE Protocol V1
================================================
Verifies packet framing, CRC-8 integrity, boundary conditions,
and encoding/decoding for all physical button commands.
"""

import os
import sys
import unittest

# Add project root to sys.path so simulator can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator.protocol_simulator import (
    MAGIC_BYTE,
    PROTOCOL_VERSION,
    OPCODE_CMD_ANSWER_CALL,
    OPCODE_CMD_REJECT_END_CALL,
    OPCODE_CMD_PLAY_PAUSE,
    OPCODE_CMD_NEXT_TRACK,
    OPCODE_CMD_PREV_TRACK,
    OPCODE_CMD_OPEN_SAVED_NAV,
    OPCODE_CMD_ACTIVATE_VOICE,
    OPCODE_CMD_HEARTBEAT,
    OPCODE_CMD_ACK,
    compute_crc8_ccitt,
    encode_packet,
    decode_packet,
    RemoteSimulator,
)


class TestProtocolV1(unittest.TestCase):

    def test_crc8_known_vectors(self):
        """Test CRC-8-CCITT implementation consistency."""
        # Known test vectors for CRC-8-CCITT (poly 0x07, init 0x00)
        self.assertEqual(compute_crc8_ccitt(b""), 0x00)
        self.assertEqual(compute_crc8_ccitt(b"\x00"), 0x00)
        crc1 = compute_crc8_ccitt(b"\xA5\x01\x00\x01\x00")
        self.assertIsInstance(crc1, int)
        self.assertTrue(0 <= crc1 <= 255)

    def test_all_seven_v1_button_commands(self):
        """Ensure all 7 V1 controls encode and decode symmetrically."""
        opcodes = [
            (OPCODE_CMD_ANSWER_CALL, b""),
            (OPCODE_CMD_REJECT_END_CALL, b""),
            (OPCODE_CMD_PLAY_PAUSE, b""),
            (OPCODE_CMD_NEXT_TRACK, b""),
            (OPCODE_CMD_PREV_TRACK, b""),
            (OPCODE_CMD_OPEN_SAVED_NAV, b""),
            (OPCODE_CMD_ACTIVATE_VOICE, bytes([0x01])),  # 1.2s Long Press trigger
        ]

        for seq, (opcode, payload) in enumerate(opcodes):
            encoded = encode_packet(opcode=opcode, seq_num=seq, payload=payload)
            self.assertEqual(encoded[0], MAGIC_BYTE)
            self.assertEqual(encoded[1], PROTOCOL_VERSION)
            self.assertEqual(encoded[2], seq)
            self.assertEqual(encoded[3], opcode)
            self.assertEqual(encoded[4], len(payload))
            self.assertEqual(len(encoded), 5 + len(payload) + 1)

            decoded = decode_packet(encoded)
            self.assertEqual(decoded.opcode, opcode)
            self.assertEqual(decoded.seq_num, seq)
            self.assertEqual(decoded.payload, payload)
            self.assertEqual(decoded.magic, MAGIC_BYTE)
            self.assertEqual(decoded.version, PROTOCOL_VERSION)

    def test_corrupted_crc_rejection(self):
        """Ensure bit corruption triggers CRC-8 rejection."""
        valid_packet = encode_packet(OPCODE_CMD_PLAY_PAUSE, seq_num=42)
        # Corrupt one payload/header byte
        corrupted = bytearray(valid_packet)
        corrupted[3] ^= 0xFF

        with self.assertRaises(ValueError) as ctx:
            decode_packet(bytes(corrupted))
        self.assertIn("CRC8 mismatch", str(ctx.exception))

    def test_invalid_magic_header(self):
        """Ensure packets with bad magic byte are rejected immediately."""
        packet = encode_packet(OPCODE_CMD_PLAY_PAUSE, seq_num=10)
        corrupted = bytearray(packet)
        corrupted[0] = 0x5A  # Bad magic

        with self.assertRaises(ValueError) as ctx:
            decode_packet(bytes(corrupted))
        self.assertIn("Invalid magic header", str(ctx.exception))

    def test_unsupported_version(self):
        """Ensure packets with incompatible protocol version are rejected."""
        packet = bytearray(encode_packet(OPCODE_CMD_PLAY_PAUSE, seq_num=10))
        packet[1] = 0x99  # Unsupported version
        # Recompute CRC to bypass CRC check and reach version check
        packet[-1] = compute_crc8_ccitt(packet[:-1])

        with self.assertRaises(ValueError) as ctx:
            decode_packet(bytes(packet))
        self.assertIn("Unsupported protocol version", str(ctx.exception))

    def test_payload_overflow_prevention(self):
        """Ensure payloads exceeding 14 bytes are rejected by encoder."""
        overflow_payload = bytes([0xAA] * 15)
        with self.assertRaises(ValueError) as ctx:
            encode_packet(OPCODE_CMD_HEARTBEAT, seq_num=1, payload=overflow_payload)
        self.assertIn("exceeds maximum 14 bytes", str(ctx.exception))

    def test_remote_simulator_sequence_and_rollover(self):
        """Verify simulator sequence counter wraps cleanly at 256."""
        sim = RemoteSimulator()
        sim._seq = 255
        p1 = sim.press_play_pause()
        self.assertEqual(p1[2], 255)
        p2 = sim.press_play_pause()
        self.assertEqual(p2[2], 0)  # Wrapped around


if __name__ == "__main__":
    unittest.main()
