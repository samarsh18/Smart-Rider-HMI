# System Architecture — Smart Rider HMI

## 1. Project Overview & Objective

**Smart Rider HMI** is a two-wheeler Human-Machine Interface system consisting of an ESP32-based handlebar-mounted physical remote and a companion Android application. The objective is to provide motorcycle and scooter riders with seamless, tactile control over essential smartphone functions (telephony, music, navigation, and voice assistance) without requiring them to glance at, unlock, or physically handle their smartphone while riding.

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
+-------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles & Boundaries

1. **Safety First (Zero Visual Distraction)**:
   All primary interactions are designed for tactile muscle memory and acoustic confirmation. The rider's eyes remain on the road and hands on the handlebars.
2. **Stateless Remote Hardware**:
   The ESP32 firmware manages physical inputs, debouncing, button timing, BLE connectivity, and local LED/buzzer feedback. It stores no navigation data, coordinates, or media state.
3. **Smartphone as the Intelligence Engine**:
   The Android application handles all telephony state machines, media sessions, speech-to-text, text-to-speech, internet connectivity, and navigation intents.
4. **No Microphone Hardware on the Remote (V1)**:
   In V1, the ESP32 remote does not contain a microphone. Capturing audio at the handlebar introduces severe wind and engine noise. Audio capture (mic) and playback (speaker/TTS) are handled entirely through the smartphone's existing audio pipeline, routing natively to the rider's helmet Bluetooth headset (Cardo, Sena, AirPods, etc.) or phone speaker.
5. **Strict Non-Goals**:
   - No computer-vision, camera feeds, or image processing.
   - No lane detection or vehicle tracking.
   - No collision prediction or traffic-risk scoring.
   - No paid third-party APIs or proprietary API key dependencies.

---

## 3. High-Level Component Architecture

### 3.1 System Flow Diagram

```mermaid
flowchart TD
    subgraph ESP32 ["ESP32 Physical Remote (Handlebar)"]
        SW[7 Tactile Pushbuttons] --> DB[Debounce & Long-Press Engine]
        DB --> CM[Command Dispatcher]
        CM --> BLE_TX[BLE GATT Server (TX Notify)]
        BLE_RX[BLE GATT Server (RX Write)] --> FB[Feedback Controller (Buzzer / LED)]
        PWR[Power Mgmt & Deep Sleep] --> DB
    end

    subgraph Transport ["Bluetooth Low Energy (BLE 4.2 / 5.0)"]
        BLE_TX -.->|Binary Packet V1| AND_RX[BLE GATT Client Callback]
        AND_TX[BLE GATT Client Write] -.->|ACK / State Payload| BLE_RX
    end

    subgraph AndroidApp ["Android Companion Application"]
        AND_RX --> FS[Foreground Service: SmartRiderService]
        FS --> PR[Protocol Deserializer & Deduplicator]
        PR --> ROUTER[Command Dispatcher Router]

        ROUTER -->|ANSWER_CALL / REJECT| TEL[Call Management & Telecom Engine]
        ROUTER -->|PLAY_PAUSE / NEXT / PREV| MED[MediaSession Controller]
        ROUTER -->|QUICK_NAVIGATION| NAV[Navigation Launcher]
        ROUTER -->|ACTIVATE_VOICE| VOC[Voice Assistant & SpeechRecognizer]

        TEL --> TTS[Text-To-Speech Engine]
        VOC --> TTS
        WTH[Weather Client: Open-Meteo] --> TTS
        
        TEL -.->|Call State Changes| AND_TX
        VOC -.->|Voice State Changes| AND_TX
    end

    subgraph AudioDevice ["Audio I/O (Helmet Intercom / Earbuds)"]
        TTS -->|Spoken Announcements| SPK[Helmet Speakers]
        MIC[Helmet Mic] -->|Voice Commands| VOC
    end
```

---

## 4. Subsystem Breakdown

### 4.1 ESP32 Handlebar Remote Subsystem
- **Microcontroller**: ESP32-WROOM-32 (dual-core Xtensa 32-bit LX6, 240MHz, integrated BLE 4.2 BR/EDR).
- **Physical Inputs**: 7 SPST momentary pushbuttons wired to GPIOs configured as `INPUT_PULLUP`.
- **Debounce & Timing Engine**:
  - 40ms software debounce filtering mechanical contact bounce.
  - Finite state machine tracking `IDLE` -> `DEBOUNCING` -> `PRESSED` -> `LONG_PRESS_DETECTED` -> `RELEASED`.
  - Short press recognized on release (duration < 1000ms).
  - Long press recognized proactively at $t = 1200\text{ ms}$ with immediate tactile/acoustic feedback.
