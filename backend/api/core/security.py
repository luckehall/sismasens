"""Utilità JWT e hashing password."""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from .config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(subject), "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_mqtt_token(sensor_id: str) -> str:
    """Genera un token MQTT per l'autenticazione al broker EMQX.
    Non scade (o scade dopo 10 anni) — l'utente può rigenerarlo.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=3650)
    return jwt.encode(
        {
            "sub": sensor_id,
            "exp": expire,
            "type": "mqtt",
        },
        settings.mqtt_token_secret,
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
