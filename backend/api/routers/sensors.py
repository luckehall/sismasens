"""Router sensori: registrazione, profilo e generazione token MQTT."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.security import create_mqtt_token, hash_password
from ..models.sensor import Sensor
from ..models.user import User

router = APIRouter(prefix="/sensors", tags=["sensors"])


class SensorCreate(BaseModel):
    sensor_id: str  # es. "mi-001"
    name: str
    location: str
    lat: float
    lon: float


class SensorResponse(BaseModel):
    sensor_id: str
    name: str
    location: str
    lat: float
    lon: float
    active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def register_sensor(
    body: SensorCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Sensor).where(Sensor.sensor_id == body.sensor_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="sensor_id già registrato")

    sensor = Sensor(
        user_id=user.id,
        sensor_id=body.sensor_id,
        name=body.name,
        location=body.location,
        lat=body.lat,
        lon=body.lon,
    )
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)
    return sensor


@router.get("/", response_model=list[SensorResponse])
async def list_sensors(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Sensor).where(Sensor.user_id == user.id))
    return result.scalars().all()


@router.post("/{sensor_id}/token")
async def generate_mqtt_token(
    sensor_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Genera (o rigenera) il token MQTT per il sensore."""
    result = await db.execute(
        select(Sensor).where(Sensor.sensor_id == sensor_id, Sensor.user_id == user.id)
    )
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensore non trovato")

    token = create_mqtt_token(sensor_id)
    sensor.mqtt_token_hash = hash_password(token)  # conserva solo l'hash
    await db.commit()

    return {"mqtt_token": token, "sensor_id": sensor_id}


@router.get("/public", response_model=list[SensorResponse])
async def list_public_sensors(db: AsyncSession = Depends(get_db)):
    """Lista sensori attivi (pubblica, per la dashboard)."""
    result = await db.execute(select(Sensor).where(Sensor.active == True))
    return result.scalars().all()
