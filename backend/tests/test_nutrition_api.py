import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_meal_recommendation_lifecycle_and_history():
    # 1. Create a user
    test_email = f"nutri_{uuid.uuid4().hex[:8]}@example.com"
    user_res = client.post(
        "/api/v1/users",
        json={"email": test_email, "display_name": "Nutrition Patient"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    try:
        # 2. Create health profile
        profile_res = client.post(
            "/api/v1/health-profiles",
            json={
                "user_id": user_id,
                "height_cm": 168.0,
                "weight_kg": 65.0,
                "diabetes_type": "type2",
                "activity_level": "moderate",
            },
        )
        assert profile_res.status_code == 201

        # 3. Generate Lunch Recommendation
        req_payload = {
            "user_id": user_id,
            "meal_type": "lunch",
            "custom_target": {
                "target_energy_kcal": 500.0,
                "max_carbohydrate_g": 50.0,
            },
        }
        rec_res = client.post("/api/v1/nutrition/recommend", json=req_payload)
        assert rec_res.status_code == 200, rec_res.text
        rec_data = rec_res.json()

        assert rec_data["user_id"] == user_id
        assert rec_data["meal_type"] == "lunch"
        assert len(rec_data["items"]) >= 2
        assert rec_data["total_energy_kcal"] > 0
        assert rec_data["total_carbohydrate_g"] > 0
        assert "clinical_safety_disclaimer" in rec_data
        assert "Plate Method" in rec_data["clinical_safety_disclaimer"]

        # 4. Generate Vegetarian Recommendation
        veg_req = {
            "user_id": user_id,
            "meal_type": "lunch",
            "dietary_preference": "vegetarian",
        }
        veg_res = client.post("/api/v1/nutrition/recommend", json=veg_req)
        assert veg_res.status_code == 200
        veg_items = veg_res.json()["items"]
        item_names = [i["food_name"].lower() for i in veg_items]
        # Should not contain chicken or salmon
        assert not any("gà" in n or "hồi" in n for n in item_names)

        # 5. Check recommendation history endpoint
        hist_res = client.get(f"/api/v1/nutrition/recommendations/user/{user_id}")
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert len(history) >= 2
        assert history[0]["meal_type"] in ["lunch", "dinner", "breakfast", "snack"]

    finally:
        # Cleanup user (cascades delete to profile, recommendations, items)
        client.delete(f"/api/v1/users/{user_id}")


def test_recommendation_nonexistent_user():
    fake_user_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/nutrition/recommend",
        json={"user_id": fake_user_id, "meal_type": "lunch"},
    )
    assert res.status_code == 404


def test_recommendation_invalid_meal_type():
    fake_user_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/nutrition/recommend",
        json={"user_id": fake_user_id, "meal_type": "midnight_buffet"},
    )
    assert res.status_code == 422

