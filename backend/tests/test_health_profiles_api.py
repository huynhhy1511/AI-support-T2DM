import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(prefix: str = "patient"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Patient Profile Test",
            "consent_accepted": True,
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    user_id = reg_res.json()["id"]

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def test_health_profile_lifecycle():
    # 1. Register & login user
    user_id, headers = _register_and_login("profile")

    try:
        # 2. Create health profile for this user
        profile_data = {
            "user_id": user_id,
            "date_of_birth": "1985-06-20",
            "sex": "male",
            "height_cm": 170.0,
            "weight_kg": 68.0,
            "diabetes_type": "type2",
            "diagnosis_year": 2020,
            "activity_level": "moderate",
            "dietary_preference": "low_sodium",
        }
        res_create = client.post(
            "/api/v1/health-profiles", json=profile_data, headers=headers
        )
        assert res_create.status_code == 201, res_create.text
        created = res_create.json()
        assert created["user_id"] == user_id
        assert created["bmi"] == 23.53  # 68 / (1.7^2) = 23.529...

        # 3. Duplicate profile creation should return 409 Conflict
        res_dup = client.post(
            "/api/v1/health-profiles", json=profile_data, headers=headers
        )
        assert res_dup.status_code == 409

        # 4. Get profile by user_id
        res_get = client.get(
            f"/api/v1/health-profiles/user/{user_id}", headers=headers
        )
        assert res_get.status_code == 200
        assert res_get.json()["activity_level"] == "moderate"

        # 5. Update health profile (weight changed to 72.25 kg -> BMI = 72.25 / 2.89 = 25.0)
        res_update = client.put(
            f"/api/v1/health-profiles/user/{user_id}",
            json={"weight_kg": 72.25, "activity_level": "active"},
            headers=headers,
        )
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["weight_kg"] == 72.25
        assert updated["activity_level"] == "active"
        assert updated["bmi"] == 25.0

        # 6. Delete profile
        res_del = client.delete(
            f"/api/v1/health-profiles/user/{user_id}", headers=headers
        )
        assert res_del.status_code == 200

        # 7. Verify profile is gone
        res_verify = client.get(
            f"/api/v1/health-profiles/user/{user_id}", headers=headers
        )
        assert res_verify.status_code == 404

    finally:
        # Cleanup user
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_create_profile_nonexistent_user():
    # Authenticated user attempting to create profile for another user_id -> 403 Forbidden
    user_id, headers = _register_and_login("nonexist")
    fake_user_id = str(uuid.uuid4())
    try:
        res = client.post(
            "/api/v1/health-profiles",
            json={"user_id": fake_user_id, "height_cm": 175.0, "weight_kg": 70.0},
            headers=headers,
        )
        assert res.status_code == 403
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_invalid_health_profile_metrics():
    user_id, headers = _register_and_login("invalid_metric")
    try:
        # Negative height or weight should be rejected with 422
        res = client.post(
            "/api/v1/health-profiles",
            json={"user_id": user_id, "height_cm": -10, "weight_kg": 70},
            headers=headers,
        )
        assert res.status_code == 422
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)
