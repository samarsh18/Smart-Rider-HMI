# Hardware & Protocol Simulation Guide — Smart Rider HMI

This directory provides simulation tools for testing the Smart Rider HMI physical remote and protocol without needing physical hardware.

---

## 1. Python BLE Protocol Simulator (`protocol_simulator.py`)

A standalone, lightweight Python tool to generate and verify Protocol V1 binary frames.

### Usage:
Run the interactive CLI:
```bash
python simulator/protocol_simulator.py
```

### Interactive Commands:
- `1`: Simulate Short Press `ANSWER_CALL`
- `2`: Simulate Short Press `REJECT_END_CALL`
- `3`: Simulate Short Press `PLAY_PAUSE`
- `4`: Simulate Short Press `NEXT_TRACK`
- `5`: Simulate Short Press `PREV_TRACK`
- `6`: Simulate Short Press `QUICK_NAVIGATION`
- `7`: Simulate Long Press (~1.2s) `VOICE_ASSISTANT`
- `h`: Simulate 30s Heartbeat with battery telemetry
- `q`: Quit

Each command prints:
- Exact raw binary byte stream (in Hex)
- Verified packet length
- Opcode, sequence number, and validated CRC-8-CCITT checksum

---

## 2. Wokwi ESP32 Hardware Simulator (`wokwi_diagram.json`)

[Wokwi](https://wokwi.com) provides cycle-accurate ESP32 simulation in the browser or directly inside VS Code via the Wokwi extension.

### Hardware Layout:
- **MCU**: ESP32-DevKitC-V4 (ESP32-WROOM-32)
- **Buttons (Active-Low to GND)**:
  - `btn1` (Green): `GPIO 18` — `ANSWER_CALL`
  - `btn2` (Red): `GPIO 19` — `REJECT_END_CALL`
  - `btn3` (Yellow): `GPIO 21` — `PLAY_PAUSE`
  - `btn4` (Blue): `GPIO 22` — `NEXT_TRACK`
  - `btn5` (Cyan): `GPIO 23` — `PREV_TRACK`
  - `btn6` (Orange): `GPIO 25` — `QUICK_NAV`
  - `btn7` (Purple): `GPIO 26` — `VOICE_ASSISTANT` (Hold 1.2s)
- **Feedback**:
  - `led_blue`: `GPIO 32` via 220Ω resistor (BLE State)
  - `led_green`: `GPIO 33` via 220Ω resistor (Action indicator)
  - `bz1`: `GPIO 27` (Acoustic piezo feedback)

### How to Run:
1. Open [wokwi.com/projects/new/esp32](https://wokwi.com/projects/new/esp32).
2. Replace `diagram.json` with the contents of `simulator/wokwi_diagram.json`.
3. Paste `esp32-firmware/src/main.cpp` into `sketch.ino` (or `main.cpp`).
4. Click **Start Simulation**.
