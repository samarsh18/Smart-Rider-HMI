# Android Companion Application — Smart Rider HMI

## 1. Overview

The `android-app` module is the smartphone integration layer for the **Smart Rider HMI** system. It connects to the ESP32 handlebar remote over Bluetooth Low Energy (BLE), intercepts the rider's physical button events and voice commands, and translates them into Android system actions (telephony, media, voice recognition, navigation, and weather alerts).

## 2. Target Specifications & Technologies

- **IDE**: Android Studio Hedgehog / Iguana / Ladybug
- **Language**: Kotlin 1.9+ / 2.0
- **UI Framework**: Jetpack Compose with Material 3
- **Min SDK**: API 26 (Android 8.0 Oreo — required for `TelecomManager.acceptRingingCall`)
- **Target / Compile SDK**: API 34 (Android 14) / API 35 (Android 15)
- **Architecture**: MVI / MVVM with Kotlin Coroutines & StateFlow
- **Background Engine**: Android Sticky Foreground Service (`SmartRiderService`)

---

## 3. Package & Module Architecture

```
android-app/
├── app/
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml
│           ├── java/com/smartrider/hmi/
│           │   ├── ble/
│           │   │   ├── BleScanner.kt             # Remote discovery and RSSI filtering
│           │   │   ├── BleConnectionManager.kt   # GATT connection, bonding & auto-reconnect
│           │   │   ├── ProtocolParser.kt         # Protocol V1 binary packet parser & CRC8
│           │   │   └── PacketSerializer.kt       # Outgoing ACK & state sync serializer
│           │   ├── service/
│           │   │   ├── SmartRiderService.kt      # Persistent Foreground Service
│           │   │   └── MediaNotificationListener.kt # NotificationListenerService for MediaSessions
│           │   ├── telephony/
│           │   │   ├── CallManager.kt            # TelecomManager accept/end call logic
│           │   │   ├── CallerResolver.kt         # ContactsContract caller ID lookup
│           │   │   └── TtsManager.kt             # Spoken caller announcements & alerts
│           │   ├── media/
│           │   │   └── MediaPlaybackController.kt# Active MediaSession transport controls
│           │   ├── voice/
│           │   │   ├── VoiceAssistantManager.kt  # SpeechRecognizer lifecycle & audio ducking
│           │   │   └── RideIntentParser.kt       # Natural language command parser
│           │   ├── navigation/
│           │   │   ├── NavigationLauncher.kt     # Google Maps navigation intent launcher
│           │   │   └── DestinationStorage.kt     # Jetpack DataStore for saved destination
│           │   ├── weather/
│           │   │   ├── OpenMeteoClient.kt        # Free Open-Meteo REST API client (no keys)
│           │   │   └── RainAlertEngine.kt        # Advance route precipitation detector
│           │   └── ui/
│           │       ├── MainActivity.kt           # Jetpack Compose entry point
│           │       ├── onboarding/               # Phased permission & pairing wizard
│           │       ├── dashboard/                # Connected status & button test monitor
│           │       └── settings/                 # Saved destination & alert preferences
│           └── res/
└── README.md
```

---

## 4. Permission Requirements Summary

| Permission | Purpose | Manifest Declaration |
| :--- | :--- | :--- |
| `BLUETOOTH_SCAN` | Discover remote (API 31+) | `usesPermissionFlags="neverForLocation"` |
| `BLUETOOTH_CONNECT` | Connect to GATT server | Required on API 31+ |
| `FOREGROUND_SERVICE` | Persistent connection | `foregroundServiceType="connectedDevice\|microphone"` |
| `ANSWER_PHONE_CALLS` | Accept/end calls | Dangerous runtime |
| `READ_PHONE_STATE` | Call state listener | Dangerous runtime |
| `READ_CALL_LOG` | Caller number | Dangerous runtime (API 28+) |
| `READ_CONTACTS` | Spoken caller name | Dangerous runtime |
| `RECORD_AUDIO` | Speech recognition | Dangerous runtime |
| `BIND_NOTIFICATION_LISTENER_SERVICE` | Control music | Special App Access in System Settings |

*(For full analysis, refer to [docs/android_permissions.md](../docs/android_permissions.md)).*

---

## 5. Development Milestones

- **M3**: Implementation of `ble/` and `service/SmartRiderService.kt` with Protocol V1 integration.
- **M4**: Implementation of `telephony/` and `media/` subsystems.
- **M5**: Implementation of `voice/`, `navigation/`, and `weather/` subsystems.
