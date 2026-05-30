#pragma once

#include "esphome.h"
#include "RAK12027_D7S.h"
#include "esp_task_wdt.h"

namespace esphome {
namespace sismasens {

static volatile bool g_interrupt1Flag = false;
static volatile bool g_interrupt2Flag = false;
static volatile bool g_clearFlag = false;  // ISR backup jumper GPIO26

// Scala empirica SI → livello intensità Mercalli (JMA)
const double scPGA[10] = {0.0555, 0.232, 0.721, 1.21, 3.38, 7.46, 14.5, 26.1, 44.4, 72.3};
const double scSI[10]  = {0.0178, 0.0939, 0.38995, 0.686, 2.08, 5.06, 10.9, 21.6, 40.3, 71.7};

static void IRAM_ATTR int1_ISR() {
  g_interrupt1Flag = true;
}

static void IRAM_ATTR int2_ISR() {
  g_interrupt2Flag = true;
}

static void IRAM_ATTR resetPin_ISR() {
  g_clearFlag = true;
}

double magnitude(double _SI, double _PGA) {
  // Calcola indipendentemente l'intensità da SI e da PGA, poi prende il massimo.
  // La versione precedente usava un unico ciclo con variabile condivisa: l'interpolazione
  // decimale di PGA veniva ignorata se SI aveva già prodotto una frazione sullo stesso
  // livello intero (condizione mag < (i+1) falsa).
  double mag_si = 0.0, mag_pga = 0.0;
  for (int i = 0; i < 10; i++) {
    if (_SI >= scSI[i]) {
      mag_si = i + 1;
      if (i < 9) mag_si += (_SI - scSI[i]) / (scSI[i + 1] - scSI[i]);
    }
    if (_PGA >= scPGA[i]) {
      mag_pga = i + 1;
      if (i < 9) mag_pga += (_PGA - scPGA[i]) / (scPGA[i + 1] - scPGA[i]);
    }
  }
  return mag_si > mag_pga ? mag_si : mag_pga;
}

class SismasensComponent : public PollingComponent {
 public:
  static const int INT1      = 33;  // IN  - interrupt sismico collapse/shutoff
  static const int INT2      = 32;  // IN  - interrupt sismico earthquake
  static const int SET       = 25;  // OUT - hard reset D7S
  static const int RESET_PIN = 26;  // IN  - backup jumper clear (collegato a GPIO27)


  RAK_D7S D7S;

  sensor::Sensor *earthquake_sensor_{nullptr};
  sensor::Sensor *collapse_sensor_{nullptr};
  sensor::Sensor *shutoff_sensor_{nullptr};
  sensor::Sensor *last_si_sensor_{nullptr};
  sensor::Sensor *last_pga_sensor_{nullptr};
  sensor::Sensor *last_temp_sensor_{nullptr};
  sensor::Sensor *last_mag_sensor_{nullptr};
  sensor::Sensor *inst_si_sensor_{nullptr};
  sensor::Sensor *inst_pga_sensor_{nullptr};
  sensor::Sensor *inst_mag_sensor_{nullptr};

  void set_earthquake_sensor(sensor::Sensor *s) { this->earthquake_sensor_ = s; }
  void set_collapse_sensor(sensor::Sensor *s)   { this->collapse_sensor_ = s; }
  void set_shutoff_sensor(sensor::Sensor *s)    { this->shutoff_sensor_ = s; }
  void set_last_si_sensor(sensor::Sensor *s)    { this->last_si_sensor_ = s; }
  void set_last_pga_sensor(sensor::Sensor *s)   { this->last_pga_sensor_ = s; }
  void set_last_temp_sensor(sensor::Sensor *s)  { this->last_temp_sensor_ = s; }
  void set_last_mag_sensor(sensor::Sensor *s)   { this->last_mag_sensor_ = s; }
  void set_inst_si_sensor(sensor::Sensor *s)    { this->inst_si_sensor_ = s; }
  void set_inst_pga_sensor(sensor::Sensor *s)   { this->inst_pga_sensor_ = s; }
  void set_inst_mag_sensor(sensor::Sensor *s)   { this->inst_mag_sensor_ = s; }

