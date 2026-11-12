import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_profile_lifecycle():
    # 1. Create a user first
    test_email = f"patient_{uuid.uuid4().hex[:8]}@example.com"
    user_res = client.post(
        "/api/v1/users",
        json={"email": test_email, "display_name": "Patient Profile Test"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

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
        res_create = client.post("/api/v1/health-profiles", json=profile_data)
        assert res_create.status_code == 201, res_create.text
        created = res_create.json()
        assert created["user_id"] == user_id
        assert created["bmi"] == 23.53  # 68 / (1.7^2) = 23.529...

        # 3. Duplicate profile creation should return 409 Conflict
        res_dup = client.post("/api/v1/health-profiles", json=profile_data)
        assert res_dup.status_code == 409

        # 4. Get profile by user_id
        res_get = client.get(f"/api/v1/health-profiles/user/{user_id}")
        assert res_get.status_code == 200
        assert res_get.json()["activity_level"] == "moderate"

        # 5. Update health profile (weight changed to 72.25 kg -> BMI = 72.25 / 2.89 = 25.0)
        res_update = client.put(
            f"/api/v1/health-profiles/user/{user_id}",
            json={"weight_kg": 72.25, "activity_level": "active"},
        )
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["weight_kg"] == 72.25
        assert updated["activity_level"] == "active"
        assert updated["bmi"] == 25.0

        # 6. Delete profile
        res_del = client.delete(f"/api/v1/health-profiles/user/{user_id}")
        assert res_del.status_code == 200

        # 7. Verify profile is gone
        res_verify = client.get(f"/api/v1/health-profiles/user/{user_id}")
        assert res_verify.status_code == 404

    finally:
        # Cleanup user
        client.delete(f"/api/v1/users/{user_id}")


def test_create_profile_nonexistent_user():
    fake_user_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/health-profiles",
        json={"user_id": fake_user_id, "height_cm": 175.0, "weight_kg": 70.0},
    )
    assert res.status_code == 404


def test_invalid_health_profile_metrics():
    # Negative height or weight should be rejected with 422
    fake_user_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/health-profiles",
        json={"user_id": fake_user_id, "height_cm": -10, "weight_kg": 70},
    )
    assert res.status_code == 422

