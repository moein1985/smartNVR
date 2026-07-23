import logging
import time
from typing import Any

import jwt
import bcrypt

logger = logging.getLogger(__name__)

_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_SECONDS = 86400
_JWT_SECRET = "frigate-intelligence-secret-key-change-in-production"


class AuthService:
    def __init__(
        self,
        secret: str = _JWT_SECRET,
        expiry_seconds: int = _JWT_EXPIRY_SECONDS,
    ) -> None:
        self._secret = secret
        self._expiry_seconds = expiry_seconds

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception as e:
            logger.error(
                "[Auth] Password verification failed: %s",
                e,
                exc_info=True,
            )
            return False

    def create_token(self, user_id: str, username: str, role: str) -> str:
        payload: dict[str, Any] = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": int(time.time()) + self._expiry_seconds,
            "iat": int(time.time()),
        }
        token = jwt.encode(payload, self._secret, algorithm=_JWT_ALGORITHM)
        logger.info("[Auth] Created token for user '%s' (role=%s)", username, role)
        return token

    def decode_token(self, token: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[_JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("[Auth] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("[Auth] Invalid token: %s", e)
            return None