  SismasensComponent() : PollingComponent(100) {}

  float get_setup_priority() const override { return esphome::setup_priority::BUS; }

  bool eq_{false}, cl_{false}, so_{false};
  double SI_{0}, PGA_{0}, TEMP_{0}, MAG_{0};
  bool clear_requested_{false};

  // ---------------------------------------------------------------------------
  // API pubblica — chiamabile da YAML o da altri punti del codice
  // ---------------------------------------------------------------------------

  // SET: hard reset hardware D7S via GPIO25
  void do_set() {
    ESP_LOGD("set", ">   D7S - HARD RESET via SET pin");
    esp_task_wdt_reset();
    digitalWrite(SET, HIGH);
    vTaskDelay(pdMS_TO_TICKS(500));
    digitalWrite(SET, LOW);
    ESP_LOGD("set", ">   D7S - HARD RESET done");
  }

  // CLEAR SENSOR: azzera memoria D7S e sensori ESPHome
  void trigger_clear() { this->clear_requested_ = true; }

  // ---------------------------------------------------------------------------
  // Logica interna clear (chiamata dall'update)
  // ---------------------------------------------------------------------------
  void doFullClear() {
    ESP_LOGD("clear", ">   CLEAR SENSOR - START");
    esp_task_wdt_reset();

    D7S.clearAllData();
    D7S.setAxis(AUTO_SWITCH);
    D7S.setThreshold(THRESHOLD_LOW);
    D7S.resetEvents();

    esp_task_wdt_reset();
    D7S.initialize();
    // Attende che il D7S completi l'installazione (memorizza asse) prima di procedere
    for (int i = 0; i < 30; i++) {
      esp_task_wdt_reset();
      vTaskDelay(pdMS_TO_TICKS(200));
      if (D7S.getState() == NORMAL_MODE) break;
    }

    esp_task_wdt_reset();
    D7S.acquireOffset();
    // Attende completamento offset acquisition
    for (int i = 0; i < 30; i++) {
      esp_task_wdt_reset();
      vTaskDelay(pdMS_TO_TICKS(200));
      if (D7S.getState() == NORMAL_MODE) break;
    }
    esp_task_wdt_reset();

    ESP_LOGD("clear", ">   CLEAR SENSOR - DONE");

    eq_ = false; cl_ = false; so_ = false;
    SI_ = 0; PGA_ = 0; TEMP_ = 0; MAG_ = 0;

    if (earthquake_sensor_ != nullptr) earthquake_sensor_->publish_state(0);
    if (collapse_sensor_ != nullptr)   collapse_sensor_->publish_state(0);
    if (shutoff_sensor_ != nullptr)    shutoff_sensor_->publish_state(0);
    if (last_si_sensor_ != nullptr)    last_si_sensor_->publish_state(0);
    if (last_pga_sensor_ != nullptr)   last_pga_sensor_->publish_state(0);
    if (last_temp_sensor_ != nullptr)  last_temp_sensor_->publish_state(0);
    if (last_mag_sensor_ != nullptr)   last_mag_sensor_->publish_state(0);
    if (inst_si_sensor_ != nullptr)    inst_si_sensor_->publish_state(0);
    if (inst_pga_sensor_ != nullptr)   inst_pga_sensor_->publish_state(0);
    if (inst_mag_sensor_ != nullptr)   inst_mag_sensor_->publish_state(0);
  }

