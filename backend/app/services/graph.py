"""Microsoft Graph client for recording resolve (Phase 1)."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.services.url_parse import ParsedRecordingUrl, normalize_recording_url


class GraphError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class GraphUser:
    oid: str
    email: str | None
    display_name: str | None


@dataclass
class ResolvedRecording:
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
    raw: dict[str, Any]


def sharing_url_to_share_id(url: str) -> str:
    """Encode a sharing URL for Graph /shares/{shareId}."""
    encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"u!{encoded}"


async def fetch_graph_me(access_token: str) -> GraphUser:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{settings.graph_base_url}/me",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"$select": "id,displayName,mail,userPrincipalName"},
        )
    if resp.status_code == 401:
        raise GraphError("Microsoft token rejected by Graph", status_code=401)
    if resp.status_code >= 400:
        raise GraphError(f"Graph /me failed: {resp.text}", status_code=resp.status_code)

    data = resp.json()
    oid = data.get("id")
    if not oid:
        raise GraphError("Graph /me response missing id")
    email = data.get("mail") or data.get("userPrincipalName")
    return GraphUser(oid=oid, email=email, display_name=data.get("displayName"))


async def _graph_get(access_token: str, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.graph_base_url}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
    if resp.status_code == 401:
        raise GraphError("Microsoft token rejected by Graph", status_code=401)
    if resp.status_code == 403:
        raise GraphError("Access denied to this recording via Graph", status_code=403)
    if resp.status_code == 404:
        raise GraphError("Recording not found in Microsoft Graph", status_code=404)
    if resp.status_code >= 400:
        raise GraphError(f"Graph request failed ({resp.status_code}): {resp.text}", status_code=resp.status_code)
    return resp.json()


async def _find_sibling_transcript(
    access_token: str, drive_id: str, parent_id: str, recording_name: str | None
) -> tuple[bool, str | None, str | None]:
    """Look for a .vtt / transcript file next to the recording."""
    try:
        data = await _graph_get(
            access_token,
            f"/drives/{drive_id}/items/{parent_id}/children",
            params={"$select": "id,name,file"},
        )
    except GraphError:
        return False, None, None

    names_hint = []
    if recording_name:
        base = recording_name.rsplit(".", 1)[0].lower()
        names_hint.append(base)

    for item in data.get("value", []):
        name = (item.get("name") or "").lower()
        if not name.endswith((".vtt", ".srt")):
            continue
        if "transcript" in name or any(h and h in name for h in names_hint) or name.endswith(".vtt"):
            return True, "sibling_file", item.get("id")
    return False, None, None


async def resolve_recording(access_token: str, url: str) -> ResolvedRecording:
    parsed: ParsedRecordingUrl = normalize_recording_url(url)
    share_id = sharing_url_to_share_id(parsed.normalized_url)

    item = await _graph_get(
        access_token,
        f"/shares/{share_id}/driveItem",
        params={"$select": "id,name,size,file,webUrl,parentReference,@microsoft.graph.downloadUrl"},
    )

    parent = item.get("parentReference") or {}
    drive_id = parent.get("driveId")
    parent_id = parent.get("id")
    file_meta = item.get("file") or {}
    mime = file_meta.get("mimeType")
    name = item.get("name")
    download_url = item.get("@microsoft.graph.downloadUrl")
    can_download = bool(download_url) or bool(item.get("id") and drive_id)

    transcript_available = False
    transcript_source = None
    transcript_item_id = None
    if drive_id and parent_id:
        transcript_available, transcript_source, transcript_item_id = await _find_sibling_transcript(
            access_token, drive_id, parent_id, name
        )

    return ResolvedRecording(
        normalized_url=parsed.normalized_url,
        kind=parsed.kind,
        drive_item_id=item.get("id"),
        drive_id=drive_id,
        name=name,
        size=item.get("size"),
        mime_type=mime,
        web_url=item.get("webUrl"),
        can_download=can_download,
        transcript_available=transcript_available,
        transcript_source=transcript_source,
        transcript_item_id=transcript_item_id,
        raw={"id": item.get("id"), "name": name, "parentReference": parent},
    )
