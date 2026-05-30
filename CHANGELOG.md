# Changelog

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