  // ---------------------------------------------------------------------------
  // SETUP
  // ---------------------------------------------------------------------------
  void setup() override {
    ESP_LOGI("main", "######################################");
    ESP_LOGI("main", "#         SISMASENS project          #");
    ESP_LOGI("main", "#              ver. 3.4              #");
    ESP_LOGI("main", "######################################");

    ESP_LOGD("init", "!!! INITIALIZATION !!!");
    Wire.begin(21, 22);
    Wire.setClock(100000);
    ESP_LOGD("init", ">   I2C - OK");

    ESP_LOGD("init", ">   D7S - RESETTING!");
    pinMode(SET, OUTPUT);
    digitalWrite(SET, HIGH);
    esp_task_wdt_reset();
    vTaskDelay(pdMS_TO_TICKS(500));
    digitalWrite(SET, LOW);
    ESP_LOGD("init", ">   D7S - RESETTED!");

    bool ok = false;
    for (int i = 0; i < 50; i++) {
      esp_task_wdt_reset();
      if (D7S.begin()) { ok = true; break; }
      ESP_LOGD("init", ">   D7S - STARTING ...");
      vTaskDelay(pdMS_TO_TICKS(100));
    }
    if (!ok) {
      ESP_LOGE("init", "D7S not found on I2C - giving up");
      return;
    }
    ESP_LOGD("init", ">   D7S - STARTED");

    D7S.setAxis(AUTO_SWITCH);
    D7S.setThreshold(THRESHOLD_LOW);

    pinMode(INT1, INPUT_PULLUP);
    pinMode(INT2, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(INT1), int1_ISR, CHANGE);
    attachInterrupt(digitalPinToInterrupt(INT2), int2_ISR, CHANGE);
    ESP_LOGD("init", "!!! INITIALIZATION interrupt mode !!!");

    pinMode(RESET_PIN, INPUT_PULLDOWN);
    attachInterrupt(digitalPinToInterrupt(RESET_PIN), resetPin_ISR, RISING);
    ESP_LOGD("init", ">   RESET_PIN interrupt - OK");

    ESP_LOGD("init", ">   D7S - INITIALIZING ...");
    esp_task_wdt_reset();
    vTaskDelay(pdMS_TO_TICKS(2000));
    esp_task_wdt_reset();
    D7S.initialize();
    esp_task_wdt_reset();
    vTaskDelay(pdMS_TO_TICKS(2000));
    esp_task_wdt_reset();
    ESP_LOGD("init", ">   D7S - INITIALIZED!");

    D7S.resetEvents();
    ESP_LOGD("init", ">   D7S - READY!");
  }

