/*
 * TALAVERA v1 - Thrust Logger
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
 * BEHAVIOUR: it records whenever it has power.
 *
 * No state machine. No commands. No radio. No diagnostics routine. The file
 * opens at power-on and closes when the logger's own switch is turned off.
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

// ---------------------------------------------------------------------------
// Pin map. Every pin here belongs to the logger subsystem only.
//
// Note on Wirikuta: its firmware defined SERVO_PIN 5 and BUTTON_PIN 5 on the
// same microcontroller, so the servo gating the igniter line shared a pin
// with an unrelated input. Keeping this map short and single-purpose is how
// that class of mistake is avoided, not by being more careful.
// ---------------------------------------------------------------------------
static const uint8_t PIN_SD_CS   = 10;  // SD card chip select
static const uint8_t PIN_LED_OK  = 2;   // Logger-local status LED. NOT the bench beacon.

// ---------------------------------------------------------------------------
// Acquisition settings
// ---------------------------------------------------------------------------
static const uint16_t SAMPLE_INTERVAL_MS = 2;     // 500 Hz target. TBD - confirm against motor rise time.
static const uint16_t FLUSH_INTERVAL_MS  = 500;   // Bound data loss if power is cut mid-test.

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
static bool     running    = false;

// Pick the next unused filename: LOG000.CSV, LOG001.CSV, ...
// Highest number is always the most recent test, matching Wirikuta convention.
static bool openNextFile() {
  char name[13];
  for (uint16_t i = 0; i < 1000; i++) {
    snprintf(name, sizeof(name), "LOG%03u.CSV", i);
    if (!SD.exists(name)) {
      logFile = SD.open(name, FILE_WRITE);
      return (bool)logFile;
    }
  }
  return false;  // 1000 files on the card. Archive them.
}

void setup() {
  pinMode(PIN_LED_OK, OUTPUT);
  digitalWrite(PIN_LED_OK, LOW);

  Serial.begin(115200);
  Serial.println(F("TALAVERA logger - no safety authority - records while powered"));

  if (!ads.begin()) {
    Serial.println(F("ADC not found"));
    return;  // Stays dark. A dark logger LED means no data, not an unsafe bench.
  }
  // +/- 4.096 V full scale. Revisit once the AD620 gain is fixed at Gate 2.
  ads.setGain(GAIN_ONE);

  if (!SD.begin(PIN_SD_CS)) {
    Serial.println(F("SD not found"));
    return;
  }

  if (!openNextFile()) {
    Serial.println(F("Could not open a log file"));
    return;
  }

  // Header. Thrust data only - no diagnostic rows, so the analysis script
  // can parse this file with nothing deleted by hand.
  logFile.println(F("# TALAVERA v1 thrust log"));
  logFile.print(F("# cal_n_per_count="));
  logFile.print(CAL_N_PER_COUNT, 8);
  logFile.print(F(" cal_verified="));
  logFile.println(CAL_VERIFIED ? F("true") : F("false"));
  logFile.println(F("millis,raw_counts,thrust_N"));
  logFile.flush();

  running = true;
  digitalWrite(PIN_LED_OK, HIGH);   // Lit = recording.
  Serial.println(F("recording"));
}

void loop() {
  if (!running) return;

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
    logFile.flush();   // Bounds loss to FLUSH_INTERVAL_MS if power is cut.
  }
}
