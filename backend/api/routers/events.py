"""Router eventi sismici: lettura pubblica + WebSocket real-time."""
import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models.event import SeismicEvent

router = APIRouter(prefix="/events", tags=["events"])

# Registry WebSocket attivi per broadcast
_ws_clients: list[WebSocket] = []


async def broadcast_event(event_data: dict[str, Any]) -> None:
    """Invia un evento a tutti i client WebSocket connessi."""
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_text(json.dumps(event_data))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


@router.get("/recent")
async def get_recent_events(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SeismicEvent)
        .order_by(desc(SeismicEvent.time))
        .limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "time": e.time.isoformat(),
            "sensor_id": e.sensor_id,
            "lat": e.lat,
            "lon": e.lon,
            "location": e.location,
            "si": e.si,
            "pga": e.pga,
            "magnitude": e.magnitude,
            "temp": e.temp,
            "collapse": e.collapse,
            "shutoff": e.shutoff,
        }
        for e in events
    ]


@router.get("/")
async def get_events(
    sensor_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(SeismicEvent).order_by(desc(SeismicEvent.time)).limit(limit)
    if sensor_id:
        query = query.where(SeismicEvent.sensor_id == sensor_id)

    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "time": e.time.isoformat(),
            "sensor_id": e.sensor_id,
            "lat": e.lat,
            "lon": e.lon,
            "location": e.location,
            "magnitude": e.magnitude,
            "si": e.si,
            "pga": e.pga,
        }
        for e in events
    ]


@router.websocket("/ws")
async def websocket_events(websocket: WebSocket):
    """Stream eventi in real-time verso la dashboard."""
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            # Mantieni la connessione viva con ping
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
