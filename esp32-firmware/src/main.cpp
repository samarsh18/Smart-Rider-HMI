#include <Arduino.h>
#include "pin_config.h"
#include "protocol_v1.h"

/**
 * =====================================================================
 * Smart Rider HMI - ESP32 Handlebar Remote Firmware (M1 Scaffold)
 * =====================================================================
 * This file establishes the entry point, pin configuration, and hardware
 * self-test diagnostics for the physical remote. Full BLE GATT server
 * and debounced state machine logic are scheduled for M2.
 */

void setupPins() {
    // Configure all 7 button inputs with internal pull-ups
    pinMode(PIN_BTN_ANSWER_CALL, INPUT_PULLUP);
    pinMode(PIN_BTN_REJECT_END_CALL, INPUT_PULLUP);
    pinMode(PIN_BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(PIN_BTN_NEXT_TRACK, INPUT_PULLUP);
    pinMode(PIN_BTN_PREV_TRACK, INPUT_PULLUP);
    pinMode(PIN_BTN_QUICK_NAV, INPUT_PULLUP);
    pinMode(PIN_BTN_VOICE_ASSISTANT, INPUT_PULLUP);

    // Configure status LEDs and buzzer
    pinMode(PIN_LED_BLE_BLUE, OUTPUT);
    pinMode(PIN_LED_STATUS_GREEN, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);

    digitalWrite(PIN_LED_BLE_BLUE, LOW);
    digitalWrite(PIN_LED_STATUS_GREEN, LOW);
    digitalWrite(PIN_BUZZER, LOW);
}

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("==========================================");
    Serial.println("  Smart Rider HMI - ESP32 Remote (M1)");
    Serial.println("  Firmware Version: 1.0.0-M1");
    Serial.println("==========================================");

    setupPins();
    Serial.println("[HW] GPIO pins initialized with INPUT_PULLUP.");
    Serial.println("[HW] Status LEDs and Buzzer configured.");
    Serial.println("[INFO] Ready for M2: Debounced state machine & BLE server.");
}

void loop() {
    // Scaffold heartbeat blink while awaiting M2 implementation
    digitalWrite(PIN_LED_BLE_BLUE, HIGH);
    delay(100);
    digitalWrite(PIN_LED_BLE_BLUE, LOW);
    delay(2900);
}
