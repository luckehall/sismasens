"""Router autenticazione: registrazione, login e gestione 2FA."""
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.security import (
    hash_password, verify_password,
    create_access_token, create_temp_token, decode_token,
    generate_totp_secret, get_totp_uri, verify_totp,
)
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemi ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Login può richiedere un secondo fattore."""
    access_token: str | None = None
    token_type: str = "bearer"
    requires_2fa: bool = False
    temp_token: str | None = None


class TwoFactorVerifyRequest(BaseModel):
    temp_token: str
    code: str


class TwoFactorEnableRequest(BaseModel):
    code: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password troppo corta (min 8 caratteri)")

    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email già registrata")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    return {"message": "Registrazione completata"}


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    if user.totp_enabled:
        # Password OK ma 2FA richiesto: emetti temp_token (5 min)
        return LoginResponse(requires_2fa=True, temp_token=create_temp_token(user.id))

    return LoginResponse(access_token=create_access_token(user.id))


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_2fa(body: TwoFactorVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Seconda fase login: verifica TOTP e restituisce access_token."""
    try:
        payload = decode_token(body.temp_token)
        if payload.get("type") != "2fa_pending":
            raise ValueError("wrong token type")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token temporaneo non valido o scaduto")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=401, detail="2FA non attivo per questo utente")

    if not verify_totp(user.totp_secret, body.code):
        raise HTTPException(status_code=401, detail="Codice 2FA non valido")

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/2fa/setup")
async def setup_2fa(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Genera un nuovo secret TOTP e restituisce URI per QR code.
    Non abilita ancora il 2FA: serve /2fa/enable per attivarlo.
    """
    secret = generate_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = False  # attivato solo dopo verifica
    await db.commit()

    return {
        "secret": secret,
        "uri": get_totp_uri(secret, user.email),
    }


@router.post("/2fa/enable")
async def enable_2fa(
    body: TwoFactorEnableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verifica il codice TOTP e abilita il 2FA sull'account."""
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="Chiama prima /auth/2fa/setup")

    if not verify_totp(user.totp_secret, body.code):
        raise HTTPException(status_code=400, detail="Codice non valido")

    user.totp_enabled = True
    await db.commit()
    return {"message": "2FA attivato"}


@router.post("/2fa/disable")
async def disable_2fa(
    body: TwoFactorEnableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disabilita il 2FA (richiede conferma con codice TOTP corrente)."""
    if not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA non attivo")

    if not verify_totp(user.totp_secret, body.code):
        raise HTTPException(status_code=400, detail="Codice non valido")

    user.totp_enabled = False
    user.totp_secret = None
    await db.commit()
    return {"message": "2FA disattivato"}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    """Info account dell'utente autenticato."""
    return {
        "id": user.id,
        "email": user.email,
        "totp_enabled": user.totp_enabled,
    }
