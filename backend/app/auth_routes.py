from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth_security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    normalize_email,
    password_hash_needs_rehash,
    verify_password,
)
from app.database import get_database_session
from app.models import AuthSession, User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


SESSION_COOKIE_NAME = "cri_session"

SESSION_DURATION = timedelta(days=7)

GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "",
).strip()


COOKIE_SECURE = (
    os.getenv(
        "AUTH_COOKIE_SECURE",
        "false",
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)


class RegisterRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Le nom est trop court."
            )

        return value

    @field_validator("email")
    @classmethod
    def clean_email(
        cls,
        value: str,
    ) -> str:
        value = normalize_email(value)

        if " " in value:
            raise ValueError(
                "Adresse e-mail invalide."
            )

        if value.count("@") != 1:
            raise ValueError(
                "Adresse e-mail invalide."
            )

        local_part, domain = value.split(
            "@",
            1,
        )

        if not local_part or not domain:
            raise ValueError(
                "Adresse e-mail invalide."
            )

        if domain.startswith("."):
            raise ValueError(
                "Adresse e-mail invalide."
            )

        if domain.endswith("."):
            raise ValueError(
                "Adresse e-mail invalide."
            )

        return value


class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def clean_email(
        cls,
        value: str,
    ) -> str:
        return normalize_email(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    name: str
    email: str
    auth_provider: str
    created_at: datetime
    last_login: datetime | None


class LogoutResponse(BaseModel):
    ok: bool


def set_session_cookie(
    response: Response,
    token: str,
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(
            SESSION_DURATION.total_seconds()
        ),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(
    response: Response,
) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def create_session(
    database_session: Session,
    user: User,
) -> str:
    now = datetime.now(timezone.utc)

    database_session.execute(
        delete(AuthSession).where(
            AuthSession.expires_at <= now
        )
    )

    raw_token = generate_session_token()

    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(
            raw_token
        ),
        expires_at=(
            now + SESSION_DURATION
        ),
    )

    database_session.add(
        auth_session
    )

    database_session.commit()

    return raw_token


def get_current_user(
    request: Request,
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE_NAME,
    ),
    database_session: Session = Depends(
        get_database_session
    ),
) -> User:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise.",
        )

    token_hash = hash_session_token(
        session_token
    )

    now = datetime.now(timezone.utc)

    auth_session = database_session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash
            == token_hash,
            AuthSession.expires_at
            > now,
        )
    )

    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Session absente ou expirée."
            ),
        )

    user = database_session.get(
        User,
        auth_session.user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Ce compte est désactivé."
            ),
        )

    request.state.user_id = str(
        user.id
    )

    request.state.user_name = user.name

    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    response: Response,
    database_session: Session = Depends(
        get_database_session
    ),
) -> User:
    existing_user = database_session.scalar(
        select(User).where(
            User.email == payload.email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Un compte existe déjà "
                "avec cette adresse e-mail."
            ),
        )

    now = datetime.now(timezone.utc)

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(
            payload.password
        ),
        auth_provider="local",
        is_active=True,
        last_login=now,
    )

    database_session.add(user)

    try:
        database_session.commit()

    except IntegrityError as error:
        database_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Un compte existe déjà "
                "avec cette adresse e-mail."
            ),
        ) from error

    database_session.refresh(user)

    token = create_session(
        database_session,
        user,
    )

    set_session_cookie(
        response,
        token,
    )

    return user


