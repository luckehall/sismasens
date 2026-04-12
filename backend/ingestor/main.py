"""SISMASENS Ingestor — Subscriber MQTT → TimescaleDB.

Ascolta il topic sismasens/events/# e scrive ogni evento nel DB.
"""
import asyncio
import json
import logging
import os
import re
import ssl
from datetime import datetime, timezone

import asyncpg
import paho.mqtt.client as mqtt
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger("ingestor")

BROKER_HOST = os.getenv("MQTT_BROKER", "emqx")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
BROKER_USER = os.getenv("MQTT_INGESTOR_USER", "ingestor")
BROKER_PASS = os.getenv("MQTT_INGESTOR_PASS", "change-me")
DB_DSN = os.getenv("DATABASE_URL", "postgresql://sismasens:sismasens@postgres:5432/sismasens")
TOPIC = "sismasens/events/#"


class EventPayload(BaseModel):
    sensor_id: str
    timestamp: str
    lat: float | None = None
    lon: float | None = None
    location: str = ""
    si: float = 0.0
    pga: float = 0.0
    magnitude: float = 0.0
    temp: float = 0.0
    collapse: bool = False
    shutoff: bool = False


# Coda thread-safe tra callback MQTT (thread) e loop asyncio
_queue: asyncio.Queue = asyncio.Queue()
_loop: asyncio.AbstractEventLoop | None = None


def _on_message(client, userdata, msg):
    try:
        raw = json.loads(msg.payload.decode())
        payload = EventPayload(**raw)

        # Sicurezza: sensor_id nel topic deve corrispondere al payload
        topic_parts = msg.topic.split("/")
        if len(topic_parts) >= 3:
            topic_sensor_id = topic_parts[2]
            if topic_sensor_id != payload.sensor_id:
                _LOGGER.warning(
                    "sensor_id mismatch: topic=%s payload=%s — scartato",
                    topic_sensor_id,
                    payload.sensor_id,
                )
                return

        if _loop:
            _loop.call_soon_threadsafe(_queue.put_nowait, payload)
    except (ValidationError, json.JSONDecodeError) as e:
        _LOGGER.warning("Payload non valido: %s — %s", msg.payload, e)


async def write_event(pool: asyncpg.Pool, event: EventPayload) -> None:
    try:
        ts = datetime.fromisoformat(event.timestamp)
    except (ValueError, TypeError):
        ts = datetime.now(timezone.utc)

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO seismic_events
              (time, sensor_id, lat, lon, location, si, pga, magnitude, temp, collapse, shutoff)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT DO NOTHING
            """,
            ts, event.sensor_id, event.lat, event.lon, event.location,
            event.si, event.pga, event.magnitude, event.temp,
            event.collapse, event.shutoff,
        )
    _LOGGER.info("Evento scritto: %s mag=%.2f", event.sensor_id, event.magnitude)

    # Broadcast WebSocket via HTTP interno all'API
    try:
        import httpx
        async with httpx.AsyncClient() as http:
            await http.post(
                "http://api:8000/events/internal/broadcast",
                json=event.dict(),
                timeout=2,
            )
    except Exception:
        pass  # Non critico


async def consume(pool: asyncpg.Pool) -> None:
    while True:
        event = await _queue.get()
        await write_event(pool, event)


async def main() -> None:
    global _loop
    _loop = asyncio.get_running_loop()

    pool = await asyncpg.create_pool(DB_DSN, min_size=2, max_size=5)

    client = mqtt.Client(client_id="sismasens-ingestor")
    client.username_pw_set(BROKER_USER, BROKER_PASS)
    client.on_message = _on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.subscribe(TOPIC, qos=1)
    client.loop_start()

    _LOGGER.info("Ingestor avviato — in ascolto su %s:%d %s", BROKER_HOST, BROKER_PORT, TOPIC)
    await consume(pool)


if __name__ == "__main__":
    asyncio.run(main())
