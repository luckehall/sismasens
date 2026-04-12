"""Modello evento sismico (hypertable TimescaleDB)."""
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class SeismicEvent(Base):
    """Hypertable TimescaleDB — partizionata per time."""
    __tablename__ = "seismic_events"

    # TimescaleDB richiede che la colonna time sia parte della PK
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    sensor_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)

    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lon: Mapped[float] = mapped_column(Float, nullable=True)
    location: Mapped[str] = mapped_column(String(256), nullable=True)

    si: Mapped[float] = mapped_column(Float, nullable=True)
    pga: Mapped[float] = mapped_column(Float, nullable=True)
    magnitude: Mapped[float] = mapped_column(Float, nullable=True)
    temp: Mapped[float] = mapped_column(Float, nullable=True)
    collapse: Mapped[bool] = mapped_column(Boolean, default=False)
    shutoff: Mapped[bool] = mapped_column(Boolean, default=False)
