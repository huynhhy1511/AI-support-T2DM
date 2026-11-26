import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_user_and_crud():
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": test_email,
        "display_name": "Test User A",
        "consent_accepted": True,
    }

    # 1. Create user
    res = client.post("/api/v1/users", json=payload)
    assert res.status_code == 201, res.text
    user_data = res.json()
    user_id = user_data["id"]
    assert user_data["email"] == test_email
    assert user_data["display_name"] == "Test User A"
    assert user_data["consent_accepted_at"] is not None

    try:
        # 2. Duplicate email should return 409 Conflict
        res_dup = client.post("/api/v1/users", json=payload)
        assert res_dup.status_code == 409

        # 3. Get user by ID
        res_get = client.get(f"/api/v1/users/{user_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == user_id

        # 4. Update user
        res_update = client.put(
            f"/api/v1/users/{user_id}",
            json={"display_name": "Updated Name", "consent_accepted": False},
        )
        assert res_update.status_code == 200
        assert res_update.json()["display_name"] == "Updated Name"

        # 5. List users
        res_list = client.get("/api/v1/users?limit=10")
        assert res_list.status_code == 200
        assert isinstance(res_list.json(), list)
        assert any(u["id"] == user_id for u in res_list.json())

    finally:
        # 6. Delete user cleanup
        res_del = client.delete(f"/api/v1/users/{user_id}")
        assert res_del.status_code == 200

    # 7. Verify deletion
    res_verify = client.get(f"/api/v1/users/{user_id}")
    assert res_verify.status_code == 404


def test_get_nonexistent_user():
    random_id = uuid.uuid4()
    res = client.get(f"/api/v1/users/{random_id}")
    assert res.status_code == 404


def test_create_user_invalid_email():
    res = client.post(
        "/api/v1/users",
        json={"email": "not-an-email", "display_name": "Invalid"},
    )
    assert res.status_code == 422

