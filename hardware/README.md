# SISMASENS — Hardware

Questa cartella contiene i file per replicare l'hardware del sensore sismico SISMASENS.

## Componenti principali

| Componente | Descrizione |
|---|---|
| **OMRON D7S** | Sensore sismico MEMS dedicato. Calcola internamente SI (Spectral Intensity) e PGA (Peak Ground Acceleration). Interfaccia I2C. |
| **ESP32** | Microcontrollore principale (es. ESP32-WROOM-32). |
| **RAK12027** | Modulo breakout per D7S (opzionale, semplifica il collegamento). |

## Pinout ESP32

| GPIO | Funzione |
|------|----------|
| GPIO21 | SDA (I2C) |
| GPIO22 | SCL (I2C) |
| GPIO25 | SET — hard reset D7S (output) |
| GPIO32 | INT2 — interrupt earthquake (input, pull-up) |
| GPIO33 | INT1 — interrupt collapse/shutoff (input, pull-up) |
| GPIO35 | Monitor tensione alimentazione (ADC, input-only) |
| GPIO26 | RESET backup (input, pull-down) |
| GPIO27 | Jumper fisico clear (collegare a GPIO26 per clear manuale) |
| GPIO2  | LED status |

## Schema di collegamento D7S → ESP32

```
D7S / RAK12027        ESP32
─────────────────────────���───
VCC (3.3V)    ──────  3.3V
GND           ──────  GND
SDA           ──────  GPIO21
SCL           ──────  GPIO22
INT1          ──────  GPIO33
INT2          ──────  GPIO32
SET           ──────  GPIO25  (tramite resistenza 1kΩ)
```

## File

- `schematics/` — Schema elettrico (KiCad / EasyEDA)
- `pcb/` — File Gerber per produzione PCB
- `bom/` — Bill of Materials

> I file di progetto hardware verranno aggiunti nelle prossime versioni.
