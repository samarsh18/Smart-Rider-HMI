#!/usr/bin/env python3
"""
Smart Rider HMI - BLE Protocol V1 Python Simulator & Verification Tool
======================================================================
Implements binary packet encoding, decoding, CRC-8-CCITT calculation,
sequence tracking, and an interactive mock remote simulator.
"""

import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

MAGIC_BYTE = 0xA5
PROTOCOL_VERSION = 0x01
MAX_PAYLOAD_LEN = 14
HEADER_LEN = 5
CHECKSUM_LEN = 1

# Opcodes (Remote -> Android)
OPCODE_CMD_ANSWER_CALL      = 0x01
OPCODE_CMD_REJECT_END_CALL  = 0x02
OPCODE_CMD_PLAY_PAUSE       = 0x03
OPCODE_CMD_NEXT_TRACK       = 0x04
OPCODE_CMD_PREV_TRACK       = 0x05
OPCODE_CMD_OPEN_SAVED_NAV   = 0x06
OPCODE_CMD_ACTIVATE_VOICE   = 0x07
OPCODE_CMD_HEARTBEAT        = 0x10

# Opcodes (Android -> Remote)
OPCODE_CMD_ACK              = 0x80
OPCODE_CMD_NACK             = 0x81
OPCODE_CMD_PHONE_STATE_SYNC = 0x82
OPCODE_CMD_BUZZER_ALERT     = 0x83

OPCODE_NAMES = {
    OPCODE_CMD_ANSWER_CALL: "CMD_ANSWER_CALL",
    OPCODE_CMD_REJECT_END_CALL: "CMD_REJECT_END_CALL",
    OPCODE_CMD_PLAY_PAUSE: "CMD_PLAY_PAUSE",
    OPCODE_CMD_NEXT_TRACK: "CMD_NEXT_TRACK",
    OPCODE_CMD_PREV_TRACK: "CMD_PREV_TRACK",
    OPCODE_CMD_OPEN_SAVED_NAV: "CMD_OPEN_SAVED_NAV",
    OPCODE_CMD_ACTIVATE_VOICE: "CMD_ACTIVATE_VOICE",
    OPCODE_CMD_HEARTBEAT: "CMD_HEARTBEAT",
    OPCODE_CMD_ACK: "CMD_ACK",
    OPCODE_CMD_NACK: "CMD_NACK",
    OPCODE_CMD_PHONE_STATE_SYNC: "CMD_PHONE_STATE_SYNC",
    OPCODE_CMD_BUZZER_ALERT: "CMD_BUZZER_ALERT",
}

STATUS_OK                    = 0x00
STATUS_ERR_UNKNOWN_OPCODE    = 0x01
STATUS_ERR_CRC_MISMATCH      = 0x02
STATUS_ERR_DUPLICATE_IGNORED = 0x03
STATUS_ERR_ACTION_FAILED     = 0x04


def compute_crc8_ccitt(data: bytes) -> int:
    """Computes CRC-8-CCITT with polynomial 0x07 and initial value 0x00."""
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


@dataclass
class ProtocolPacket:
    magic: int
    version: int
    seq_num: int
    opcode: int
    payload_len: int
    payload: bytes
    crc8: int

    @property
    def opcode_name(self) -> str:
        return OPCODE_NAMES.get(self.opcode, f"UNKNOWN_0x{self.opcode:02X}")

    def to_hex(self) -> str:
        encoded = encode_packet(self.opcode, self.seq_num, self.payload)
        return " ".join(f"{b:02X}" for b in encoded)


def encode_packet(opcode: int, seq_num: int, payload: bytes = b"") -> bytes:
    """Encodes command fields into a validated Protocol V1 binary byte frame."""
    if len(payload) > MAX_PAYLOAD_LEN:
        raise ValueError(f"Payload length ({len(payload)}) exceeds maximum {MAX_PAYLOAD_LEN} bytes")

    header_and_payload = bytes([
        MAGIC_BYTE,
        PROTOCOL_VERSION,
        seq_num & 0xFF,
        opcode & 0xFF,
        len(payload),
    ]) + payload

    crc = compute_crc8_ccitt(header_and_payload)
    return header_and_payload + bytes([crc])


