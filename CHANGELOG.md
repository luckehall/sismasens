# Changelog

## [FW 4.1.1] — 2026-06-02

### Corretto
- Collapse software: il flag viene posto a `1` in tempo reale durante il terremoto, nel ciclo di lettura istantanea (ogni 5 s), non più a fine evento su `getLatestSI`. Si azzera a `0` al termine del terremoto insieme agli altri flag. Il comportamento precedente (valutazione post-evento) causava un ritardo inaccettabile tra il superamento della soglia SI e la segnalazione a HA/cloud.

## [FW 4.1.0] — 2026-06-02

### Aggiunto
- Fallback software per collapse: se al termine di un terremoto `SI > 10 cm/s`, il flag collapse viene forzato a `true` indipendentemente dal pin INT1 del D7S.

### Motivazione
Il meccanismo hardware di collapse detection del D7S non ha mai prodotto un evento bit1 nel registro EVENT (0x1002) in nessuna condizione di test, nonostante SI e PGA elevati e tentativi su più versioni firmware (4.0.x). La soglia interna del sensore non è documentata né configurabile via I2C. SI > 10 cm/s corrisponde a intensità JMA 5+ (zona di rischio strutturale) ed è una soglia conservativa che replica il comportamento atteso. La soluzione software è esplicita nei log (`SW COLLAPSE: SI=... > 10.0 cm/s`) per distinguerla da un eventuale futuro trigger hardware.

### Corretto
- `setAxis(AXIS_AUTO_SWITCH)` e `setThreshold(THRESHOLD_LOW)` riapplicati dopo il completamento di `initialize()` e `acquireOffset()` sia in `setup()` che in `doFullClear()`. Il D7S può resettare REG_CTRL durante le fasi di calibrazione; senza ri-applicarli il sensore operava con asse YZ fisso e soglia alta (default hardware), abbassando i valori SI calcolati.

## [FW 4.0.0] — 2026-05-31

### Modificato
- Libreria D7S sostituita: `RAK12027-D7S` → `luckehall/d7s-esphome` (riscrittura da zero)
- `isInCollapse()` / `isInShutoff()` eliminati — sostituiti da `d7s_.readEventRegister()` + `isCollapseEvent()` / `isShutoffEvent()` con cache del registro read-clear 0x1002
- Scaling PGA corretto: divisore `0.980665` → `9.80665` (1g = 9.80665 m/s²)
- Scaling SI: rimossa moltiplicazione `* 10` della libreria RAK12027 — la nuova libreria restituisce cm/s nativi
- API corretta: typo `isEarthquakeOccuring` / `getLastest*` / `getInstantneus*` → nomi corretti
- I2C robusto: check `endTransmission()`, timeout 50 ms su `available()`, nessun `delay()` tra write

## [1.1.3] — 2026-05-30

### Corretto
- `_build_payload()`: torna a usare i picchi istantanei `_peak_inst_si`/`_peak_inst_pga` con magnitudine calcolata via `_calc_magnitude()`. I valori `last_*` del D7S non vengono memorizzati per eventi sotto la soglia di detection, rendendo impossibile la pubblicazione di quei dati al cloud. I picchi istantanei sono invece sempre disponibili per qualsiasi evento rilevato dal coordinator.

## [1.1.2] — 2026-05-30

