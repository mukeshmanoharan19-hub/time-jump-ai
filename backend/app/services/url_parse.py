"""Parse and normalize Microsoft Teams / SharePoint / Stream recording URLs."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse


class UnsupportedRecordingUrlError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedRecordingUrl:
    original_url: str
    normalized_url: str
    kind: str  # sharepoint_stream | sharepoint_share | teams | onedrive_share


_SUPPORTED_HOST_SUFFIXES = (
    "sharepoint.com",
    "microsoft.com",
    "microsoftonline.com",
    "1drv.ms",
    "office.com",
)


def _host_allowed(hostname: str | None) -> bool:
    if not hostname:
        return False
    host = hostname.lower()
    return any(host == s or host.endswith("." + s) for s in _SUPPORTED_HOST_SUFFIXES)


def normalize_recording_url(url: str) -> ParsedRecordingUrl:
    raw = (url or "").strip()
    if not raw:
        raise UnsupportedRecordingUrlError("URL is empty")

    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise UnsupportedRecordingUrlError("URL must be http(s)")
    if not _host_allowed(parsed.hostname):
        raise UnsupportedRecordingUrlError(
            "Unsupported host. Use a Teams, SharePoint, Stream, or OneDrive recording link."
        )

    host = (parsed.hostname or "").lower()
    path = unquote(parsed.path or "")
    path_lower = path.lower()
    query = parse_qs(parsed.query)

    # SharePoint Stream player: .../_layouts/15/stream.aspx?id=/path/to/file.mp4
    if "stream.aspx" in path_lower:
        file_id = query.get("id", [None])[0]
        if not file_id:
            raise UnsupportedRecordingUrlError("Stream URL is missing the id query parameter")
        normalized = f"{parsed.scheme}://{host}{path}?id={file_id}"
        return ParsedRecordingUrl(raw, normalized, "sharepoint_stream")

    # Sharing links: /:v:/ /:f:/ /:u:/ etc.
    if "/:v:/" in path_lower or "/:f:/" in path_lower or "/:u:/" in path_lower:
        # Drop tracking fragments; keep path + essential query
        normalized = f"{parsed.scheme}://{host}{path}"
        if parsed.query:
            # keep resid/cid if present
            keep = []
            for key in ("resid", "cid", "e"):
                if key in query and query[key]:
                    keep.append(f"{key}={query[key][0]}")
            if keep:
                normalized += "?" + "&".join(keep)
        return ParsedRecordingUrl(raw, normalized, "sharepoint_share")

    # Teams deep links / meeting recording redirects
    if "teams.microsoft.com" in host or host.endswith(".teams.microsoft.com"):
        normalized = f"{parsed.scheme}://{host}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return ParsedRecordingUrl(raw, normalized, "teams")

    # OneDrive short links
    if host == "1drv.ms" or host.endswith(".1drv.ms"):
        normalized = f"{parsed.scheme}://{host}{path}"
        return ParsedRecordingUrl(raw, normalized, "onedrive_share")

    # Generic SharePoint path to a media file
    if "sharepoint.com" in host:
        if any(path_lower.endswith(ext) for ext in (".mp4", ".webm", ".mkv", ".mov")):
            normalized = f"{parsed.scheme}://{host}{path}"
            return ParsedRecordingUrl(raw, normalized, "sharepoint_stream")
        # Site document library paths without extension still may be recordings
        if "/documents/" in path_lower or "/shared documents/" in path_lower or "/recordings/" in path_lower:
            normalized = f"{parsed.scheme}://{host}{path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return ParsedRecordingUrl(raw, normalized, "sharepoint_stream")

    raise UnsupportedRecordingUrlError(
        "Unrecognized recording URL shape. Supported: SharePoint Stream, sharing links (:v:), "
        "Teams recording links, OneDrive short links."
    )