def decode_packet(data: bytes) -> ProtocolPacket:
    """Decodes and validates a raw byte frame according to Protocol V1."""
    if len(data) < HEADER_LEN + CHECKSUM_LEN:
        raise ValueError(f"Packet too short: {len(data)} bytes (minimum {HEADER_LEN + CHECKSUM_LEN})")

    magic = data[0]
    if magic != MAGIC_BYTE:
        raise ValueError(f"Invalid magic header byte: 0x{magic:02X} (expected 0x{MAGIC_BYTE:02X})")

    version = data[1]
    if version != PROTOCOL_VERSION:
        raise ValueError(f"Unsupported protocol version: 0x{version:02X} (expected 0x{PROTOCOL_VERSION:02X})")

    seq_num = data[2]
    opcode = data[3]
    payload_len = data[4]

    expected_total_len = HEADER_LEN + payload_len + CHECKSUM_LEN
    if len(data) != expected_total_len:
        raise ValueError(f"Length mismatch: packet has {len(data)} bytes, header declared {expected_total_len}")

    payload = data[HEADER_LEN:HEADER_LEN + payload_len]
    expected_crc = data[HEADER_LEN + payload_len]

    computed_crc = compute_crc8_ccitt(data[:HEADER_LEN + payload_len])
    if computed_crc != expected_crc:
        raise ValueError(f"CRC8 mismatch: received 0x{expected_crc:02X}, computed 0x{computed_crc:02X}")

    return ProtocolPacket(
        magic=magic,
        version=version,
        seq_num=seq_num,
        opcode=opcode,
        payload_len=payload_len,
        payload=payload,
        crc8=expected_crc,
    )


class RemoteSimulator:
    """Simulates an ESP32 handlebar remote transmitting button presses."""

    def __init__(self):
        self._seq = 0

    def next_seq(self) -> int:
        seq = self._seq
        self._seq = (self._seq + 1) & 0xFF
        return seq

    def press_answer_call(self) -> bytes:
        return encode_packet(OPCODE_CMD_ANSWER_CALL, self.next_seq())

    def press_reject_call(self) -> bytes:
        return encode_packet(OPCODE_CMD_REJECT_END_CALL, self.next_seq())

    def press_play_pause(self) -> bytes:
        return encode_packet(OPCODE_CMD_PLAY_PAUSE, self.next_seq())

    def press_next_track(self) -> bytes:
        return encode_packet(OPCODE_CMD_NEXT_TRACK, self.next_seq())

    def press_prev_track(self) -> bytes:
        return encode_packet(OPCODE_CMD_PREV_TRACK, self.next_seq())

    def press_quick_nav(self) -> bytes:
        return encode_packet(OPCODE_CMD_OPEN_SAVED_NAV, self.next_seq())

    def hold_voice_assistant(self) -> bytes:
        return encode_packet(OPCODE_CMD_ACTIVATE_VOICE, self.next_seq(), payload=bytes([0x01]))

    def send_heartbeat(self, battery_pct: int = 85) -> bytes:
        return encode_packet(OPCODE_CMD_HEARTBEAT, self.next_seq(), payload=bytes([battery_pct]))


def interactive_cli():
    print("=" * 60)
    print("  Smart Rider HMI - BLE Protocol V1 Interactive Simulator")
    print("=" * 60)
    print("Commands:")
    print("  1 - Short Press: ANSWER_CALL")
    print("  2 - Short Press: REJECT_END_CALL")
    print("  3 - Short Press: PLAY_PAUSE")
    print("  4 - Short Press: NEXT_TRACK")
    print("  5 - Short Press: PREV_TRACK")
    print("  6 - Short Press: QUICK_NAVIGATION")
    print("  7 - Long Press:  VOICE_ASSISTANT (1.2s)")
    print("  h - Heartbeat (Battery 90%)")
    print("  q - Quit")
    print("=" * 60)

    sim = RemoteSimulator()

    while True:
        try:
            choice = input("\nSelect button action > ").strip()
            if choice == "q":
                break
            packet_bytes = None
            if choice == "1":
                packet_bytes = sim.press_answer_call()
            elif choice == "2":
                packet_bytes = sim.press_reject_call()
            elif choice == "3":
                packet_bytes = sim.press_play_pause()
            elif choice == "4":
                packet_bytes = sim.press_next_track()
            elif choice == "5":
                packet_bytes = sim.press_prev_track()
            elif choice == "6":
                packet_bytes = sim.press_quick_nav()
            elif choice == "7":
                packet_bytes = sim.hold_voice_assistant()
            elif choice == "h":
                packet_bytes = sim.send_heartbeat()
            else:
                print("Unknown command.")
                continue

            hex_str = " ".join(f"{b:02X}" for b in packet_bytes)
            decoded = decode_packet(packet_bytes)
            print(f"[TX Packet] Bytes ({len(packet_bytes)}B): {hex_str}")
            print(f"            Parsed: Opcode={decoded.opcode_name} (0x{decoded.opcode:02X}), "
                  f"Seq={decoded.seq_num}, PayloadLen={decoded.payload_len}, CRC8=0x{decoded.crc8:02X}")

        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    interactive_cli()
