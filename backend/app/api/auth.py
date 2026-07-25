from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_auth
from app.auth.tokens import hash_token, new_session_token, session_expiry
from app.db.session import get_db
from app.models import AppSession, User
from app.services.graph import GraphError, fetch_graph_me

router = APIRouter(prefix="/auth", tags=["auth"])


class MicrosoftExchangeRequest(BaseModel):
    access_token: str = Field(min_length=20)
    expires_in: int | None = Field(default=None, ge=60, description="Seconds until Graph token expires")


class MicrosoftExchangeResponse(BaseModel):
    session_token: str
    expires_at: datetime
    user: dict


class MeResponse(BaseModel):
    id: str
    email: str | None
    display_name: str | None


@router.post("/microsoft", response_model=MicrosoftExchangeResponse)
async def exchange_microsoft_token(
    body: MicrosoftExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        me = await fetch_graph_me(body.access_token)
    except GraphError as e:
        code = status.HTTP_401_UNAUTHORIZED if e.status_code == 401 else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(e)) from e

    result = await db.execute(select(User).where(User.microsoft_oid == me.oid))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(microsoft_oid=me.oid, email=me.email, display_name=me.display_name)
        db.add(user)
        await db.flush()
    else:
        user.email = me.email
        user.display_name = me.display_name

    token = new_session_token()
    graph_expires = None
    if body.expires_in is not None:
        graph_expires = datetime.now(timezone.utc) + timedelta(seconds=body.expires_in)

    app_session = AppSession(
        user_id=user.id,
        token_hash=hash_token(token),
        graph_access_token=body.access_token,
        graph_token_expires_at=graph_expires,
        expires_at=session_expiry(),
    )
    db.add(app_session)
    await db.commit()

    return MicrosoftExchangeResponse(
        session_token=token,
        expires_at=app_session.expires_at,
        user={
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
        },
    )


@router.get("/me", response_model=MeResponse)
async def auth_me(auth: AuthContext = Depends(get_current_auth)):
    return MeResponse(
        id=str(auth.user.id),
        email=auth.user.email,
        display_name=auth.user.display_name,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(auth.session)
    await db.commit()
