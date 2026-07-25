from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.deps import AuthContext, get_current_auth
from app.services.graph import GraphError, resolve_recording
from app.services.url_parse import UnsupportedRecordingUrlError

router = APIRouter(prefix="/recordings", tags=["recordings"])


class ResolveRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


class ResolveResponse(BaseModel):
    normalized_url: str
    kind: str
    drive_item_id: str | None
    drive_id: str | None
    name: str | None
    size: int | None
    mime_type: str | None
    web_url: str | None
    can_download: bool
    transcript_available: bool
    transcript_source: str | None
    transcript_item_id: str | None


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_recording_url(
    body: ResolveRequest,
    auth: AuthContext = Depends(get_current_auth),
):
    try:
        resolved = await resolve_recording(auth.graph_access_token, body.url)
    except UnsupportedRecordingUrlError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except GraphError as e:
        if e.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Graph token expired or invalid. Sign in again.",
            ) from e
        if e.status_code in (403, 404):
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    return ResolveResponse(
        normalized_url=resolved.normalized_url,
        kind=resolved.kind,
        drive_item_id=resolved.drive_item_id,
        drive_id=resolved.drive_id,
        name=resolved.name,
        size=resolved.size,
        mime_type=resolved.mime_type,
        web_url=resolved.web_url,
        can_download=resolved.can_download,
        transcript_available=resolved.transcript_available,
        transcript_source=resolved.transcript_source,
        transcript_item_id=resolved.transcript_item_id,
    )
