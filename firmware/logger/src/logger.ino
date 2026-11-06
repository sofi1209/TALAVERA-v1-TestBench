/*
 * TALAVERA v1 - Thrust Logger
 * Target: ESP32-DevKitC V4  (ESP32-WROOM-32D module)
 * Converter: ADS1220, 24-bit, over SPI
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
 * A 2.4 GHz transmitter at up to +20 dBm would sit centimetres from the
 * analog front end and from the pyrotechnic wiring - the two most
 * EMI-sensitive things on the bench. killRadios() runs first in setup() and
 * must stay there. See decision D-029.
 * ---------------------------------------------------------------------------
 *
 * BEHAVIOUR: it records while RECORD is closed. No state machine, no
 * commands, no radio, no diagnostics routine. The file opens when RECORD
 * closes and is closed cleanly when RECORD opens, so the data file survives
 * the E-STOP press that follows in the post-test procedure.
 *
 * ---------------------------------------------------------------------------
 * STATUS: PRELIMINARY SKELETON. NOT COMPILED, NOT VERIFIED AGAINST HARDWARE.
 *
 * The ADS1220 register values below are PLACEHOLDERS. Gain, data rate and
 * reference source all depend on the load cell datasheet (open item O-2) and
 * must be confirmed against the ADS1220 datasheet before use. Register-level
 * SPI is used deliberately rather than a third-party library, so there is no
 * dependency that cannot be read and checked here.
 * ---------------------------------------------------------------------------
 */

#include <SPI.h>
#include <SD.h>
#include <WiFi.h>
#include <esp_bt.h>

// ---------------------------------------------------------------------------
// Pin map - ESP32-WROOM-32D. Matches MCU1 on the bench schematic.
//
// Avoids GPIO6-11 (SPI flash) and every strapping pin (0, 2, 5, 12, 15), so a
// cable left connected cannot stop the module booting. RECORD is on GPIO34
// because 34-39 are INPUT-ONLY and so physically cannot become outputs
// through a coding mistake - they also have no internal pull-up, hence the
// external one on the schematic.
//
// SD card and ADC share one VSPI bus with separate chip selects, the same
// arrangement IGNIS-v5 uses for its SD card and radio.
// ---------------------------------------------------------------------------
static const uint8_t PIN_SPI_SCK  = 18;
static const uint8_t PIN_SPI_MISO = 19;
static const uint8_t PIN_SPI_MOSI = 23;
static const uint8_t PIN_ADC_CS   = 17;
static const uint8_t PIN_ADC_DRDY = 16;   // active low, data ready
static const uint8_t PIN_SD_CS    =  4;
static const uint8_t PIN_SD_DETECT= 27;   // card present, active low
static const uint8_t PIN_RECORD   = 34;   // INPUT-ONLY, external pull-up
static const uint8_t PIN_LED_OK   = 13;   // logger-local only. NOT the bench beacon.

// ---------------------------------------------------------------------------
// ADS1220 command set
// ---------------------------------------------------------------------------
static const uint8_t CMD_RESET  = 0x06;
static const uint8_t CMD_START  = 0x08;
static const uint8_t CMD_RDATA  = 0x10;
static const uint8_t CMD_WREG   = 0x40;   // | (reg << 2) | (len - 1)

// ---------------------------------------------------------------------------
// ADS1220 configuration - ALL FOUR BYTES ARE PLACEHOLDERS (O-2)
//
//   REG0  MUX[7:4] GAIN[3:1] PGA_BYPASS[0]
//   REG1  DR[7:5] MODE[4:3] CM[2] TS[1] BCS[0]
//   REG2  VREF[7:6] FIR[5:4] PSW[3] IDAC[2:0]
//   REG3  I1MUX[7:5] I2MUX[4:2] DRDYM[1] -
//
// Intent, to be confirmed against the datasheet and the load cell:
//   - differential AIN0-AIN1, PGA enabled, gain set from the cell's mV/V
//   - continuous conversion so the burn is captured without re-triggering
//   - EXTERNAL reference on REFP0/REFN0, tied to the bridge excitation, so
//     the measurement is ratiometric and excitation drift cancels
// ---------------------------------------------------------------------------
static const uint8_t ADS_REG0 = 0x00;   // TBD - gain depends on O-2
static const uint8_t ADS_REG1 = 0x04;   // TBD - data rate and continuous mode
static const uint8_t ADS_REG2 = 0x40;   // TBD - external reference
static const uint8_t ADS_REG3 = 0x00;   // TBD

static const uint16_t FLUSH_INTERVAL_MS = 500;

// ---------------------------------------------------------------------------
// Calibration - PLACEHOLDER, NOT VERIFIED
//
// Derive from the load cell rated output (mV/V), the excitation voltage, the
// configured PGA gain and the reference, then verify against a known mass in
// Stage 4 of test/BRINGUP-PLAN.md. Wirikuta's CALIBRATION_PARAM belongs to a
// different gain chain and does NOT carry over.
// ---------------------------------------------------------------------------
static const float CAL_N_PER_COUNT = 1.0f;
static const bool  CAL_VERIFIED    = false;

SPISettings adcSpi(1000000, MSBFIRST, SPI_MODE1);   // ADS1220 is CPOL=0, CPHA=1
File logFile;
static uint32_t lastFlush = 0;
static bool recording = false, hwReady = false;