@router.post(
    "/login",
    response_model=UserResponse,
)
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    database_session: Session = Depends(
        get_database_session
    ),
) -> User:
    user = database_session.scalar(
        select(User).where(
            User.email == payload.email
        )
    )

    credentials_valid = (
        user is not None
        and user.password_hash is not None
        and verify_password(
            payload.password,
            user.password_hash,
        )
    )

    if not credentials_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Adresse e-mail ou mot "
                "de passe incorrect."
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Ce compte est désactivé."
            ),
        )

    if password_hash_needs_rehash(
        user.password_hash
    ):
        user.password_hash = hash_password(
            payload.password
        )

    user.last_login = datetime.now(
        timezone.utc
    )

    database_session.commit()
    database_session.refresh(user)

    token = create_session(
        database_session,
        user,
    )

    set_session_cookie(
        response,
        token,
    )

    request.state.user_id = str(
        user.id
    )

    request.state.user_name = user.name

    return user


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    return current_user


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
def logout(
    request: Request,
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE_NAME,
    ),
    database_session: Session = Depends(
        get_database_session
    ),
) -> LogoutResponse:
    if session_token:
        token_hash = hash_session_token(
            session_token
        )

        logout_user_id = database_session.scalar(
            select(AuthSession.user_id).where(
                AuthSession.token_hash
                == token_hash
            )
        )

        if logout_user_id is not None:
            request.state.user_id = str(
                logout_user_id
            )

            logout_user = database_session.get(
                User,
                logout_user_id,
            )

            if logout_user is not None:
                request.state.user_name = (
                    logout_user.name
                )

        database_session.execute(
            delete(AuthSession).where(
                AuthSession.token_hash
                == token_hash
            )
        )

        database_session.commit()

    clear_session_cookie(
        response
    )

    return LogoutResponse(
        ok=True
    )


class GoogleCredentialRequest(BaseModel):
    credential: str = Field(
        min_length=20,
        max_length=10000,
    )


class GoogleConfigResponse(BaseModel):
    client_id: str


def verify_google_credential(
    credential: str,
) -> dict:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "La connexion Google "
                "n'est pas configurée."
            ),
        )

    try:
        claims = (
            google_id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                GOOGLE_CLIENT_ID,
            )
        )

    except (
        ValueError,
        GoogleAuthError,
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Jeton Google invalide."
            ),
        ) from exc

    issuer = claims.get("iss")

    if issuer not in {
        "accounts.google.com",
        "https://accounts.google.com",
    }:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Émetteur Google invalide."
            ),
        )

    google_sub = str(
        claims.get("sub", "")
    ).strip()

    email = normalize_email(
        str(
            claims.get("email", "")
        )
    )

    email_verified = (
        str(
            claims.get(
                "email_verified",
                "",
            )
        )
        .strip()
        .lower()
        == "true"
    )

    if (
        not google_sub
        or not email
        or not email_verified
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Compte Google non vérifié."
            ),
        )

    return claims


@router.get(
    "/google-config",
    response_model=GoogleConfigResponse,
)
def google_config() -> GoogleConfigResponse:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "La connexion Google "
                "n'est pas configurée."
            ),
        )

    return GoogleConfigResponse(
        client_id=GOOGLE_CLIENT_ID
    )


@router.post(
    "/google",
    response_model=UserResponse,
)
def google_login(
    request: Request,
    payload: GoogleCredentialRequest,
    response: Response,
    database_session: Session = Depends(
        get_database_session
    ),
) -> User:
    claims = verify_google_credential(
        payload.credential
    )

    google_sub = str(
        claims["sub"]
    ).strip()

    email = normalize_email(
        str(
            claims["email"]
        )
    )

    google_name = str(
        claims.get("name", "")
        or claims.get("given_name", "")
        or email.split("@")[0]
    ).strip()

    user = database_session.scalar(
        select(User).where(
            User.google_sub == google_sub
        )
    )

    if user is None:
        user = database_session.scalar(
            select(User).where(
                User.email == email
            )
        )

        if user is not None:
            if (
                user.google_sub
                and user.google_sub
                != google_sub
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Ce compte est déjà lié "
                        "à un autre compte Google."
                    ),
                )

            user.google_sub = google_sub

        else:
            user = User(
                name=google_name,
                email=email,
                password_hash=None,
                google_sub=google_sub,
                auth_provider="google",
                is_active=True,
            )

            database_session.add(                user
            )

    if not user.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Compte désactivé.",
        )

    user.last_login = datetime.now(
        timezone.utc
    )

    database_session.commit()
    database_session.refresh(user)

    session_token = create_session(
        database_session,
        user,
    )

    set_session_cookie(
        response,
        session_token,
    )

    request.state.user_id = str(
        user.id
    )

    request.state.user_name = user.name

    return user

