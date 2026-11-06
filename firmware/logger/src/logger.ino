/*
 * TALAVERA v1 - Thrust Logger
 * Target: ESP32-DevKitC V4  (ESP32-WROOM-32D module)
 * Ignitia Rocket Lab - Tecnologico de Monterrey, Campus Guadalajara
 *
 * ---------------------------------------------------------------------------
 * THIS CODE HAS NO SAFETY AUTHORITY.
 *
 * Arming, firing and emergency stop on TALAVERA are hardware only: switches,
 * relay contacts and resistors. This sketch cannot arm, cannot fire, cannot
 * abort and cannot stop anything. It has no output pins that leave its own
 * subsystem, by design and by board layout.
 *
 * If this code crashes, hangs or is deleted entirely, the bench remains
 * exactly as safe. The only consequence is a missing thrust record.
 *
 * Do not add an output that reaches the arm line, the fire line, the shunt
 * coil, the master coil or the igniter pair. If a change appears to need one,
 * that change is wrong - raise it as a hardware question.
 * ---------------------------------------------------------------------------
 *
 * THE RADIO IS DELIBERATELY STOPPED. DO NOT ENABLE IT.
 *
 * The ESP32 carries Wi-Fi and Bluetooth. TALAVERA exists partly to remove RF
 * from the safety path, and a 2.4 GHz transmitter at up to +20 dBm sitting
 * centimetres from the AD620 front end and from a 20 m pyrotechnic cable is
 * an EMI source next to the two most sensitive things on the bench.
 *
 * killRadios() below is called first in setup() and must stay there. Enabling
 * Wi-Fi or BT is a hardware and safety question, not a firmware convenience -
 * see decision D-029 in docs/DECISION-LOG.md.
 * ---------------------------------------------------------------------------
 *
 * BEHAVIOUR: it records while RECORD is closed.
 *
 * No state machine. No commands. No radio. No diagnostics routine. The file
 * opens when RECORD closes and is closed cleanly when RECORD opens, so the
 * data file survives the E-STOP press that follows in the post-test procedure.
 *
 * This is deliberate. Wirikuta 1.1 ran a nine-state machine with six remote
 * commands, and two defects in it are documented in docs/REQUIREMENTS.md.
 * A logger with one behaviour has nowhere to hide a defect of that kind.
 *
 * Side benefit: the CSV contains thrust data only, so the manual cell
 * deletion that the Kalman script used to require is no longer necessary.
 *
 * ---------------------------------------------------------------------------
 * STATUS: PRELIMINARY SKELETON. NOT VERIFIED AGAINST HARDWARE.
 *
 * THE ADC IS UNDER REVIEW. The ADS1115 code below is a placeholder. Its
 * selection has been reopened (D-036) because the reported field problems
 * point at I2C rather than at conversion quality, and IGNIS-v5 documented
 * the same I2C trouble independently. If an SPI part is chosen - AD7190,
 * ADS1256 or MCP3561 are the candidates - this file's acquisition calls and
 * the I2C pin definitions are replaced wholesale. See
 * docs/ADC-TRADE-STUDY.md before investing effort here.
 *
 * The calibration constants below are placeholders. They cannot be filled in
 * until the load cell datasheet is available - see open item 4 in
 * docs/REQUIREMENTS.md. Do not trust any thrust figure this produces until
 * CAL_N_PER_COUNT has been derived from the datasheet and verified against a
 * known calibration mass in Stage 4 of test/BRINGUP-PLAN.md.
 * ---------------------------------------------------------------------------
 */

#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <WiFi.h>
#include <esp_bt.h>

// ---------------------------------------------------------------------------
// Pin map - ESP32-DevKitC V4. Every pin here belongs to the logger only.
//
// Pins were chosen to avoid the ESP32 traps rather than for convenience:
//   - GPIO6..11  are wired to the SPI flash. Never usable.
//   - GPIO0,2,5,12,15 are strapping pins and are avoided entirely, so a
//     cable left connected cannot stop the module from booting.
//   - GPIO34..39 are input-only, which is why RECORD sits on 34: that pin
//     is physically incapable of becoming an output by a coding mistake.
//
// Note on Wirikuta: its firmware defined SERVO_PIN 5 and BUTTON_PIN 5 on the
// same microcontroller, so the servo gating the igniter line shared a pin
// with an unrelated input. Keeping this map short, single-purpose and
// commented is how that class of mistake is avoided, not by being careful.
// ---------------------------------------------------------------------------
static const uint8_t PIN_SD_CS    = 4;   // microSD chip select
static const uint8_t PIN_SD_SCK   = 18;  // VSPI default
static const uint8_t PIN_SD_MISO  = 19;  // VSPI default
static const uint8_t PIN_SD_MOSI  = 23;  // VSPI default
static const uint8_t PIN_I2C_SDA  = 21;  // ADS1115
static const uint8_t PIN_I2C_SCL  = 22;  // ADS1115
static const uint8_t PIN_LED_OK   = 13;  // Logger-local LED. NOT the bench beacon.
static const uint8_t PIN_RECORD   = 34;  // INPUT-ONLY. Closed to GND = record.

// ---------------------------------------------------------------------------
// Acquisition settings
//
// The ADS1115 caps the sample rate at 860 SPS, not the ESP32. Running the
// ESP32 faster than the converter buys nothing but duplicated samples, so
// the interval below is set from the converter's limit with margin.
// Confirm against the motor thrust rise time before Gate 4.
// ---------------------------------------------------------------------------
static const uint16_t SAMPLE_INTERVAL_MS = 3;     // ~333 Hz, inside the ADS1115 860 SPS ceiling
static const uint16_t FLUSH_INTERVAL_MS  = 500;   // Bound data loss if power is cut unexpectedly

