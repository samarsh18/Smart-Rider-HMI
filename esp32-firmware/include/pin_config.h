#ifndef PIN_CONFIG_H
#define PIN_CONFIG_H

#include <stdint.h>

/**
 * =====================================================================
 * Smart Rider HMI - ESP32 Hardware Pin Configuration
 * Target Board: ESP32-WROOM-32
 * =====================================================================
 * All buttons are configured as active-low inputs with internal pull-ups
 * (INPUT_PULLUP). Pressing a button pulls the respective GPIO to GND.
 */

// --- 7 V1 Physical Pushbuttons ---
#define PIN_BTN_ANSWER_CALL      18   // Button 1: Short press answers call
#define PIN_BTN_REJECT_END_CALL  19   // Button 2: Short press rejects/ends call
#define PIN_BTN_PLAY_PAUSE       21   // Button 3: Short press toggles media
#define PIN_BTN_NEXT_TRACK       22   // Button 4: Short press skips to next track
#define PIN_BTN_PREV_TRACK       23   // Button 5: Short press skips to previous track
#define PIN_BTN_QUICK_NAV        25   // Button 6: Short press launches saved nav
#define PIN_BTN_VOICE_ASSISTANT  26   // Button 7: Long press (~1.2s) activates voice

// --- Feedback Outputs ---
#define PIN_BUZZER               27   // Active Piezo Buzzer (PWM / tone)
#define PIN_LED_BLE_BLUE         32   // Blue LED: BLE Connection Status
#define PIN_LED_STATUS_GREEN     33   // Green LED: Action / Feedback Indicator

// --- Battery Telemetry (Optional ADC) ---
#define PIN_BATTERY_ADC          35   // Input-only ADC1 pin for 1S LiPo voltage divider

// --- Timing Thresholds (Milliseconds) ---
#define DEBOUNCE_TIME_MS         40   // Software debounce filter
#define LONG_PRESS_THRESHOLD_MS  1200 // Long press trigger for BTN_VOICE_ASSISTANT
#define MULTI_PRESS_LOCKOUT_MS   200  // Multi-key lockout threshold

#endif // PIN_CONFIG_H
