import pytest
from fastapi.testclient import TestClient

REGISTER_URL = "/v1/auth/register"
PROJECTS_URL = "/v1/projects"

MAX_VERSIONS = 50


def _make_composition(duration=60.0, fps=30, width=1920, height=1080):
    return {
        "resolution": {"width": width, "height": height},
        "fps": fps,
        "duration": duration,
        "tracks": [],
    }


@pytest.fixture
def auth_headers(client):
    resp = client.post(REGISTER_URL, json={"email": "versions@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def auth_headers_b(client):
    resp = client.post(REGISTER_URL, json={"email": "other2@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def project(client, auth_headers):
    resp = client.post(PROJECTS_URL, json={"name": "Version Test"}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


def _update_project(client, auth_headers, project_id, duration=10.0):
    resp = client.put(
        f"{PROJECTS_URL}/{project_id}",
        json={"composition": _make_composition(duration=duration)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    return resp.json()


def _versions_url(project_id):
    return f"{PROJECTS_URL}/{project_id}/versions"


class TestVersionCreation:
    def test_update_creates_version(self, client, auth_headers, project):
        _update_project(client, auth_headers, project["id"])
        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["version_number"] == 1

    def test_multiple_updates_create_multiple_versions(self, client, auth_headers, project):
        for i in range(3):
            _update_project(client, auth_headers, project["id"], duration=float(10 + i))
        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        assert resp.json()["total"] == 3

    def test_versions_ordered_newest_first(self, client, auth_headers, project):
        _update_project(client, auth_headers, project["id"], duration=10.0)
        _update_project(client, auth_headers, project["id"], duration=20.0)
        _update_project(client, auth_headers, project["id"], duration=30.0)
        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        items = resp.json()["items"]
        version_numbers = [v["version_number"] for v in items]
        assert version_numbers == sorted(version_numbers, reverse=True)

    def test_version_snapshot_contains_old_composition(self, client, auth_headers, project):
        # First update: set duration to 10
        _update_project(client, auth_headers, project["id"], duration=10.0)
        # Second update: set duration to 20 — this creates v2 snapshotting the duration=10 state
        _update_project(client, auth_headers, project["id"], duration=20.0)

        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        items = resp.json()["items"]
        # Newest version (v2) should snapshot the state BEFORE the second update (duration=10)
        v2 = next(v for v in items if v["version_number"] == 2)
        assert v2["composition_snapshot"]["duration"] == 10.0

    def test_no_version_on_create(self, client, auth_headers, project):
        # Creating a project should NOT auto-create a version
        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        assert resp.json()["total"] == 0


class TestVersionPruning:
    def test_version_cap_enforced(self, client, auth_headers, project):
        # Create MAX_VERSIONS + 3 updates — only MAX_VERSIONS should remain
        for i in range(MAX_VERSIONS + 3):
            _update_project(client, auth_headers, project["id"], duration=float(i + 1))
        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        assert resp.json()["total"] == MAX_VERSIONS

    def test_oldest_versions_pruned(self, client, auth_headers, project):
        for i in range(MAX_VERSIONS + 2):
            _update_project(client, auth_headers, project["id"], duration=float(i + 1))
        resp = client.get(
            _versions_url(project["id"]) + f"?page={MAX_VERSIONS // 20 + 1}&page_size=20",
            headers=auth_headers,
        )
        items = resp.json()["items"]
        # All remaining version numbers should be >= 3 (oldest 2 pruned)
        min_version = min(v["version_number"] for v in items) if items else None
        if min_version:
            assert min_version >= 3


class TestRestoreVersion:
    def test_restore_sets_composition(self, client, auth_headers, project):
        # v1 snapshot: empty comp (duration=0)
        _update_project(client, auth_headers, project["id"], duration=10.0)
        # v2 snapshot: duration=10
        _update_project(client, auth_headers, project["id"], duration=20.0)

        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        versions = resp.json()["items"]
        # v1 snapshot is the empty composition (duration=0), v2 has duration=10
        v1 = next(v for v in versions if v["version_number"] == 1)

        restore_resp = client.post(
            f"{PROJECTS_URL}/{project['id']}/versions/{v1['id']}/restore",
            headers=auth_headers,
        )
        assert restore_resp.status_code == 200
        data = restore_resp.json()
        assert data["composition"]["duration"] == v1["composition_snapshot"]["duration"]

    def test_restore_creates_pre_restore_snapshot(self, client, auth_headers, project):
        _update_project(client, auth_headers, project["id"], duration=10.0)
        _update_project(client, auth_headers, project["id"], duration=20.0)

        resp = client.get(_versions_url(project["id"]), headers=auth_headers)
        versions_before = resp.json()["items"]
        v1 = next(v for v in versions_before if v["version_number"] == 1)
        count_before = resp.json()["total"]

        client.post(
            f"{PROJECTS_URL}/{project['id']}/versions/{v1['id']}/restore",
            headers=auth_headers,
        )

        resp_after = client.get(_versions_url(project["id"]), headers=auth_headers)
        assert resp_after.json()["total"] == count_before + 1

    def test_restore_not_found(self, client, auth_headers, project):
        resp = client.post(
            f"{PROJECTS_URL}/{project['id']}/versions/00000000-0000-0000-0000-000000000000/restore",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_restore_wrong_user(self, client, auth_headers, auth_headers_b, project):
        _update_project(client, auth_headers, project["id"])
        versions = client.get(_versions_url(project["id"]), headers=auth_headers).json()["items"]

        resp = client.post(
            f"{PROJECTS_URL}/{project['id']}/versions/{versions[0]['id']}/restore",
            headers=auth_headers_b,
        )
        assert resp.status_code == 403


class TestVersionAccess:
    def test_list_versions_wrong_user(self, client, auth_headers, auth_headers_b, project):
        resp = client.get(_versions_url(project["id"]), headers=auth_headers_b)
        assert resp.status_code == 403

    def test_list_versions_pagination(self, client, auth_headers, project):
        for i in range(5):
            _update_project(client, auth_headers, project["id"], duration=float(i + 1))
        page1 = client.get(
            _versions_url(project["id"]) + "?page=1&page_size=3", headers=auth_headers
        ).json()
        page2 = client.get(
            _versions_url(project["id"]) + "?page=2&page_size=3", headers=auth_headers
        ).json()
        assert len(page1["items"]) == 3
        assert len(page2["items"]) == 2
        assert page1["total"] == 5