- **Feedback Module**:
  - 1x Active Piezo Buzzer (audible clicks, long-press tone, disconnect chirp).
  - 1x Dual-color LED (Blue for BLE connection states, Green/Amber for command activity).
- **Power Management**:
  - 1S LiPo / 18650 cell with TP4056 charge controller.
  - Auto-sleep after 10 minutes of BLE disconnection or inactivity.
  - GPIO wake-up from deep sleep on any button press via `esp_sleep_enable_ext1_wakeup`.

### 4.2 Android Companion Subsystem
- **Architecture Pattern**: Modern Android Architecture with Jetpack Compose (UI), Kotlin Coroutines & Flow (asynchronous streams), and a sticky Android Foreground Service (`SmartRiderService`).
- **Foreground Service**:
  - Declared with `foregroundServiceType="connectedDevice|microphone"`.
  - Maintains persistent system notification ensuring Android does not kill the BLE listener during background operation.
- **BLE Communications Layer**:
  - Scanning via `BluetoothLeScanner` with specific `ScanFilter` for the Smart Rider Service UUID.
  - Automatic reconnection logic with exponential backoff on link loss.
  - Binary packet decoding, sequence counter validation, and duplicate rejection.
- **Telephony & Call Controller**:
  - Listens to incoming call events using `TelephonyCallback` / `PhoneStateListener`.
  - Resolves incoming caller contact name via `ContactsContract`.
  - Speaks caller name via `TextToSpeech` ("Incoming call from Rahul").
  - Answers call via `TelecomManager.acceptRingingCall()` (API 26+) or rejects call via `TelecomManager.endCall()` (API 28+).
- **Media Controller Layer**:
  - Binds to active system media sessions using `MediaSessionManager` (Spotify, YouTube Music, Apple Music, Audible).
  - Dispatches `play()`, `pause()`, `skipToNext()`, `skipToPrevious()` directly to the active media session.
- **Voice Assistant Layer**:
  - Invokes `SpeechRecognizer` in response to the `ACTIVATE_VOICE` command.
  - Provides audio prompt (beep) and listens for rider speech commands (e.g., *"Weather ahead"*, *"Navigate to office"*, *"Next track"*, *"Call home"*).
  - Voice pipeline pauses media session during speech recognition (audio ducking).
- **Navigation Controller**:
  - Stores a user-configured default destination (e.g., Home or Work) in encrypted DataStore.
  - Dispatches `ACTION_VIEW` intent with `google.navigation:q=lat,lng&mode=d` to open turn-by-turn navigation in Google Maps instantly.
- **Weather & Environmental Alerts**:
  - Queries the free, open-source Open-Meteo Weather API (`https://api.open-meteo.com/v1/forecast`) based on current GPS location.
  - Checks for upcoming precipitation, wind gusts, and storms along the route.
  - Generates spoken audio alerts (e.g., *"Rain expected in 15 minutes along your route"*).

---

## 5. Security & Safety Architecture

1. **BLE Pairing & Whitelisting**:
   The ESP32 uses BLE Security Manager (SM) bonding with encrypted communication. Once bonded with the rider's phone, the ESP32 whitelists the phone address to prevent rogue connections from nearby vehicles.
2. **Crash & Disconnect Resilience**:
   If BLE link drops (e.g., distance or RF interference), the ESP32 emits a distinct 3-beep acoustic warning to alert the rider, and enters fast-reconnect advertising mode.
3. **Zero In-Ride Configuration**:
   All setup (pairing, button test, setting default destination) is performed while stationary via the Android Compose onboarding UI. While riding, the phone remains tucked away.

---

## 6. Software Bill of Materials (SBOM) & Dependencies

| Layer | Component | Version / Tool | Purpose |
| :--- | :--- | :--- | :--- |
| **Embedded** | ESP32-WROOM-32 | ESP-IDF / Arduino core | Remote Controller Firmware |
| **Embedded** | NimBLE-Arduino or ESP32 BLE | v1.4+ / Built-in | Memory-efficient BLE GATT Server |
| **Android** | Kotlin | 1.9+ | Primary language |
| **Android** | Jetpack Compose | BOM 2024.x | Modern UI framework for onboarding |
| **Android** | AndroidX Core & Lifecycle | Latest Stable | Foreground service lifecycle |
| **Android** | Android Telecom / Media | Android SDK API 26-34 | Call and Media control |
| **Android** | Google Play Services / Location | 21.0+ | GPS coordinates for weather queries |
| **Web API** | Open-Meteo API | REST v1 | Free weather forecast & rain alerts (No API key) |