  // ---------------------------------------------------------------------------
  // UPDATE (ogni 100ms)
  // ---------------------------------------------------------------------------
  void update() override {
    static unsigned long t           = millis();
    static unsigned long tLastShake  = millis();
    static unsigned long tRefresh    = millis();
    static bool weeklyResetDone      = false;
    unsigned long delay_time;

    // --- Reset settimanale ---
    if (millis() - tLastShake > 604800000 && !eq_ && !weeklyResetDone) {
      weeklyResetDone = true;
      tLastShake = millis();
      ESP_LOGD("run", ">   WEEKLY RESET");
      doFullClear();
      return;
    }

    // --- Clear sensor: da button HA o da jumper GPIO26 ---
    if ((clear_requested_ || g_clearFlag) && !eq_) {
      clear_requested_ = false;
      g_clearFlag = false;
      ESP_LOGD("run", ">   CLEAR TRIGGERED");
      doFullClear();
      return;
    }

    // --- Interrupt INT1: collapse / shutoff ---
    // isInCollapse() e isInShutoff() della libreria RAK12027-D7S sono buggati:
    // restituiscono costanti hardcoded (sempre true). Il registro EVENT 0x1002
    // è read-clear: bit1=collapse, bit0=shutoff. Si legge direttamente via Wire.
    if (g_interrupt1Flag) {
      g_interrupt1Flag = false;

      Wire.beginTransmission(0x55);
      Wire.write(0x10); Wire.write(0x02);
      Wire.endTransmission(false);
      Wire.requestFrom((uint8_t)0x55, (uint8_t)1);
      uint8_t events = Wire.available() ? Wire.read() & 0x03 : 0;

      if (events & 0x02) {
        cl_ = true;
        if (collapse_sensor_ != nullptr)
          collapse_sensor_->publish_state(cl_);
        ESP_LOGD("run", ">   COLLAPSE!");
      }
      if (events & 0x01) {
        so_ = true;
        if (shutoff_sensor_ != nullptr)
          shutoff_sensor_->publish_state(so_);
        ESP_LOGD("run", ">   Shutting down all device!");
      }
    }

    // --- Interrupt INT2: earthquake start / end ---
    if (g_interrupt2Flag) {
      g_interrupt2Flag = false;

      if (D7S.isEarthquakeOccuring()) {
        eq_ = true;
        weeklyResetDone = false;
        tLastShake = millis();
        if (earthquake_sensor_ != nullptr)
          earthquake_sensor_->publish_state(eq_);
        ESP_LOGD("run", ">   EARTHQUAKE STARTED!");

      } else {
        eq_ = false; cl_ = false; so_ = false;
        ESP_LOGD("run", ">   EARTHQUAKE ENDED!");

        SI_ = D7S.getLastestSI(0) * 10;                  // kine (cm/s)
        ESP_LOGD("run", ">   READ lastSI");
        vTaskDelay(pdMS_TO_TICKS(350));

        PGA_ = D7S.getLastestPGA(0) / 0.980665;          // g (libreria RAK12027 restituisce ~0.1 m/s² per unità)
        ESP_LOGD("run", ">   READ lastPGA");
        vTaskDelay(pdMS_TO_TICKS(350));

        TEMP_ = D7S.getLastestTemperature(0);
        ESP_LOGD("run", ">   READ lastTEMP");

        MAG_ = magnitude(SI_, PGA_);                      // scPGA calibrata in g

        if (earthquake_sensor_ != nullptr) earthquake_sensor_->publish_state(eq_);
        if (collapse_sensor_   != nullptr) collapse_sensor_->publish_state(cl_);
        if (shutoff_sensor_    != nullptr) shutoff_sensor_->publish_state(so_);
        if (last_si_sensor_    != nullptr) last_si_sensor_->publish_state(SI_);
        if (last_pga_sensor_   != nullptr) last_pga_sensor_->publish_state(PGA_);
        if (last_temp_sensor_  != nullptr) last_temp_sensor_->publish_state(TEMP_);
        if (last_mag_sensor_   != nullptr) last_mag_sensor_->publish_state(MAG_);
      }
    }

    // --- Lettura istantanea SI/PGA/MAG ---
    delay_time = eq_ ? 5000 : 30000;

    if ((millis() - t) > delay_time) {
      t = millis();
      SI_  = D7S.getInstantaneusSI() * 10;               // kine (cm/s)
      PGA_ = D7S.getInstantaneusPGA() / 0.980665;        // g (libreria RAK12027 restituisce ~0.1 m/s² per unità)
      MAG_ = magnitude(SI_, PGA_);                       // scPGA calibrata in g
      ESP_LOGD("sisma", "SI: %f  PGA: %f  MAG: %f", SI_, PGA_, MAG_);

      if (inst_si_sensor_  != nullptr) inst_si_sensor_->publish_state(SI_);
      if (inst_pga_sensor_ != nullptr) inst_pga_sensor_->publish_state(PGA_);
      if (inst_mag_sensor_ != nullptr) inst_mag_sensor_->publish_state(MAG_);
    }

    // --- Reset valori istantanei ogni 10 min (fuori da terremoto) ---
    if (millis() - tRefresh > 600000 && !eq_) {
      tRefresh = millis();
      ESP_LOGD("reset", "Instant values reset");
      if (inst_si_sensor_  != nullptr) inst_si_sensor_->publish_state(0);
      if (inst_pga_sensor_ != nullptr) inst_pga_sensor_->publish_state(0);
      if (inst_mag_sensor_ != nullptr) inst_mag_sensor_->publish_state(0);
    }
  }

};  // chiude SismasensComponent

}  // namespace sismasens
}  // namespace esphome
