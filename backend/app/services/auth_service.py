import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import ConflictError, UnauthorizedError
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.config import settings


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: RegisterRequest) -> AuthResponse:
        if self.db.query(User).filter(User.email == data.email).first():
            raise ConflictError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._issue_tokens(user)

    def login(self, data: LoginRequest) -> AuthResponse:
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        return self._issue_tokens(user)

    def refresh(self, raw_refresh_token: str) -> AuthResponse:
        try:
            payload = decode_token(raw_refresh_token)
        except Exception:
            raise UnauthorizedError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        stored = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == _token_hash(raw_refresh_token),
            RefreshToken.revoked.is_(False),
        ).first()

        if not stored or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh token expired or revoked")

        stored.revoked = True
        self.db.commit()

        user = self.db.query(User).filter(
            User.id == user_id, User.is_active.is_(True)
        ).first()
        if not user:
            raise UnauthorizedError("User not found")

        return self._issue_tokens(user)

    def logout(self, raw_refresh_token: str) -> None:
        stored = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == _token_hash(raw_refresh_token)
        ).first()
        if stored:
            stored.revoked = True
            self.db.commit()

    def _issue_tokens(self, user: User) -> AuthResponse:
        access_token = create_access_token(str(user.id))
        raw_refresh = create_refresh_token(str(user.id))

        db_token = RefreshToken(
            user_id=user.id,
            token_hash=_token_hash(raw_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_DAYS),
        )
        self.db.add(db_token)
        self.db.commit()

        return AuthResponse(access_token=access_token, refresh_token=raw_refresh)
