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


def test_health_profile_me_upsert_completeness_and_energy_calculator():
    """Verify /health-profiles/me, /completeness, and automatic Mifflin-St Jeor BMR/TDEE/target_energy calculation."""
    user_id, headers = _register_and_login("hp_me")
    try:
        # 1. Before profile exists: GET /me -> 404, GET /me/completeness -> incomplete with all 5 fields
        res_missing = client.get("/api/v1/health-profiles/me", headers=headers)
        assert res_missing.status_code == 404

        comp_before = client.get(
            "/api/v1/health-profiles/me/completeness", headers=headers
        )
        assert comp_before.status_code == 200
        comp_before_data = comp_before.json()
        assert comp_before_data["is_complete"] is False
        assert set(comp_before_data["missing_fields"]) == {
            "date_of_birth",
            "sex",
            "height_cm",
            "weight_kg",
            "activity_level",
        }
        assert comp_before_data["target_energy_kcal"] is None

        # 2. PUT /me creates profile and computes BMR/TDEE/target_energy_kcal
        upsert_create = client.put(
            "/api/v1/health-profiles/me",
            json={
                "date_of_birth": "1990-01-15",
                "sex": "male",
                "height_cm": 170.0,
                "weight_kg": 70.0,
                "activity_level": "moderate",
                "nutrition_goal": "maintenance",
                "comorbidities": ["hypertension"],
                "allergies": ["shellfish", "peanut"],
            },
            headers=headers,
        )
        assert upsert_create.status_code == 200, upsert_create.text
        created = upsert_create.json()
        assert created["user_id"] == user_id
        assert created["nutrition_goal"] == "maintenance"
        assert created["comorbidities"] == ["hypertension"]
        assert created["allergies"] == ["shellfish", "peanut"]
        assert created["bmr_kcal"] is not None and created["bmr_kcal"] > 0
        assert created["tdee_kcal"] == round(created["bmr_kcal"] * 1.55, 1)
        assert created["target_energy_kcal"] == created["tdee_kcal"]

        # 3. GET /me & GET /me/completeness now return complete profile
        get_me = client.get("/api/v1/health-profiles/me", headers=headers)
        assert get_me.status_code == 200
        assert get_me.json()["id"] == created["id"]

        comp_after = client.get(
            "/api/v1/health-profiles/me/completeness", headers=headers
        )
        assert comp_after.status_code == 200
        comp_after_data = comp_after.json()
        assert comp_after_data["is_complete"] is True
        assert comp_after_data["missing_fields"] == []
        assert comp_after_data["bmi"] == 24.22
        assert comp_after_data["target_energy_kcal"] == created["target_energy_kcal"]

        # 4. PUT /me updates nutrition_goal to weight_loss -> reduces target by 400 kcal (above floor)
        upsert_update = client.put(
            "/api/v1/health-profiles/me",
            json={"nutrition_goal": "weight_loss"},
            headers=headers,
        )
        assert upsert_update.status_code == 200
        updated = upsert_update.json()
        assert updated["nutrition_goal"] == "weight_loss"
        assert updated["target_energy_kcal"] == round(
            max(1400.0, updated["tdee_kcal"] - 400.0), 1
        )
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)

