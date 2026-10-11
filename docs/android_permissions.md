# Android Permissions & API Limitations — Smart Rider HMI

## 1. Executive Summary

Implementing physical remote control of telephony, media playback, voice assistant, and navigation on modern Android is heavily governed by Android's privacy, security, and power-management frameworks. Functionality cannot simply be assumed; each feature requires specific APIs, permission grants, manifest declarations, and user-initiated configuration steps.

This document provides a comprehensive technical audit of the APIs, required permissions, platform limitations across Android versions (Android 8.0 / API 26 through Android 15 / API 35), and recommended architectural mitigation strategies.

---

## 2. Feature-by-Feature Permission & API Analysis

### 2.1 Call Answering & Call Rejection

#### Official APIs
- **Accept Call**: `TelecomManager.acceptRingingCall()` *(Available API 26+)*
- **End / Reject Call**: `TelecomManager.endCall()` *(Available API 28+)*

#### Required Permissions
```xml
<uses-permission android:name="android.permission.ANSWER_PHONE_CALLS" />
<uses-permission android:name="android.permission.CALL_PHONE" />
```

#### Technical Realities & Limitations
1. **Runtime Permission Requirement**:
   `ANSWER_PHONE_CALLS` is classified as `dangerous` and must be explicitly requested at runtime with rider consent.
2. **Android 10+ (API 29+) Background Launch Restrictions**:
   Android restricts starting activities or showing call screens from the background. Because our service runs as a persistent Foreground Service (`FOREGROUND_SERVICE`), invoking `acceptRingingCall()` directly on the `TelecomManager` system service succeeds without needing to pop an activity.
3. **Google Play Store Policy Constraints**:
   Google Play restricts apps using `ANSWER_PHONE_CALLS` and `READ_CALL_LOG`. To publish on Google Play, the app must submit a **Permissions Declaration Form** justifying the core use case as a **"Connected Device / Automobile Companion Application"** (similar to Garmin Connect, Android Auto, or Sena utility apps).
4. **Fallback Mechanism**:
   If `TelecomManager.acceptRingingCall()` is blocked on certain restricted OEM builds, the fallback is simulating a wired headset hook event (`KeyEvent.KEYCODE_HEADSETHOOK`) via `AudioManager.dispatchMediaKeyEvent()`.

---

### 2.2 Caller Identification & Spoken Announcements

#### Official APIs
- **Call State Monitoring**: `TelephonyCallback` *(API 31+)* and `PhoneStateListener` *(API 26–30)*
- **Caller Contact Resolution**: `ContactsContract.PhoneLookup` ContentProvider
- **Spoken Audio**: Android `TextToSpeech` engine with `AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE`

#### Required Permissions
```xml
<uses-permission android:name="android.permission.READ_PHONE_STATE" />
<uses-permission android:name="android.permission.READ_CALL_LOG" />
<uses-permission android:name="android.permission.READ_CONTACTS" />
```

#### Technical Realities & Limitations
1. **The Android 9 (API 28) Breaking Change**:
   Prior to Android 9, `READ_PHONE_STATE` was sufficient to read the incoming telephone number. From Android 9 onward, the `EXTRA_INCOMING_NUMBER` field is intentionally withheld as an empty string unless the app is **also** granted `READ_CALL_LOG`.
2. **Resolution Pipeline**:
   When the state transitions to `CALL_STATE_RINGING`:
   - Step 1: Read incoming phone number from telephony callback.
   - Step 2: Query `ContactsContract.PhoneLookup.CONTENT_FILTER_URI` with the number.
   - Step 3: If match found, retrieve `DISPLAY_NAME`; otherwise format raw phone digits.
   - Step 4: Request audio focus ducking any background media.
   - Step 5: Speak: *"Incoming call from [Name]."*

---

### 2.3 Media Playback Control (Play / Pause / Skip)

#### Recommended Architecture: `MediaSessionManager` + `NotificationListenerService`
To control third-party music apps (Spotify, YouTube Music, Apple Music, SoundCloud, Audible, etc.), the application must obtain references to active media sessions.

```kotlin
val mediaSessionManager = context.getSystemService(Context.MEDIA_SESSION_SERVICE) as MediaSessionManager
val activeSessions = mediaSessionManager.getActiveSessions(componentName)
val controller = activeSessions.firstOrNull()
controller?.transportControls?.skipToNext()
```

#### Required Permissions & Special Access
```xml
<service
    android:name=".service.SmartRiderNotificationListener"
    android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
    android:exported="true">
    <intent-filter>
        <action android:name="android.service.notification.NotificationListenerService" />
    </intent-filter>
</service>
```

#### Technical Realities & Limitations
1. **Special Access Dialog (Cannot be prompted via simple runtime dialog)**:
   `BIND_NOTIFICATION_LISTENER_SERVICE` is a **Special App Access** permission. The application cannot grant it via a standard popup; it must navigate the user directly into the system settings screen:
   ```kotlin
   context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
   ```
2. **Fallback without Notification Access**:
   If the user refuses notification access, the app falls back to dispatching global media key events:
   ```kotlin
   audioManager.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE))
   audioManager.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE))
   ```
   *Limitation of Fallback*: In Android 11+, synthetic key events are dropped if no media player currently holds active audio focus. Notification Access is the primary, robust solution.

---

### 2.4 Bluetooth Low Energy (BLE)

#### Required Permissions by Android Version

**For Android 12+ (API 31, 32, 33, 34, 35)**:
```xml
<uses-permission 
    android:name="android.permission.BLUETOOTH_SCAN" 
    android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
```

