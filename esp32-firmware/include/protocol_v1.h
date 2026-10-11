#ifndef PROTOCOL_V1_H
#define PROTOCOL_V1_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/**
 * =====================================================================
 * Smart Rider HMI - Binary BLE Protocol V1 Specification Header
 * =====================================================================
 */

#define PROTOCOL_MAGIC_BYTE      0xA5
#define PROTOCOL_VERSION_1       0x01
#define PROTOCOL_MAX_PAYLOAD_LEN 14
#define PROTOCOL_HEADER_LEN      5
#define PROTOCOL_CHECKSUM_LEN    1
#define PROTOCOL_MAX_PACKET_LEN  (PROTOCOL_HEADER_LEN + PROTOCOL_MAX_PAYLOAD_LEN + PROTOCOL_CHECKSUM_LEN)

// --- GATT UUID Definitions ---
#define SERVICE_UUID_SMART_RIDER "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_UUID_COMMAND_TX     "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHAR_UUID_CONTROL_RX     "d9c05e32-8404-44df-90a4-3e9a01f4c78a"
#define CHAR_UUID_DEVICE_INFO    "e8a2a510-7521-4f76-a0bf-0e86b241416e"

// --- Protocol Opcodes: Remote -> Android (TX) ---
#define OPCODE_CMD_ANSWER_CALL       0x01
#define OPCODE_CMD_REJECT_END_CALL   0x02
#define OPCODE_CMD_PLAY_PAUSE        0x03
#define OPCODE_CMD_NEXT_TRACK        0x04
#define OPCODE_CMD_PREV_TRACK        0x05
#define OPCODE_CMD_OPEN_SAVED_NAV    0x06
#define OPCODE_CMD_ACTIVATE_VOICE    0x07
#define OPCODE_CMD_HEARTBEAT         0x10

// --- Protocol Opcodes: Android -> Remote (RX) ---
#define OPCODE_CMD_ACK               0x80
#define OPCODE_CMD_NACK              0x81
#define OPCODE_CMD_PHONE_STATE_SYNC  0x82
#define OPCODE_CMD_BUZZER_ALERT      0x83

// --- Status Codes for ACK/NACK ---
#define STATUS_OK                    0x00
#define STATUS_ERR_UNKNOWN_OPCODE    0x01
#define STATUS_ERR_CRC_MISMATCH      0x02
#define STATUS_ERR_DUPLICATE_IGNORED 0x03
#define STATUS_ERR_ACTION_FAILED     0x04

// --- Structured Packet Representation ---
typedef struct {
    uint8_t magic;
    uint8_t version;
    uint8_t seq_num;
    uint8_t opcode;
    uint8_t payload_len;
    uint8_t payload[PROTOCOL_MAX_PAYLOAD_LEN];
    uint8_t crc8;
} __attribute__((packed)) protocol_packet_t;

/**
 * Computes CRC-8-CCITT checksum over the given data buffer.
 * Polynomial: 0x07 (x^8 + x^2 + x^1 + 1), Init: 0x00
 */
static inline uint8_t protocol_crc8(const uint8_t *data, size_t length) {
    uint8_t crc = 0x00;
    for (size_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x80) {
                crc = (uint8_t)((crc << 1) ^ 0x07);
            } else {
                crc = (uint8_t)(crc << 1);
            }
        }
    }
    return crc;
}

/**
 * Serializes a packet into a byte buffer for BLE transmission.
 * Returns total serialized bytes written, or 0 on error.
 */
static inline size_t protocol_serialize(const protocol_packet_t *pkt, uint8_t *out_buffer, size_t max_out_len) {
    if (!pkt || !out_buffer || pkt->payload_len > PROTOCOL_MAX_PAYLOAD_LEN) {
        return 0;
    }
    size_t total_len = PROTOCOL_HEADER_LEN + pkt->payload_len + PROTOCOL_CHECKSUM_LEN;
    if (max_out_len < total_len) {
        return 0;
    }

    out_buffer[0] = PROTOCOL_MAGIC_BYTE;
    out_buffer[1] = PROTOCOL_VERSION_1;
    out_buffer[2] = pkt->seq_num;
    out_buffer[3] = pkt->opcode;
    out_buffer[4] = pkt->payload_len;

    for (uint8_t i = 0; i < pkt->payload_len; i++) {
        out_buffer[PROTOCOL_HEADER_LEN + i] = pkt->payload[i];
    }

    uint8_t computed_crc = protocol_crc8(out_buffer, PROTOCOL_HEADER_LEN + pkt->payload_len);
    out_buffer[PROTOCOL_HEADER_LEN + pkt->payload_len] = computed_crc;

    return total_len;
}

/**
 * Deserializes an incoming byte buffer into a packet struct.
 * Returns true if valid header, length, and CRC-8 match.
 */
static inline bool protocol_deserialize(const uint8_t *buffer, size_t length, protocol_packet_t *out_pkt) {
    if (!buffer || !out_pkt || length < (PROTOCOL_HEADER_LEN + PROTOCOL_CHECKSUM_LEN)) {
        return false;
    }
    if (buffer[0] != PROTOCOL_MAGIC_BYTE || buffer[1] != PROTOCOL_VERSION_1) {
        return false;
    }

    uint8_t payload_len = buffer[4];
    if (payload_len > PROTOCOL_MAX_PAYLOAD_LEN) {
        return false;
    }

    size_t expected_total_len = PROTOCOL_HEADER_LEN + payload_len + PROTOCOL_CHECKSUM_LEN;
    if (length != expected_total_len) {
        return false;
    }

    uint8_t expected_crc = buffer[PROTOCOL_HEADER_LEN + payload_len];
    uint8_t computed_crc = protocol_crc8(buffer, PROTOCOL_HEADER_LEN + payload_len);
    if (expected_crc != computed_crc) {
        return false;
    }

    out_pkt->magic = buffer[0];
    out_pkt->version = buffer[1];
    out_pkt->seq_num = buffer[2];
    out_pkt->opcode = buffer[3];
    out_pkt->payload_len = payload_len;
    for (uint8_t i = 0; i < payload_len; i++) {
        out_pkt->payload[i] = buffer[PROTOCOL_HEADER_LEN + i];
    }
    out_pkt->crc8 = expected_crc;

    return true;
}

#endif // PROTOCOL_V1_H
