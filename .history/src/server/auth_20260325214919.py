from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "ANTIGRAVITY_SYNC_SECRET_KEY")
if SECRET_KEY == "ANTIGRAVITY_SYNC_SECRET_KEY":
    # WARNING: Use environment variable SECRET_KEY in production.
    # This fallback is only for local/dev convenience.
    print("[WARNING] SECRET_KEY está no valor padrão; defina SECRET_KEY no ambiente para produção.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 semana

ph = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