**For Android 8.0 to Android 11 (API 26–30)**:
```xml
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

#### Technical Realities & Limitations
1. **The `neverForLocation` Flag**:
   Declaring `android:usesPermissionFlags="neverForLocation"` on `BLUETOOTH_SCAN` informs Android that the BLE scanner is strictly for peripheral communication, completely eliminating the need to prompt the user for invasive Location permissions on Android 12+.
2. **Hardware Requirement Declarations**:
   ```xml
   <uses-feature android:name="android.hardware.bluetooth_le" android:required="true" />
   ```

---

### 2.5 Background Operation & Service Persistence

The companion app must remain running in the background when the phone is locked inside the rider's pocket.

#### Android 14+ (API 34+) Foreground Service Types
Android 14 mandates explicit declaration of foreground service types:
```xml
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />

<service
    android:name=".service.SmartRiderService"
    android:foregroundServiceType="connectedDevice|microphone"
    android:exported="false" />
```

#### Battery Optimization Exemption
```xml
<uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />
```
- OEM custom battery managers (Xiaomi MIUI / HyperOS, Samsung OneUI, OnePlus OxygenOS) aggressively terminate background services after 15–30 minutes of screen-off time.
- The onboarding wizard must provide clear guidance for users to disable battery optimization and enable "Autostart" for the Smart Rider app.

---

### 2.6 Voice Assistant & Speech Recognition

#### APIs
- `android.speech.SpeechRecognizer`
- `RecognizerIntent.ACTION_RECOGNIZE_SPEECH`

#### Required Permissions
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

#### Manifest Package Visibility Query (Android 11+ / API 30+)
Android 11 restricts package visibility. The app must declare intent queries to bind to the Google speech recognition service:
```xml
<queries>
    <intent>
        <action android:name="android.speech.RecognitionService" />
    </intent>
</queries>
```

#### Technical Realities & Limitations
1. **Microphone in Background / Locked Screen**:
   Starting audio capture when the device screen is off requires the foreground service to hold `foregroundServiceType="microphone"`.
2. **Audio Ducking**:
   Before initiating speech recognition, the service must request transient audio focus (`AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`) so any playing music or podcast lowers in volume while the rider speaks.

---

### 2.7 Quick Navigation & Weather Monitoring

#### Navigation Intent (No Special Permissions)
Launching Google Maps to a saved latitude/longitude:
```kotlin
val gmmIntentUri = Uri.parse("google.navigation:q=$latitude,$longitude&mode=d")
val mapIntent = Intent(Intent.ACTION_VIEW, gmmIntentUri).apply {
    setPackage("com.google.android.apps.maps")
    flags = Intent.FLAG_ACTIVITY_NEW_TASK
}
context.startActivity(mapIntent)
```
Manifest query for Android 11+:
```xml
<queries>
    <package android:name="com.google.android.apps.maps" />
</queries>
```

#### Weather Monitoring (Open-Meteo REST API)
- **API**: `https://api.open-meteo.com/v1/forecast?latitude=...&longitude=...&hourly=precipitation_probability,rain`
- **Cost / Keys**: Free, open-source, requires **no API key**.
- **Permissions**:
  ```xml
  <uses-permission android:name="android.permission.INTERNET" />
  <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
  <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
  ```

---

## 3. Comprehensive Permission Matrix

| Permission Name | Protection Level | Purpose | Mandatory / Optional |
| :--- | :--- | :--- | :--- |
| `BLUETOOTH_CONNECT` | Dangerous (API 31+) | Connect & communicate with ESP32 | **Mandatory** |
| `BLUETOOTH_SCAN` | Dangerous (API 31+) | Discover ESP32 remote | **Mandatory** |
| `FOREGROUND_SERVICE` | Normal | Keep BLE connection active in pocket | **Mandatory** |
| `RECORD_AUDIO` | Dangerous | Handle voice assistant commands | **Mandatory** |
| `ANSWER_PHONE_CALLS`| Dangerous | Accept / reject calls via handlebar buttons | **Mandatory** |
| `READ_PHONE_STATE` | Dangerous | Detect incoming ring / active call | **Mandatory** |
| `READ_CALL_LOG` | Dangerous | Read caller number for announcements | Recommended (fallback to generic ring) |
| `READ_CONTACTS` | Dangerous | Match caller number to contact name | Recommended |
| `BIND_NOTIFICATION_LISTENER`| Special Access | Read & control music players (Spotify, etc.)| **Mandatory for Music** |
| `ACCESS_FINE_LOCATION`| Dangerous | Weather query location | Optional (saved city fallback) |
| `REQUEST_IGNORE_BATTERY`| Normal / Special Intent| Prevent Android from killing service on rides| Highly Recommended |

---

## 4. User Onboarding & Permission Grant Strategy

To avoid overwhelming the rider with a barrage of system dialogs on first launch, the app implements a **Phased Educational Onboarding Flow**:

1. **Step 1: Welcome & Value Proposition**: Explain why permissions are required for road safety.
2. **Step 2: Bluetooth & Remote Setup**: Request `BLUETOOTH_SCAN` & `BLUETOOTH_CONNECT`. Discover and pair remote.
3. **Step 3: Call & Audio Controls**: Explain caller announcement and button control. Request `ANSWER_PHONE_CALLS`, `READ_PHONE_STATE`, `READ_CALL_LOG`, `READ_CONTACTS`.
4. **Step 4: Music Control**: Provide direct one-tap button to open `Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS` with clear graphic illustration.
5. **Step 5: Voice Assistant**: Request `RECORD_AUDIO` and test microphone with spoken beep.
6. **Step 6: Battery Optimization**: Guide user to disable battery restrictions so the app persists for 8+ hour road trips.