### Corretto
- Coordinator: pubblicazione cloud ritardata di 5 s dopo fine terremoto (`async_call_later`) per attendere che tutti i valori post-evento D7S (`last_si`, `last_pga`, `last_mag`) arrivino da ESPHome prima dell'invio MQTT.
- `_build_payload()` usa sempre `last_si`/`last_pga`/`last_mag` (valori D7S mediati sull'evento, più accurati dei picchi istantanei). Rimosso `_calc_magnitude()` non più necessario.

## [1.1.1] — 2026-05-30

### Corretto
- Coordinator: `_calc_magnitude(si, pga)` — porta Python della formula firmware per calcolare l'intensità JMA da SI e PGA. Sostituisce `_peak_inst_mag` in `_build_payload()`: la magnitudine pubblicata su cloud è ora sempre coerente con SI e PGA pubblicati.

## [FW 3.6] — 2026-05-30

### Corretto
- `setup()`: `initialize()` ora attende NORMAL_MODE con loop attivo (max 10 s, WDT reset ogni 200 ms) invece di un'attesa fissa da 2 s. Il D7S necessita di completare la Initial Installation Mode per acquisire l'orientamento di riferimento del collapse; con 2 s fissi la modalità non completava → INT1 non scattava mai per collapse.

## [FW 3.5] — 2026-05-30

### Corretto
- `inst_pga`: aggiunto fattore ×10 sulla chiamata `getInstantaneusPGA()`. Il registro D7S 0x2002 ha risoluzione 0.01 m/s²/LSB mentre la libreria applica /1000 come se fosse 0.001 m/s²/LSB → valore 10× troppo piccolo rispetto a `last_pga`.
- `get_fw_version()` e `FW_VERSION = "3.5"` aggiunti a `SismasensComponent`. Il lambda ESPHome `fw_version` chiama il metodo direttamente — il valore FW è ora la costante C++ in sismasens.h, non il global `fw` EEPROM.

## [FW 3.4] — 2026-05-30

### Aggiunto
- `SismasensComponent::get_fw_version()` — espone la versione del firmware come costante C++ (`FW_VERSION = "3.4"`). Il text sensor ESPHome `fw_version` chiama `id(sismasens_component).get_fw_version()` invece del global `fw`, rendendo sismasens.h l'unica sorgente della verità per la versione.

## [FW 3.3] — 2026-05-30

### Corretto
- `magnitude()`: separati i cicli di valutazione SI e PGA; il risultato è `max(mag_si, mag_pga)`. Il bug precedente ignorava l'interpolazione decimale di PGA quando SI aveva già prodotto una frazione sullo stesso livello intero.
- Threshold D7S ripristinato a `THRESHOLD_LOW` (più sensibile).

## [FW 3.2] — 2026-05-30

### Corretto
- `doFullClear()`: sequenza reset D7S corretta secondo specifiche registro:
  - Rimossi i clear ridondanti (clearEarthquakeData/Installation/Offset/Selftest prima di clearAllData)
  - `initialize()` ora precede `acquireOffset()` (ordine corretto: prima si stabilisce l'asse di installazione, poi si acquisisce l'offset)
  - Aggiunta attesa attiva su `getState() == NORMAL_MODE` dopo `initialize()` e dopo `acquireOffset()`, con WDT reset ogni 200ms (max 6 s ciascuna)
  - Senza questa attesa il D7S tornava in NORMAL_MODE con asse non memorizzato, compromettendo il rilevamento collapse

## [FW 3.1] — 2026-05-30

### Corretto
- Bypass di `isInCollapse()` e `isInShutoff()` della libreria RAK12027-D7S: entrambe restituivano costante `1` (sempre true) per un bug nell'implementazione. Lettura diretta del registro EVENT 0x1002 via Wire (bit1=collapse, bit0=shutoff, read-clear).
- Threshold D7S: `THRESHOLD_LOW` → `THRESHOLD_HIGH` per ridurre i falsi positivi da vibrazioni meccaniche non sismiche.

## [1.1.0] — 2026-05-30

### Aggiunto
- Button "Test Cloud Publish" nel device HA: pubblica un evento di test con i valori D7S attuali senza attendere un evento sismico reale. Visibile solo se cloud è abilitato e MQTT è connesso.

### Corretto
- Coordinator: aggiunto `on_connect` callback per logging esplicito dell'esito autenticazione MQTT.

## [1.0.2] — 2026-05-30

### Aggiunto
- Button "Test Cloud Publish" nel device HA: pubblica un evento di test con i valori D7S attuali senza attendere un evento sismico reale. Visibile solo se cloud è abilitato e MQTT è connesso.

### Corretto
- Coordinator: aggiunto `on_connect` callback che logga esplicitamente l'esito dell'autenticazione MQTT (rc=0 = ok, rc≠0 = errore con codice).
- Coordinator: refactor `_publish_event` in `_build_payload` + `_publish_payload` per riuso.

## [1.0.1] — 2026-04-10

### Corretto
- Coordinator: pubblica i valori istantanei di picco (`inst_si`, `inst_pga`, `inst_mag`) misurati durante l'evento invece dei valori post-evento memorizzati dal D7S.
- HA integration: prevenire thread multipli di riconnessione MQTT se la connessione si perde più volte in rapida successione.
- HA integration: riconnessione MQTT automatica ogni 60 s in caso di errore o perdita connessione.

## [1.0.0] — 2026-03-15

### Aggiunto
- Prima release pubblica.
- Integration HA installabile via HACS.
- Supporto sensore OMRON D7S via ESPHome.
- Pubblicazione eventi sismici su broker cloud MQTT con TLS.
- Config flow a due step: device ESPHome + cloud opzionale.
- Entità sensor, binary_sensor e button.
- Coordinatore con listener state change ESPHome.
