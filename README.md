# SISMASENS — Sistema di Monitoraggio Sismico Distribuito

Sistema open source per il monitoraggio sismico basato su sensore **OMRON D7S** + **ESP32**, integrato con **Home Assistant** e connesso a una rete distribuita di sensori con dashboard pubblica in tempo reale.

---

## Architettura

```
[D7S + ESP32]  ──ESPHome──>  [Home Assistant]  ──MQTT/TLS──>  [sismasens.iotzator.com]
                              custom integration                  │
                              (entità, button,                    ├── TimescaleDB (eventi)
                               cloud publish)                     ├── API REST (FastAPI)
                                                                  ├── Broker MQTT (EMQX)
                                                                  └── Dashboard pubblica
                                                                      (mappa Leaflet RT)
```

---

## Componenti

| Cartella | Descrizione |
|---|---|
| [`hardware/`](hardware/) | Schema elettrico, BOM, pinout |
| [`esphome/`](esphome/) | Firmware ESP32 — componente ESPHome custom |
| [`homeassistant/`](homeassistant/) | Custom integration HA (riferimento — vedi `custom_components/`) |
| [`custom_components/`](custom_components/) | Integration HA installabile via HACS |
| [`backend/`](backend/) | **Submodulo** → [luckehall/sismasens-backend](https://github.com/luckehall/sismasens-backend) |

> Il backend è mantenuto in un repository separato e collegato tramite **git submodule**.
> Clona il repo con `--recurse-submodules` per ottenere anche il backend.

---

## Prerequisiti hardware

- **OMRON D7S** (o modulo breakout **RAK12027**)
- **ESP32** (es. ESP32-WROOM-32) collegato al D7S via I2C

---

## Clone

```bash
# Clone completo (repo principale + submodulo backend)
git clone --recurse-submodules https://github.com/luckehall/sismasens.git

# Se hai già clonato senza --recurse-submodules
git submodule update --init --recursive
```

---

## 1. Firmware ESP32 (ESPHome)

```bash
cp esphome/templates/sismasens-device.yaml.example esphome/templates/mio-sensore.yaml
# Edita mio-sensore.yaml con le tue credenziali Wi-Fi e coordinate
esphome run esphome/templates/mio-sensore.yaml
```

Il device apparirà in Home Assistant tramite la scoperta automatica ESPHome.  
Le entità avranno la forma `sensor.sismasens_<prefisso>_<prefisso>_earthquake`.

---

## 2. Home Assistant — Custom Integration

> **Prerequisito:** il device ESPHome deve essere già integrato in HA e le sue entità visibili prima di installare l'integrazione SISMASENS.

### Installazione via HACS (raccomandata)

1. HACS → Integrazioni → ⋮ → Repository personalizzati
2. Aggiungi `https://github.com/luckehall/sismasens` — categoria `Integration`
3. Installa **SISMASENS Seismic Monitor**
4. Riavvia HA

### Installazione manuale

```bash
cp -r custom_components/sismasens /config/custom_components/sismasens
# Riavvia Home Assistant
```

### Configurazione

1. **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → SISMASENS**
2. Inserisci il **prefisso device** (es. `mi-001`) — deve corrispondere al nome ESPHome (`sismasens-mi-001`)
3. (Opzionale) Abilita la **pubblicazione cloud**:
   - Ottieni il token MQTT su [sismasens.iotzator.com/setup](https://sismasens.iotzator.com/setup)
   - Inserisci token, latitudine e longitudine

### Entità create dall'integrazione

| Entità | Tipo | Descrizione |
|---|---|---|
| `binary_sensor.sismasens_*_earthquake` | Binary | Terremoto in corso |
| `binary_sensor.sismasens_*_collapse` | Binary | Collapse rilevato |
| `binary_sensor.sismasens_*_shutoff` | Binary | Shutoff rilevato |
| `sensor.sismasens_*_last_si` | Sensor | Ultimo SI post-evento (cm/s) |
| `sensor.sismasens_*_last_pga` | Sensor | Ultimo PGA post-evento (g) |
| `sensor.sismasens_*_last_temp` | Sensor | Temperatura sensore (°C) |
| `sensor.sismasens_*_last_m` | Sensor | Ultima magnitudine |
| `sensor.sismasens_*_inst_si` | Sensor | SI istantaneo (durante evento) |
| `sensor.sismasens_*_inst_pga` | Sensor | PGA istantaneo |
| `sensor.sismasens_*_inst_m` | Sensor | Magnitudine istantanea |
| `button.sismasens_*_clear_sensor` | Button | Azzera memoria D7S |
| `button.sismasens_*_set` | Button | Hard reset D7S |
| `button.sismasens_*_reboot` | Button | Riavvia ESP32 |

---

## 3. Backend cloud (VPS)

Il backend è ospitato nel submodulo `backend/` ([luckehall/sismasens-backend](https://github.com/luckehall/sismasens-backend)).  
Documentazione completa: vedi [`backend/README.md`](backend/README.md).

Il backend richiede un VPS con **Ubuntu 22.04**, **Apache2** e **Certbot** già installati.

### Primo deploy

```bash
git clone --recurse-submodules https://github.com/luckehall/sismasens /opt/sismasens
sudo bash /opt/sismasens/backend/deploy.sh
# → installa Docker, crea .env da .env.example, si ferma

nano /opt/sismasens/backend/.env   # inserisci password reali

sudo bash /opt/sismasens/backend/deploy.sh --start
# → ottiene certificato TLS, configura Apache, avvia container
```

### Aggiornamento

```bash
cd /opt/sismasens && git pull origin main
git submodule update --remote --merge
cd backend && docker compose up -d --build
```

---

## 4. Registrazione sensore (cloud)

Apri [sismasens.iotzator.com/setup](https://sismasens.iotzator.com/setup):

1. Crea un account (email + password, opzionale 2FA TOTP, oppure **Accedi con Google**)
2. Inserisci i dati del sensore (ID, nome, posizione)
3. Clicca sulla mappa per impostare le coordinate
4. Clicca **Registra** → ottieni il token MQTT
5. Incolla il token in HA: Impostazioni → SISMASENS → Configura → Token MQTT

Dalla stessa pagina puoi **revocare**, **riattivare** o **eliminare** i sensori registrati, e rigenerare il token MQTT.

---

## 5. API REST

Documentazione interattiva disponibile su `https://sismasens.iotzator.com/api/docs`.

### Endpoints principali

| Metodo | Path | Auth | Descrizione |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Crea account utente |
| `POST` | `/api/auth/login` | — | Login → JWT access token (o temp\_token se 2FA attivo) |
| `POST` | `/api/auth/2fa/verify` | temp\_token | Completa login con codice TOTP |
| `POST` | `/api/auth/google` | — | Login/registrazione via Google OAuth |
| `POST` | `/api/auth/2fa/setup` | Bearer | Genera secret TOTP e QR URI |
| `POST` | `/api/auth/2fa/enable` | Bearer | Abilita 2FA (verifica primo codice) |
| `POST` | `/api/auth/2fa/disable` | Bearer | Disabilita 2FA |
| `POST` | `/api/sensors/` | Bearer | Registra sensore |
| `POST` | `/api/sensors/{id}/token` | Bearer | Genera/rigenera token MQTT |
| `PATCH` | `/api/sensors/{id}/active` | Bearer | Revoca/riattiva sensore |
| `DELETE` | `/api/sensors/{id}` | Bearer | Elimina sensore |
| `GET` | `/api/sensors/public` | — | Lista sensori attivi (pubblica) |
| `GET` | `/api/events/recent` | — | Ultimi 20 eventi (pubblica) |
| `WS` | `/events/ws` | — | Stream eventi in real-time |
| `GET` | `/api/health` | — | Health check |

---

## Workflow submodulo backend

**Modificare il backend:**
```bash
cd /Users/lsala/Repo/sismasens-backend   # lavora nel repo backend
git commit && git push origin main

cd /Users/lsala/Repo/sismasens           # aggiorna il puntatore nel repo principale
git -C backend pull origin main
git add backend && git commit -m "chore: bump backend submodule"
git push origin main
```

**Deploy VPS:**
```bash
ssh sismasens "cd /opt/sismasens && git pull origin main && git submodule update --remote --merge && cd backend && docker compose up -d --build"
```

---

## Flusso dati

```
Sensore D7S rileva scossa
        │
        ▼
ESP32 aggiorna entità ESPHome
        │
        ▼
HA coordinator SISMASENS rileva transizione earthquake → 0
        │
        ▼
Pubblica JSON su MQTT: sismasens/events/{sensor_id}
        │   (EMQX su sismasens.iotzator.com:8883, autenticato con JWT)
        ▼
Ingestor scrive in TimescaleDB (tabella seismic_events)
        │
        ├──▶ Broadcast WebSocket ai client dashboard
        └──▶ Dashboard mostra marker sulla mappa
```

---

## Changelog

### v3.2.0 (corrente)
- Autenticazione utente: registrazione email+password con **2FA TOTP** opzionale
- **Login con Google** (OAuth 2.0 / OIDC) — piattaforma
- Gestione sensori nella dashboard: revoca, riattivazione, eliminazione, rinnovo token MQTT
- Backend estratto in repo privato separato ([luckehall/sismasens-backend](https://github.com/luckehall/sismasens-backend)) e collegato come **git submodule**
- HACS: `hacs.json` + `custom_components/` al root del repo per installazione diretta

### v3.1.0
- Pagina `/setup` per registrazione utente+sensore con mappa cliccabile
- Fix autenticazione EMQX: JWT per ingestor, placeholder `${username}` ACL (EMQX 5.x)
- Fix coordinator HA: MQTT username = prefisso originale (non normalizzato)
- Broadcast WebSocket real-time eventi alla dashboard
- Fix dashboard: leaflet CSS, vite.config.js, VITE_API_BASE, formattazione date

### v3.0.0
- Monorepo open source
- Custom integration Home Assistant con config flow e pubblicazione cloud
- Backend FastAPI + TimescaleDB + EMQX + dashboard Leaflet
- Deploy su VPS Apache2 con `deploy.sh`

### v2.5
- Versione originale ESPHome custom component

---

## Licenza

MIT — Vedi [LICENSE](LICENSE)