// ---------------------------------------------------------------------------
// Calibration - PLACEHOLDER VALUES, NOT VERIFIED
//
// CAL_N_PER_COUNT must be derived from:
//   - load cell rated output (mV/V)        <- TBD, needs datasheet
//   - excitation voltage                   <- TBD, set by hardware
//   - AD620 gain                           <- TBD, set by Rg at Gate 2
//   - ADS1115 full-scale range and PGA     <- set below
// then verified with a known mass in Stage 4 of the bring-up plan.
//
// Wirikuta used CALIBRATION_PARAM 0.23734177 (manual Annex C). That value
// belongs to Wirikuta's gain chain and does NOT carry over to this board.
// ---------------------------------------------------------------------------
static const float CAL_N_PER_COUNT = 1.0f;   // TBD - placeholder. Logs raw counts as newtons until set.
static const bool  CAL_VERIFIED    = false;  // Set true only after Stage 4 sign-off.

Adafruit_ADS1115 ads;
File logFile;

static uint32_t lastSample = 0;
static uint32_t lastFlush  = 0;
static bool     recording  = false;
static bool     hwReady    = false;

// Stop both radios before anything else runs. See the header block.
static void killRadios() {
  WiFi.persistent(false);
  WiFi.disconnect(true, true);
  WiFi.mode(WIFI_OFF);
  btStop();
}

static bool recordRequested() {
  // Active low. The pin is input-only and needs an EXTERNAL pull-up:
  // GPIO34..39 have no internal pull-ups. An open or broken RECORD line
  // therefore reads as "not recording", which loses data but changes
  // nothing about bench safety.
  return digitalRead(PIN_RECORD) == LOW;
}

// Pick the next unused filename: LOG000.CSV, LOG001.CSV, ...
// Highest number is always the most recent test, matching Wirikuta convention.
static bool openNextFile() {
  char name[16];
  for (uint16_t i = 0; i < 1000; i++) {
    snprintf(name, sizeof(name), "/LOG%03u.CSV", i);
    if (!SD.exists(name)) {
      logFile = SD.open(name, FILE_WRITE);
      return (bool)logFile;
    }
  }
  return false;  // 1000 files on the card. Archive them.
}

static void startRecording() {
  if (!openNextFile()) {
    Serial.println(F("could not open a log file"));
    return;
  }
  // Header. Thrust data only - no diagnostic rows, so the analysis script
  // can parse this file with nothing deleted by hand.
  logFile.println(F("# TALAVERA v1 thrust log"));
  logFile.println(F("# logger: ESP32-WROOM-32D, radios stopped"));
  logFile.print(F("# cal_n_per_count="));
  logFile.print(CAL_N_PER_COUNT, 8);
  logFile.print(F(" cal_verified="));
  logFile.println(CAL_VERIFIED ? F("true") : F("false"));
  logFile.println(F("millis,raw_counts,thrust_N"));
  logFile.flush();

  recording = true;
  digitalWrite(PIN_LED_OK, HIGH);   // Lit = recording.
  Serial.println(F("recording"));
}

static void stopRecording() {
  if (logFile) {
    logFile.flush();
    logFile.close();                // Clean close - this is the whole point of RECORD.
  }
  recording = false;
  digitalWrite(PIN_LED_OK, LOW);
  Serial.println(F("stopped, file closed"));
}

void setup() {
  killRadios();                     // First. Always.

  pinMode(PIN_LED_OK, OUTPUT);
  digitalWrite(PIN_LED_OK, LOW);
  pinMode(PIN_RECORD, INPUT);       // GPIO34: input-only, external pull-up required.

  Serial.begin(115200);
  Serial.println(F("TALAVERA logger - no safety authority - radios stopped"));

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  if (!ads.begin()) {
    Serial.println(F("ADC not found"));
    return;                         // Stays dark. A dark logger LED means no data, not an unsafe bench.
  }
  // +/- 4.096 V full scale, fastest conversion. Revisit the PGA once the
  // AD620 gain is fixed at Gate 2 - note the ADS1115 runs on 3.3 V here, so
  // its input must stay within 3.3 V + 0.3 V regardless of this setting.
  ads.setGain(GAIN_ONE);
  ads.setDataRate(RATE_ADS1115_860SPS);

  SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
  if (!SD.begin(PIN_SD_CS)) {
    Serial.println(F("SD not found"));
    return;
  }

  hwReady = true;
  Serial.println(F("ready - waiting for RECORD"));
}

void loop() {
  if (!hwReady) return;

  const bool want = recordRequested();

  if (want && !recording) {
    startRecording();
  } else if (!want && recording) {
    stopRecording();                // File closed before the operator presses E-STOP.
  }

  if (!recording) return;

  const uint32_t now = millis();

  if (now - lastSample >= SAMPLE_INTERVAL_MS) {
    lastSample = now;

    // Differential across AIN0/AIN1 - the buffered instrumentation amp output.
    const int16_t raw = ads.readADC_Differential_0_1();

    // Raw counts are written alongside the scaled value so a log taken before
    // calibration is still usable afterwards.
    logFile.print(now);
    logFile.print(',');
    logFile.print(raw);
    logFile.print(',');
    logFile.println(raw * CAL_N_PER_COUNT, 4);
  }

  if (now - lastFlush >= FLUSH_INTERVAL_MS) {
    lastFlush = now;
    logFile.flush();                // Bounds loss to FLUSH_INTERVAL_MS if power is cut.
  }
}
