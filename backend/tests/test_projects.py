import pytest
from fastapi.testclient import TestClient

REGISTER_URL = "/v1/auth/register"
PROJECTS_URL = "/v1/projects"


def _make_valid_composition(duration=60.0, fps=30, width=1920, height=1080):
    return {
        "resolution": {"width": width, "height": height},
        "fps": fps,
        "duration": duration,
        "tracks": [],
    }


@pytest.fixture
def auth_headers(client):
    resp = client.post(REGISTER_URL, json={"email": "proj@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def auth_headers_b(client):
    resp = client.post(REGISTER_URL, json={"email": "other@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_project(client, auth_headers, name="Test Project"):
    resp = client.post(PROJECTS_URL, json={"name": name}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


class TestCreateProject:
    def test_create_project_success(self, client, auth_headers):
        resp = client.post(PROJECTS_URL, json={"name": "My Video"}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Video"
        assert "composition" in data
        assert data["fps"] == 30
        assert data["resolution_width"] == 1920
        assert data["duration"] == 0.0

    def test_create_project_custom_settings(self, client, auth_headers):
        resp = client.post(
            PROJECTS_URL,
            json={"name": "4K", "resolution_width": 3840, "resolution_height": 2160, "fps": 60},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["resolution_width"] == 3840
        assert data["fps"] == 60

    def test_create_project_unauthenticated(self, client):
        resp = client.post(PROJECTS_URL, json={"name": "Test"})
        assert resp.status_code in (401, 403)

    def test_create_project_returns_empty_composition(self, client, auth_headers):
        resp = client.post(PROJECTS_URL, json={"name": "Test"}, headers=auth_headers)
        comp = resp.json()["composition"]
        assert comp["tracks"] == []
        assert comp["fps"] == 30


class TestListProjects:
    def test_list_projects_empty(self, client, auth_headers):
        resp = client.get(PROJECTS_URL, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_projects_shows_created(self, client, auth_headers):
        _create_project(client, auth_headers, "P1")
        _create_project(client, auth_headers, "P2")
        resp = client.get(PROJECTS_URL, headers=auth_headers)
        assert resp.json()["total"] == 2

    def test_list_projects_excludes_other_users(self, client, auth_headers, auth_headers_b):
        _create_project(client, auth_headers, "User A Project")
        resp = client.get(PROJECTS_URL, headers=auth_headers_b)
        assert resp.json()["total"] == 0

    def test_list_projects_excludes_archived_by_default(self, client, auth_headers):
        project = _create_project(client, auth_headers, "P1")
        client.put(
            f"{PROJECTS_URL}/{project['id']}",
            json={"is_archived": True},
            headers=auth_headers,
        )
        resp = client.get(PROJECTS_URL, headers=auth_headers)
        assert resp.json()["total"] == 0

    def test_list_archived_projects(self, client, auth_headers):
        project = _create_project(client, auth_headers, "P1")
        client.put(
            f"{PROJECTS_URL}/{project['id']}",
            json={"is_archived": True},
            headers=auth_headers,
        )
        resp = client.get(f"{PROJECTS_URL}?archived=true", headers=auth_headers)
        assert resp.json()["total"] == 1

    def test_list_projects_pagination(self, client, auth_headers):
        for i in range(5):
            _create_project(client, auth_headers, f"P{i}")
        page1 = client.get(f"{PROJECTS_URL}?page=1&page_size=3", headers=auth_headers).json()
        page2 = client.get(f"{PROJECTS_URL}?page=2&page_size=3", headers=auth_headers).json()
        assert len(page1["items"]) == 3
        assert len(page2["items"]) == 2
        assert page1["total"] == 5


class TestGetProject:
    def test_get_project_success(self, client, auth_headers):
        created = _create_project(client, auth_headers)
        resp = client.get(f"{PROJECTS_URL}/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_project_not_found(self, client, auth_headers):
        resp = client.get(f"{PROJECTS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_project_wrong_user(self, client, auth_headers, auth_headers_b):
        created = _create_project(client, auth_headers)
        resp = client.get(f"{PROJECTS_URL}/{created['id']}", headers=auth_headers_b)
        assert resp.status_code == 403


class TestUpdateProject:
    def test_update_name(self, client, auth_headers):
        created = _create_project(client, auth_headers, "Old Name")
        resp = client.put(
            f"{PROJECTS_URL}/{created['id']}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_with_valid_composition(self, client, auth_headers):
        created = _create_project(client, auth_headers)
        comp = _make_valid_composition(duration=30.0)
        resp = client.put(
            f"{PROJECTS_URL}/{created['id']}",
            json={"composition": comp},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["duration"] == 30.0
        assert data["composition"]["duration"] == 30.0

    def test_update_with_invalid_composition_rejected(self, client, auth_headers):
        created = _create_project(client, auth_headers)
        bad_comp = {"resolution": {"width": 1920, "height": 1080}, "fps": -1, "duration": 10.0, "tracks": []}
        resp = client.put(
            f"{PROJECTS_URL}/{created['id']}",
            json={"composition": bad_comp},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_update_wrong_user(self, client, auth_headers, auth_headers_b):
        created = _create_project(client, auth_headers)
        resp = client.put(
            f"{PROJECTS_URL}/{created['id']}",
            json={"name": "Hacked"},
            headers=auth_headers_b,
        )
        assert resp.status_code == 403

    def test_update_archives_project(self, client, auth_headers):
        created = _create_project(client, auth_headers)
        resp = client.put(
            f"{PROJECTS_URL}/{created['id']}",
            json={"is_archived": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_archived"] is True


class TestDeleteProject:
    def test_delete_project(self, client, auth_headers):
        created = _create_project(client, auth_headers)
        del_resp = client.delete(f"{PROJECTS_URL}/{created['id']}", headers=auth_headers)
        assert del_resp.status_code == 204

        get_resp = client.get(f"{PROJECTS_URL}/{created['id']}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_wrong_user(self, client, auth_headers, auth_headers_b):
        created = _create_project(client, auth_headers)
        resp = client.delete(f"{PROJECTS_URL}/{created['id']}", headers=auth_headers_b)
        assert resp.status_code == 403

    def test_delete_unauthenticated(self, client, auth_headers):
        created = _create_project(client, auth_headers)
        resp = client.delete(f"{PROJECTS_URL}/{created['id']}")
        assert resp.status_code in (401, 403)
