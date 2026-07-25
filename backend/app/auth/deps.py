from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.tokens import hash_token
from app.db.session import get_db
from app.models import AppSession, User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    session: AppSession
    graph_access_token: str


async def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token_hash = hash_token(credentials.credentials)
    result = await db.execute(
        select(AppSession)
        .where(AppSession.token_hash == token_hash)
        .options(selectinload(AppSession.user))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return AuthContext(
        user=session.user,
        session=session,
        graph_access_token=session.graph_access_token,
    )


async def get_user_id(auth: AuthContext = Depends(get_current_auth)) -> UUID:
    return auth.user.id
