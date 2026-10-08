# SISMASENS — Claude Code context

## Progetto

Sistema open source per **monitoraggio sismico distribuito**.
Sensore OMRON D7S + ESP32 → ESPHome → Home Assistant → cloud (sismasens.iotzator.com).

## Architettura

```
[D7S + ESP32]  ──ESPHome──>  [Home Assistant]  ──MQTT/TLS──>  [sismasens.iotzator.com]
                              custom integration                  ├── TimescaleDB
                              (entità, button, cloud publish)     ├── API REST (FastAPI)
                                                                  ├── Broker MQTT (EMQX 5)
                                                                  └── Dashboard Leaflet RT
```

## Struttura repo

```
sismasens/                      ← repo principale
├── hardware/                   # schema elettrico, BOM, pinout
├── esphome/                    # firmware ESP32 (componente ESPHome custom)
├── homeassistant/              # riferimento integration HA
├── custom_components/sismasens/ # integration HA installabile via HACS
└── backend/                    # git submodule → luckehall/sismasens-backend
```

## Repo `sismasens-backend` (submodulo)

Stack: FastAPI 3.11 + PostgreSQL 15 + TimescaleDB + EMQX 5 + React/Vite + Apache2 + Docker Compose.

```
backend/
├── api/         # FastAPI (auth, sensors, events, WebSocket)
├── ingestor/    # subscriber MQTT → TimescaleDB
├── dashboard/   # React + Leaflet (mappa sensori RT)
├── broker/      # config EMQX
└── docker-compose.yml
```

## Comandi utili

```bash
# Clone completo con submodulo
git clone --recurse-submodules https://github.com/luckehall/sismasens.git

# Aggiorna submodulo backend
git submodule update --remote backend

# Deploy backend (VPS)
cd backend && docker compose up -d
```

## Versione corrente

**FW 4.1.1** — collapse software in tempo reale su SI istantaneo > 10 cm/s

## Note sviluppo

- `backend/` è un **git submodule** privato: modifiche vanno committate *prima* nel repo `sismasens-backend`, poi aggiornato il puntatore in `sismasens`
- L'integration HACS è in `custom_components/sismasens/` — stessa struttura di qualsiasi custom component HA
- La comunicazione cloud avviene via MQTT con TLS — il broker è EMQX su VPS
- TimescaleDB per le serie temporali degli eventi sismici (hypertable su `timestamp`)

## Da verificare alla prossima revisione

**Riconnessioni a raffica del client `ha-sismasens-mc_001` (utente `mc-001`, IP 151.58.247.6) verso EMQX** — osservato il 2026-10-08 sul VPS `pkm-vps`: circa 6.000 socket in `TIME_WAIT` sulla porta 8883 da quell'unico IP, `beam.smp` di `sismasens-emqx` a ~135-150% di CPU a broker quasi inattivo (solo 3 client MQTT connessi), causa probabile degli intermittenti "worker non raggiungibile" di PKM sullo stesso VPS.

- Causa non ancora accertata. Ipotesi: due istanze HA con lo stesso `client_id` che si espellono a vicenda (takeover in loop), credenziali/certificato rifiutati con retry senza pausa, oppure reconnect senza backoff nell'integrazione `custom_components/sismasens/`. Controllare il log MQTT dell'istanza HA di `mc-001`.
- Mitigazione applicata a mano solo a runtime (`emqx ctl conf load`, nel volume dati di EMQX, NON nel repo): `flapping_detect` attivo (`max_count=15`, `window_time=1m`, `ban_time=5m`) — CPU scesa a ~6%. Conseguenza: il client resta bloccato 5 minuti alla volta finché non si corregge la causa, quindi quel sensore non è di fatto collegato.
- Da fare: correggere la causa nell'integrazione/istanza HA; poi riportare `flapping_detect` nella configurazione versionata del broker in `backend/` (es. `EMQX_FLAPPING_DETECT__ENABLE=true` nel compose) così sopravvive a un ricreato da zero del container, e decidere se tenerlo permanentemente.
