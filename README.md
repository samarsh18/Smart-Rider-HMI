# Smart Rider HMI

> **ESP32-Based Physical Remote & Android Companion for Two-Wheeler Riders**

Smart Rider HMI is an automotive-grade Human-Machine Interface designed to make motorcycle and scooter riding safer. It provides a tactile 7-button handlebar remote and an Android companion service, allowing riders to control phone calls, music, turn-by-turn navigation, and a voice assistant using physical buttons and acoustic feedback—without looking at or touching their smartphone.

---

## Key Features

- **7 Tactile Handlebar Controls**: Glove-friendly, high-contrast controls for calls, media, voice assistant, and navigation.
- **Hands-Free Telephony**: Answer or reject phone calls via physical buttons or voice commands with spoken caller ID announcements.
- **Media Controls**: Universal play/pause, next track, and previous track controls compatible with Spotify, YouTube Music, and other media players.
- **One-Touch Navigation**: Instant turn-by-turn navigation to a saved default destination (Home/Work) via Google Maps.
- **Route Weather Alerts**: Proactive spoken alerts for rain and severe weather along the route using the free, open-source Open-Meteo API (no API keys required).
- **Zero In-Ride Distraction**: Remote carries no microphone hardware; audio capture and playback route through the rider's existing helmet Bluetooth headset (Cardo, Sena, earbuds) or phone speaker.

---

## The Seven V1 Physical Controls

| # | Button | Gesture | Primary Function |
| :- | :--- | :--- | :--- |
| **1** | `ANSWER_CALL` | Short Press | Accept incoming phone call |
| **2** | `REJECT_END_CALL` | Short Press | Reject ringing call / terminate active call |
| **3** | `PLAY_PAUSE` | Short Press | Toggle media playback (Play/Pause) |
| **4** | `NEXT_TRACK` | Short Press | Skip to next track |
| **5** | `PREV_TRACK` | Short Press | Restart / skip to previous track |
| **6** | `QUICK_NAVIGATION`| Short Press | Launch navigation to saved destination |
| **7** | `VOICE_ASSISTANT` | Long Press (~1.2s)| Activate voice assistant |

---

## System Architecture

```
+-------------------------------------------------------------------------+
|                          TWO-WHEELER COCKPIT                            |
|                                                                         |
|  [ Handlebar Remote ]                        [ Rider Helmet / Audio ]   |
|   - 7 Tactile Buttons                         - Bluetooth Intercom      |
|   - Status LED / Buzzer                         (Cardo, Sena, Buds)     |
|   - ESP32-WROOM-32 (BLE Server)                         ^               |
+---------------------------------------------------------|---------------+
                         |                                |
             BLE 4.2 / 5.0 (Custom GATT)             A2DP / HFP
                         |                           Audio Route
                         v                                |
+---------------------------------------------------------v---------------+
|                   SMARTPHONE (Pocket / Mount)                           |
|                                                                         |
|  [ Android Companion App & Foreground Service ]                         |
|   - BLE GATT Client & Packet Parser                                     |
|   - MediaSession Controller (Play / Pause / Skip)                       |
|   - Telecom Call Handler & Spoken Caller ID                             |
|   - SpeechRecognizer Voice Assistant & Text-To-Speech (TTS)             |
|   - Quick Navigation Launcher (Google Maps Intent)                      |
|   - Route Weather Monitor (Open-Meteo Free API)                         |
+---------------------------------------------------------+---------------+
```

---

## Repository Structure

```
Smart-Rider-HMI/
├── android-app/             # Android Kotlin / Jetpack Compose companion app
│   └── README.md            # Android architecture & package plan
├── esp32-firmware/          # ESP32-WROOM-32 Arduino / C++ firmware
│   ├── include/
│   │   ├── pin_config.h     # GPIO pin mappings & timing constants
│   │   └── protocol_v1.h    # Binary packet structs, opcodes, CRC-8
│   ├── src/
│   │   └── main.cpp         # Firmware entry point & hardware self-test
│   └── platformio.ini       # PlatformIO build configuration
├── simulator/               # Protocol & hardware simulation tools
│   ├── protocol_simulator.py# Interactive Python Protocol V1 CLI & packet generator
│   ├── wokwi_diagram.json   # Wokwi ESP32 7-button breadboard diagram
│   └── README.md            # Simulation usage guide
├── docs/                    # Complete technical documentation
│   ├── architecture.md      # Detailed system architecture & non-goals
│   ├── button_specification.md # Electrical specs, state machine & feedback
│   ├── ble_protocol.md      # BLE GATT profile, binary framing & ACK flow
│   ├── android_permissions.md  # Deep permission audit & Play Store compliance
│   └── development_roadmap.md  # Milestones M1-M6 & simulation matrix
├── tests/                   # Automated test suite
│   └── test_protocol.py     # Unit tests for protocol framing and CRC-8
├── README.md                # Project documentation overview
└── .gitignore               # Multi-platform gitignore
```

---

## Getting Started & Validation

### 1. Run Protocol Unit Tests
Verify packet encoding, decoding, CRC-8 integrity, and sequence rollover:
```bash
python -m unittest discover tests
```

### 2. Run Interactive Protocol Simulator
Simulate physical button presses and view generated binary frames:
```bash
python simulator/protocol_simulator.py
```

### 3. ESP32 Simulation via Wokwi
Open `simulator/wokwi_diagram.json` in [Wokwi](https://wokwi.com) with `esp32-firmware/src/main.cpp` for virtual hardware testing.

---

## Documentation Index

- [System Architecture](docs/architecture.md)
- [Physical Button Specification](docs/button_specification.md)
- [BLE Protocol Specification](docs/ble_protocol.md)
- [Android Permissions & API Audit](docs/android_permissions.md)
- [Development Roadmap](docs/development_roadmap.md)

---

## License

This project is licensed under the Apache 2.0 License.
