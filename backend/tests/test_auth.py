import pytest

REGISTER_URL = "/v1/auth/register"
LOGIN_URL = "/v1/auth/login"
REFRESH_URL = "/v1/auth/refresh"
LOGOUT_URL = "/v1/auth/logout"
ME_URL = "/v1/users/me"

USER_PAYLOAD = {"email": "test@example.com", "password": "password123"}


def test_register_success(client):
    response = client.post(REGISTER_URL, json=USER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email(client):
    client.post(REGISTER_URL, json=USER_PAYLOAD)
    response = client.post(REGISTER_URL, json=USER_PAYLOAD)
    assert response.status_code == 409
    assert "already registered" in response.json()["error"]


def test_login_success(client):
    client.post(REGISTER_URL, json=USER_PAYLOAD)
    response = client.post(LOGIN_URL, json=USER_PAYLOAD)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    client.post(REGISTER_URL, json=USER_PAYLOAD)
    response = client.post(LOGIN_URL, json={"email": USER_PAYLOAD["email"], "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "x"})
    assert response.status_code == 401


def test_protected_endpoint_requires_auth(client):
    response = client.get(ME_URL)
    assert response.status_code in (401, 403)


def test_protected_endpoint_with_valid_token(client):
    tokens = client.post(REGISTER_URL, json=USER_PAYLOAD).json()
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == USER_PAYLOAD["email"]


def test_protected_endpoint_with_invalid_token(client):
    response = client.get(ME_URL, headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


def test_refresh_token(client):
    tokens = client.post(REGISTER_URL, json=USER_PAYLOAD).json()
    response = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_token_cannot_be_reused(client):
    tokens = client.post(REGISTER_URL, json=USER_PAYLOAD).json()
    client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    response = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    tokens = client.post(REGISTER_URL, json=USER_PAYLOAD).json()
    client.post(LOGOUT_URL, json={"refresh_token": tokens["refresh_token"]})
    response = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_update_profile(client):
    tokens = client.post(REGISTER_URL, json={**USER_PAYLOAD, "full_name": "Alice"}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.put(ME_URL, json={"full_name": "Bob"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Bob"
