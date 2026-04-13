"""SISMASENS Backend API — FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .core.config import settings
from .core.database import engine, Base
from .routers import auth, sensors, events


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea le tabelle al primo avvio
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Converti seismic_events in hypertable TimescaleDB (idempotente)
        await conn.execute(text(
            "SELECT create_hypertable('seismic_events', 'time', if_not_exists => TRUE);"
        ))
        # Migrazione idempotente: aggiunge colonne 2FA se non esistono
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64);"
        ))
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT FALSE;"
        ))
        # Migrazione idempotente: Google OAuth
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(128);"
        ))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id) WHERE google_id IS NOT NULL;"
        ))
        await conn.execute(text(
            "ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;"
        ))
    yield


app = FastAPI(
    title="SISMASENS API",
    version="1.0.0",
    description="Backend per il sistema di monitoraggio sismico distribuito SISMASENS.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sensors.router)
app.include_router(events.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
