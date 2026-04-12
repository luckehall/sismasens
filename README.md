# SISMASENS — Sistema di Monitoraggio Sismico Distribuito

Sistema open source per il monitoraggio sismico basato su sensore **OMRON D7S** + **ESP32**, integrato con **Home Assistant** e connesso a una rete distribuita di sensori con dashboard pubblica in tempo reale.

---

## Architettura

```
[D7S + ESP32]  ──ESPHome──>  [Home Assistant]  ──MQTT/TLS──>  [sismasens.iotzator.com]
                              custom integration                  │
                              (entità, button,                    ├── TimescaleDB
                               cloud publish)                     ├── API REST
                                                                  └── Dashboard pubblica
                                                                      (mappa Leaflet)
```

---

## Prerequisiti

### Hardware
- **OMRON D7S** (o modulo breakout **RAK12027**)
- **ESP32** (es. ESP32-WROOM-32) collegato al D7S via I2C

### Software — obbligatori prima di installare l'integrazione HA
L'integrazione SISMASENS per Home Assistant **non comunica direttamente con l'ESP32**.
Legge le entità già create dall'integrazione ESPHome standard in HA ("approccio layered").

Per questo motivo è necessario, nell'ordine:

1. **Flashare il firmware ESPHome** sul device con il componente `sismasens`
   (vedi [`esphome/`](esphome/) e la sezione *Installazione rapida* qui sotto)
2. **Integrare il device in Home Assistant** tramite l'integrazione ESPHome standard
   (HA scopre automaticamente i device ESPHome sulla rete locale)
3. **Verificare che le entità ESPHome siano presenti** in HA —
   devono comparire entità come `binary_sensor.sismasens_<prefisso>_<prefisso>_earthquake`
   prima di poter configurare l'integrazione SISMASENS

Solo a questo punto l'installazione dell'integrazione SISMASENS avrà successo.
Il prefisso da inserire nel config flow (es. `mi-001`) deve corrispondere
al nome del device ESPHome (`sismasens-mi-001`).

---

## Componenti

| Cartella | Descrizione |
|---|---|
| [`hardware/`](hardware/) | Schema elettrico, BOM, pinout |
| [`esphome/`](esphome/) | Firmware ESP32 — componente ESPHome custom |
| [`homeassistant/`](homeassistant/) | Custom integration HA (installabile via HACS) |
| [`backend/`](backend/) | API FastAPI, broker MQTT EMQX, dashboard React, Docker Compose |

---

## Installazione rapida

### 1. Firmware ESP32 (ESPHome)

```bash
cp esphome/templates/sismasens-device.yaml.example esphome/templates/mio-sensore.yaml
# Edita mio-sensore.yaml con le tue coordinate e credenziali
esphome run esphome/templates/mio-sensore.yaml
```

### 2. Home Assistant — Custom Integration

> **Prerequisito:** il device ESPHome deve essere già integrato in HA e le sue entità
> devono essere visibili prima di procedere. Vedi la sezione [Prerequisiti](#prerequisiti).

**Via HACS (raccomandato):**
1. Apri HACS → Integrazioni → Menu ⋮ → Repository personalizzati
2. Aggiungi `https://github.com/luckehall/sismasens` — categoria `Integration`
3. Installa "SISMASENS Seismic Monitor"
4. Riavvia HA → Impostazioni → Integrazioni → Aggiungi → SISMASENS

**Manuale:**
```bash
cp -r homeassistant/custom_components/sismasens \
      /config/custom_components/sismasens
# Riavvia Home Assistant
```

**Setup:**
1. Inserisci il prefisso del device ESPHome (es. `mi-001`) — deve corrispondere al nome del device (`sismasens-mi-001`)
2. (Opzionale) Inserisci latitudine, longitudine e token MQTT ottenuto su [sismasens.iotzator.com](https://sismasens.iotzator.com/register)

### 3. Backend (VPS)

```bash
cd backend
cp .env.example .env
# Edita .env con le tue password
docker compose up -d
```

**Primo avvio TLS:**
```bash
docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot -d sismasens.iotzator.com \
  --email tua@email.com --agree-tos
docker compose restart nginx
```

---

## Registrazione sensore (cloud)

1. Registrati su [sismasens.iotzator.com/register](https://sismasens.iotzator.com/register)
2. Crea il tuo sensore con coordinate geografiche
3. Ottieni il token MQTT
4. Inserisci il token nella configurazione dell'integrazione HA

---

## Entità Home Assistant create

| Entità | Tipo | Descrizione |
|---|---|---|
| `binary_sensor.sismasens_*_earthquake` | Binary | Terremoto in corso |
| `binary_sensor.sismasens_*_collapse` | Binary | Collapse rilevato |
| `binary_sensor.sismasens_*_shutoff` | Binary | Shutoff rilevato |
| `sensor.sismasens_*_last_si` | Sensor | Ultimo SI (cm/s) |
| `sensor.sismasens_*_last_pga` | Sensor | Ultimo PGA (g) |
| `sensor.sismasens_*_last_temp` | Sensor | Temperatura sensore (°C) |
| `sensor.sismasens_*_last_m` | Sensor | Ultima magnitudine |
| `sensor.sismasens_*_inst_si` | Sensor | SI istantaneo |
| `sensor.sismasens_*_inst_pga` | Sensor | PGA istantaneo |
| `sensor.sismasens_*_inst_m` | Sensor | Magnitudine istantanea |
| `button.sismasens_*_clear_sensor` | Button | Azzera memoria D7S |
| `button.sismasens_*_set` | Button | Hard reset D7S |
| `button.sismasens_*_reboot` | Button | Riavvia ESP32 |

---

## Changelog

### v3.0.0
- Monorepo open source
- Custom integration Home Assistant con config flow e pubblicazione cloud
- Backend FastAPI + TimescaleDB + EMQX
- Dashboard pubblica con mappa Leaflet
- **Bugfix PGA**: la libreria RAK12027 restituisce PGA in kGal (registro in Gal / 1000);
  divisore corretto `/ 0.980665` (1g = 0.980665 kGal) per ottenere il valore in g

### v2.5
- Versione originale ESPHome custom component

---

## Licenza

MIT — Vedi [LICENSE](LICENSE)