static void killRadios() {
  WiFi.persistent(false);
  WiFi.disconnect(true, true);
  WiFi.mode(WIFI_OFF);
  btStop();
}

static void adcCmd(uint8_t c) {
  SPI.beginTransaction(adcSpi);
  digitalWrite(PIN_ADC_CS, LOW);
  SPI.transfer(c);
  digitalWrite(PIN_ADC_CS, HIGH);
  SPI.endTransaction();
}

static void adcConfigure() {
  adcCmd(CMD_RESET);
  delay(1);
  SPI.beginTransaction(adcSpi);
  digitalWrite(PIN_ADC_CS, LOW);
  SPI.transfer(CMD_WREG | (0 << 2) | 3);   // write 4 registers starting at 0
  SPI.transfer(ADS_REG0);
  SPI.transfer(ADS_REG1);
  SPI.transfer(ADS_REG2);
  SPI.transfer(ADS_REG3);
  digitalWrite(PIN_ADC_CS, HIGH);
  SPI.endTransaction();
  adcCmd(CMD_START);                        // continuous conversion
}

// Returns the latest 24-bit signed sample, sign-extended to 32 bits.
static int32_t adcRead() {
  SPI.beginTransaction(adcSpi);
  digitalWrite(PIN_ADC_CS, LOW);
  SPI.transfer(CMD_RDATA);
  uint32_t v = ((uint32_t)SPI.transfer(0xFF) << 16) |
               ((uint32_t)SPI.transfer(0xFF) << 8) |
                (uint32_t)SPI.transfer(0xFF);
  digitalWrite(PIN_ADC_CS, HIGH);
  SPI.endTransaction();
  if (v & 0x800000UL) v |= 0xFF000000UL;    // sign-extend
  return (int32_t)v;
}

static bool recordRequested() {
  // Active low. An open or broken RECORD line reads as "not recording",
  // which loses data and changes nothing about bench safety (D-032).
  return digitalRead(PIN_RECORD) == LOW;
}

static bool cardPresent() {
  return digitalRead(PIN_SD_DETECT) == LOW;
}

static bool openNextFile() {
  char name[16];
  for (uint16_t i = 0; i < 1000; i++) {
    snprintf(name, sizeof(name), "/LOG%03u.CSV", i);
    if (!SD.exists(name)) {
      logFile = SD.open(name, FILE_WRITE);
      return (bool)logFile;
    }
  }
  return false;
}

static void startRecording() {
  if (!openNextFile()) { Serial.println(F("could not open a log file")); return; }
  logFile.println(F("# TALAVERA v1 thrust log"));
  logFile.println(F("# logger: ESP32-WROOM-32D, radios stopped"));
  logFile.println(F("# adc: ADS1220, SPI, differential AIN0-AIN1"));
  logFile.print(F("# cal_n_per_count="));
  logFile.print(CAL_N_PER_COUNT, 8);
  logFile.print(F(" cal_verified="));
  logFile.println(CAL_VERIFIED ? F("true") : F("false"));
  logFile.println(F("millis,raw_counts,thrust_N"));
  logFile.flush();
  recording = true;
  digitalWrite(PIN_LED_OK, HIGH);
  Serial.println(F("recording"));
}

static void stopRecording() {
  if (logFile) { logFile.flush(); logFile.close(); }
  recording = false;
  digitalWrite(PIN_LED_OK, LOW);
  Serial.println(F("stopped, file closed"));
}

void setup() {
  killRadios();                    // first, always

  pinMode(PIN_LED_OK, OUTPUT);
  digitalWrite(PIN_LED_OK, LOW);
  pinMode(PIN_RECORD, INPUT);      // GPIO34: input-only, external pull-up
  pinMode(PIN_SD_DETECT, INPUT_PULLUP);
  pinMode(PIN_ADC_CS, OUTPUT);
  digitalWrite(PIN_ADC_CS, HIGH);
  pinMode(PIN_ADC_DRDY, INPUT);

  Serial.begin(115200);
  Serial.println(F("TALAVERA logger - no safety authority - radios stopped"));

  SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);

  adcConfigure();

  if (!cardPresent()) Serial.println(F("warning: SD_DETECT reports no card"));
  if (!SD.begin(PIN_SD_CS)) { Serial.println(F("SD not found")); return; }

  hwReady = true;
  Serial.println(F("ready - waiting for RECORD"));
}

void loop() {
  if (!hwReady) return;

  const bool want = recordRequested();
  if (want && !recording)       startRecording();
  else if (!want && recording)  stopRecording();
  if (!recording) return;

  // Pace from the converter, not from a timer: DRDY falls when a new sample
  // exists, so the log rate is whatever the ADS1220 is actually configured
  // for and no sample is duplicated or missed.
  if (digitalRead(PIN_ADC_DRDY) == LOW) {
    const int32_t raw = adcRead();
    const uint32_t now = millis();
    logFile.print(now);
    logFile.print(',');
    logFile.print(raw);
    logFile.print(',');
    logFile.println(raw * CAL_N_PER_COUNT, 4);
  }

  const uint32_t now = millis();
  if (now - lastFlush >= FLUSH_INTERVAL_MS) {
    lastFlush = now;
    logFile.flush();             // bounds loss if power is cut unexpectedly
  }
}
