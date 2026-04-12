"""Costanti per l'integrazione SISMASENS."""

DOMAIN = "sismasens"
VERSION = "1.0.0"

# Config entry keys
CONF_DEVICE_PREFIX = "device_prefix"
CONF_CLOUD_TOKEN = "cloud_token"
CONF_CLOUD_ENABLED = "cloud_enabled"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

# MQTT cloud
CLOUD_BROKER = "sismasens.iotzator.com"
CLOUD_PORT = 8883  # MQTT over TLS
CLOUD_TOPIC_EVENTS = "sismasens/events/{sensor_id}"

# Entity ID delle entità ESPHome generate in HA.
# Il device ESPHome si chiama "sismasens-{prefix}" e le entità
# si chiamano "{PREFIX} *", quindi l'entity_id HA risultante è:
#   {domain}.sismasens_{prefix}_{prefix}_{suffix}
# es. prefix="mi-001" → norm="mi_001"
#   sensor.sismasens_mi_001_mi_001_earthquake  (sensor numerico 0/1, non binary_sensor)
ESPHOME_ENTITIES = {
    # Sensori numerici 0/1 — earthquake/collapse/shutoff sono sensor::Sensor in ESPHome
    "earthquake":     "sensor.sismasens_{prefix}_{prefix}_earthquake",
    "collapse":       "sensor.sismasens_{prefix}_{prefix}_collapse",
    "shutoff":        "sensor.sismasens_{prefix}_{prefix}_shutoff",
    # Sensori numerici — valori post-evento
    "last_si":        "sensor.sismasens_{prefix}_{prefix}_last_si",
    "last_pga":       "sensor.sismasens_{prefix}_{prefix}_last_pga",
    "last_temp":      "sensor.sismasens_{prefix}_{prefix}_last_temp",
    "last_mag":       "sensor.sismasens_{prefix}_{prefix}_last_m",
    # Sensori numerici — valori istantanei (durante evento)
    "inst_si":        "sensor.sismasens_{prefix}_{prefix}_inst_si",
    "inst_pga":       "sensor.sismasens_{prefix}_{prefix}_inst_pga",
    "inst_mag":       "sensor.sismasens_{prefix}_{prefix}_inst_m",
    # Text sensor — timestamp ultimo terremoto (typo "eartquake" è del firmware D7S, intenzionale)
    "last_eartquake": "sensor.sismasens_{prefix}_{prefix}_last_eartquake",
    # Text sensors — info dispositivo
    "location":       "sensor.sismasens_{prefix}_{prefix}_location",
    "fw_version":     "sensor.sismasens_{prefix}_{prefix}_fw_version",
    "power_supply":   "sensor.sismasens_{prefix}_{prefix}_power_supply",
}

# Entity ID dei button ESPHome
ESPHOME_BUTTONS = {
    "clear_sensor": "button.sismasens_{prefix}_{prefix}_clear_sensor",
    "set":          "button.sismasens_{prefix}_{prefix}_set",
    "reboot":       "button.sismasens_{prefix}_{prefix}_reboot",
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
