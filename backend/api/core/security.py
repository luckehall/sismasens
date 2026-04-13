"""Utilità JWT, hashing password e TOTP."""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import pyotp
from jose import jwt

from .config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "type": "access"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_temp_token(user_id: int) -> str:
    """Token temporaneo (5 min) emesso dopo password OK se 2FA è attivo.
    Usato come input per POST /auth/2fa/verify.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "2fa_pending"},
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


# ── TOTP ──────────────────────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="SISMASENS")


def verify_totp(secret: str, code: str) -> bool:
    """Verifica il codice TOTP con finestra ±1 step (tolleranza orologio 30s)."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)
