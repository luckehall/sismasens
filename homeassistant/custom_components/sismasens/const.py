"""Costanti per l'integrazione SISMASENS."""

DOMAIN = "sismasens"
VERSION = "1.0.0"

# Config entry keys
CONF_DEVICE_PREFIX = "device_prefix"
CONF_CLOUD_TOKEN = "cloud_token"
CONF_CLOUD_ENABLED = "cloud_enabled"

# MQTT cloud
CLOUD_BROKER = "sismasens.iotzator.com"
CLOUD_PORT = 8883  # MQTT over TLS
CLOUD_TOPIC_EVENTS = "sismasens/events/{sensor_id}"

# Suffissi entità ESPHome attese (relative al device_prefix)
# es. device_prefix="mi-001" → entity "sensor.mi_001_earthquake"
ESPHOME_ENTITIES = {
    "earthquake": "sensor.{prefix}_earthquake",
    "collapse":   "sensor.{prefix}_collapse",
    "shutoff":    "sensor.{prefix}_shutoff",
    "last_si":    "sensor.{prefix}_last_si",
    "last_pga":   "sensor.{prefix}_last_pga",
    "last_temp":  "sensor.{prefix}_last_temp",
    "last_mag":   "sensor.{prefix}_last_m",
    "inst_si":    "sensor.{prefix}_inst_si",
    "inst_pga":   "sensor.{prefix}_inst_pga",
    "inst_mag":   "sensor.{prefix}_inst_m",
    "gps":        "sensor.{prefix}_gps",
    "location":   "sensor.{prefix}_location",
}

# Soglie magnitudine per classificazione
MAGNITUDE_LEVELS = {
    "minimal":  (0.0, 1.0),
    "minor":    (1.0, 2.5),
    "light":    (2.5, 4.0),
    "moderate": (4.0, 5.5),
    "strong":   (5.5, 7.0),
    "major":    (7.0, 99.0),
}
