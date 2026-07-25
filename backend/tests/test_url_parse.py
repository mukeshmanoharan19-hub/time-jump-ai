import pytest

from app.services.url_parse import UnsupportedRecordingUrlError, normalize_recording_url


def test_stream_aspx():
    url = (
        "https://contoso.sharepoint.com/sites/Team/_layouts/15/stream.aspx"
        "?id=%2Fsites%2FTeam%2FShared%20Documents%2FRecordings%2Fstandup.mp4&nav=abc"
    )
    parsed = normalize_recording_url(url)
    assert parsed.kind == "sharepoint_stream"
    assert "stream.aspx" in parsed.normalized_url
    assert "id=" in parsed.normalized_url


def test_sharing_link_v():
    url = "https://contoso-my.sharepoint.com/:v:/g/personal/user_contoso_com/EbExampleShareId?e=abcd"
    parsed = normalize_recording_url(url)
    assert parsed.kind == "sharepoint_share"
    assert "/:v:/" in parsed.normalized_url


def test_teams_host():
    url = "https://teams.microsoft.com/l/meetingrec/19:meeting_abc@thread.v2"
    parsed = normalize_recording_url(url)
    assert parsed.kind == "teams"


def test_onedrive_short():
    url = "https://1drv.ms/v/s!Abc123"
    parsed = normalize_recording_url(url)
    assert parsed.kind == "onedrive_share"


def test_rejects_empty():
    with pytest.raises(UnsupportedRecordingUrlError):
        normalize_recording_url("")


def test_rejects_unknown_host():
    with pytest.raises(UnsupportedRecordingUrlError):
        normalize_recording_url("https://example.com/video.mp4")


def test_sharepoint_mp4_path():
    url = "https://contoso.sharepoint.com/sites/Team/Shared%20Documents/Recordings/call.mp4"
    parsed = normalize_recording_url(url)
    assert parsed.kind == "sharepoint_stream"
    assert parsed.normalized_url.endswith("call.mp4")
