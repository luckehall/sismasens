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
