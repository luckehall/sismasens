# Changelog

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
