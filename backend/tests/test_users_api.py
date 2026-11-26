import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(prefix: str = "user"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User A",
            "consent_accepted": True,
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    user_data = reg_res.json()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    return user_data, {"Authorization": f"Bearer {token}"}


def test_create_user_and_crud():
    user_data, headers = _register_and_login("crud")
    user_id = user_data["id"]
    assert user_data["display_name"] == "Test User A"
    assert user_data["consent_accepted_at"] is not None

    try:
        # 1. Duplicate email on /users should return 409 Conflict
        res_dup = client.post(
            "/api/v1/users",
            json={
                "email": user_data["email"],
                "display_name": "Dup",
                "consent_accepted": True,
            },
        )
        assert res_dup.status_code == 409

        # 2. Get user by ID (authenticated)
        res_get = client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["id"] == user_id

        # 3. Update user (authenticated)
        res_update = client.put(
            f"/api/v1/users/{user_id}",
            json={"display_name": "Updated Name", "consent_accepted": False},
            headers=headers,
        )
        assert res_update.status_code == 200
        assert res_update.json()["display_name"] == "Updated Name"

        # 4. List users
        res_list = client.get("/api/v1/users?limit=10")
        assert res_list.status_code == 200
        assert isinstance(res_list.json(), list)
        assert any(u["id"] == user_id for u in res_list.json())

    finally:
        # 5. Delete user cleanup (authenticated)
        res_del = client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert res_del.status_code == 200

    # 6. Verify deletion (token now references deleted user -> 401)
    res_verify = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert res_verify.status_code == 401


def test_get_nonexistent_user():
    random_id = uuid.uuid4()
    # Unauthenticated -> 401
    res_unauth = client.get(f"/api/v1/users/{random_id}")
    assert res_unauth.status_code == 401

    # Authenticated as another user -> 403 Forbidden
    user_data, headers = _register_and_login("other")
    try:
        res_forbidden = client.get(f"/api/v1/users/{random_id}", headers=headers)
        assert res_forbidden.status_code == 403
    finally:
        client.delete(f"/api/v1/users/{user_data['id']}", headers=headers)


def test_create_user_invalid_email():
    res = client.post(
        "/api/v1/users",
        json={"email": "not-an-email", "display_name": "Invalid"},
    )
    assert res.status_code == 422
