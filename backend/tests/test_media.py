from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient


REGISTER_URL = "/v1/auth/register"
LOGIN_URL = "/v1/auth/login"
UPLOAD_URL_ENDPOINT = "/v1/media/upload-url"
CONFIRM_ENDPOINT = "/v1/media/confirm"
MEDIA_LIST_ENDPOINT = "/v1/media"


@pytest.fixture
def mock_spaces(monkeypatch):
    mock = MagicMock()
    mock.generate_presigned_url.return_value = "https://fake-spaces.com/presigned-upload"
    mock.delete_object.return_value = {}
    monkeypatch.setattr(
        "app.services.media_service.MediaService._get_spaces_client",
        lambda self: mock,
    )
    return mock


@pytest.fixture
def mock_ffprobe(monkeypatch):
    monkeypatch.setattr(
        "app.services.media_service.MediaService._extract_ffprobe_metadata",
        lambda self, key: {"duration_seconds": 30.0, "width": 1920, "height": 1080, "fps": 30.0, "codec": "h264"},
    )


@pytest.fixture
def auth_headers(client):
    resp = client.post(REGISTER_URL, json={"email": "media@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def auth_headers_b(client):
    resp = client.post(REGISTER_URL, json={"email": "other@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe, filename="clip.mp4"):
    upload_resp = client.post(
        UPLOAD_URL_ENDPOINT,
        json={"filename": filename, "mime_type": "video/mp4", "size_bytes": 1_000_000},
        headers=auth_headers,
    )
    assert upload_resp.status_code == 200
    storage_key = upload_resp.json()["storage_key"]
    return client.post(
        CONFIRM_ENDPOINT,
        json={"storage_key": storage_key, "filename": filename, "mime_type": "video/mp4", "size_bytes": 1_000_000},
        headers=auth_headers,
    )


class TestUploadUrl:
    def test_upload_url_success(self, client, auth_headers, mock_spaces):
        resp = client.post(
            UPLOAD_URL_ENDPOINT,
            json={"filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 5_000_000},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "upload_url" in data
        assert "storage_key" in data
        assert "expires_at" in data
        assert data["upload_url"] == "https://fake-spaces.com/presigned-upload"

    def test_upload_url_requires_auth(self, client, mock_spaces):
        resp = client.post(
            UPLOAD_URL_ENDPOINT,
            json={"filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 1000},
        )
        assert resp.status_code in (401, 403)

    def test_storage_key_scoped_to_user(self, client, auth_headers, mock_spaces):
        resp = client.post(
            UPLOAD_URL_ENDPOINT,
            json={"filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 1000},
            headers=auth_headers,
        )
        storage_key = resp.json()["storage_key"]
        assert storage_key.startswith("media/")


class TestConfirmUpload:
    def test_confirm_creates_media(self, client, auth_headers, mock_spaces, mock_ffprobe):
        resp = _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe)
        assert resp.status_code == 201
        data = resp.json()
        assert data["media_type"] == "video"
        assert data["status"] == "ready"
        assert data["width"] == 1920
        assert data["duration_seconds"] == 30.0

    def test_confirm_requires_auth(self, client, mock_spaces, mock_ffprobe):
        resp = client.post(
            CONFIRM_ENDPOINT,
            json={"storage_key": "media/fake/key.mp4", "filename": "x.mp4", "mime_type": "video/mp4", "size_bytes": 100},
        )
        assert resp.status_code in (401, 403)

    def test_confirm_wrong_owner(self, client, auth_headers, auth_headers_b, mock_spaces, mock_ffprobe):
        upload_resp = client.post(
            UPLOAD_URL_ENDPOINT,
            json={"filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 100},
            headers=auth_headers,
        )
        storage_key = upload_resp.json()["storage_key"]
        # User B tries to confirm user A's storage_key
        resp = client.post(
            CONFIRM_ENDPOINT,
            json={"storage_key": storage_key, "filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 100},
            headers=auth_headers_b,
        )
        assert resp.status_code == 403

    def test_confirm_duplicate_key_rejected(self, client, auth_headers, mock_spaces, mock_ffprobe):
        upload_resp = client.post(
            UPLOAD_URL_ENDPOINT,
            json={"filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 100},
            headers=auth_headers,
        )
        storage_key = upload_resp.json()["storage_key"]
        payload = {"storage_key": storage_key, "filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 100}
        r1 = client.post(CONFIRM_ENDPOINT, json=payload, headers=auth_headers)
        assert r1.status_code == 201
        r2 = client.post(CONFIRM_ENDPOINT, json=payload, headers=auth_headers)
        assert r2.status_code == 409


class TestListMedia:
    def test_list_media_empty(self, client, auth_headers, mock_spaces):
        resp = client.get(MEDIA_LIST_ENDPOINT, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_media_shows_confirmed(self, client, auth_headers, mock_spaces, mock_ffprobe):
        _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe, "clip.mp4")
        resp = client.get(MEDIA_LIST_ENDPOINT, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_media_filter_by_type(self, client, auth_headers, mock_spaces, mock_ffprobe):
        # Upload video
        _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe, "clip.mp4")
        # Upload image — override ffprobe mock for image
        upload_resp = client.post(
            UPLOAD_URL_ENDPOINT,
            json={"filename": "photo.png", "mime_type": "image/png", "size_bytes": 50_000},
            headers=auth_headers,
        )
        storage_key = upload_resp.json()["storage_key"]
        client.post(
            CONFIRM_ENDPOINT,
            json={"storage_key": storage_key, "filename": "photo.png", "mime_type": "image/png", "size_bytes": 50_000},
            headers=auth_headers,
        )

        resp = client.get(f"{MEDIA_LIST_ENDPOINT}?media_type=video", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["media_type"] == "video"

    def test_list_media_only_own(self, client, auth_headers, auth_headers_b, mock_spaces, mock_ffprobe):
        _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe)
        resp = client.get(MEDIA_LIST_ENDPOINT, headers=auth_headers_b)
        assert resp.json()["total"] == 0


class TestDeleteMedia:
    def test_delete_soft_deletes(self, client, auth_headers, mock_spaces, mock_ffprobe, db):
        confirm_resp = _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe)
        media_id = confirm_resp.json()["id"]

        del_resp = client.delete(f"{MEDIA_LIST_ENDPOINT}/{media_id}", headers=auth_headers)
        assert del_resp.status_code == 204

        # No longer in list
        list_resp = client.get(MEDIA_LIST_ENDPOINT, headers=auth_headers)
        assert list_resp.json()["total"] == 0

        # But record still in DB with is_deleted=True
        from app.models.media import Media
        record = db.query(Media).filter(Media.id == media_id).first()
        assert record is not None
        assert record.is_deleted is True

    def test_delete_wrong_user_returns_404(self, client, auth_headers, auth_headers_b, mock_spaces, mock_ffprobe):
        confirm_resp = _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe)
        media_id = confirm_resp.json()["id"]

        resp = client.delete(f"{MEDIA_LIST_ENDPOINT}/{media_id}", headers=auth_headers_b)
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client, auth_headers, mock_spaces, mock_ffprobe):
        confirm_resp = _confirm_payload(client, auth_headers, mock_spaces, mock_ffprobe)
        media_id = confirm_resp.json()["id"]

        resp = client.delete(f"{MEDIA_LIST_ENDPOINT}/{media_id}")
        assert resp.status_code in (401, 403)
