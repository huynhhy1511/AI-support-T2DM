import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_sample_foods():
    client.post("/api/v1/foods/seed-sample")


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

        # 4b. Generate Vegan Recommendation (should exclude meats, chicken, salmon, eggs, and dairy)
        vegan_req = {
            "user_id": user_id,
            "meal_type": "lunch",
            "dietary_preference": "vegan",
        }
        vegan_res = client.post("/api/v1/nutrition/recommend", json=vegan_req)
        assert vegan_res.status_code == 200
        vegan_items = vegan_res.json()["items"]
        vegan_names = [i["food_name"].lower() for i in vegan_items]
        assert not any(
            "gà" in n or "hồi" in n or "trứng" in n or "sữa" in n for n in vegan_names
        )

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


def test_recommendation_all_foods_excluded_no_unsafe_fallback():
    """Verify that when all foods are excluded (e.g. severe allergies/restrictions), system returns empty items, NEVER falling back to all foods."""
    test_email = f"no_fallback_{uuid.uuid4().hex[:8]}@example.com"
    user_res = client.post(
        "/api/v1/users",
        json={"email": test_email, "display_name": "Allergy Patient"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    try:
        # Exclude all 14 sample foods in DB by keywords
        all_food_keywords = [
            "gạo", "yến mạch", "khoai", "cơm", "ức gà", "cá hồi",
            "đậu phụ", "trứng", "bông cải", "rau muống", "dưa chuột",
            "táo", "sữa chua", "hạnh nhân"
        ]
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={
                "user_id": user_id,
                "meal_type": "lunch",
                "excluded_keywords": all_food_keywords,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total_energy_kcal"] == 0.0
        assert data["total_carbohydrate_g"] == 0.0
        assert "Không tìm thấy thực phẩm phù hợp với các ràng buộc an toàn" in data["meal_balance_evaluation"]
        assert any("Cảnh báo an toàn" in note for note in data["safety_notes"])

    finally:
        client.delete(f"/api/v1/users/{user_id}")


def test_recommendation_user_allergy_specific_food():
    """Verify that when user specifies an allergy keyword (e.g. ức gà), that food is never recommended while safe foods are."""
    test_email = f"allergy_{uuid.uuid4().hex[:8]}@example.com"
    user_res = client.post(
        "/api/v1/users",
        json={"email": test_email, "display_name": "Chicken Allergy Patient"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={
                "user_id": user_id,
                "meal_type": "lunch",
                "excluded_keywords": ["ức gà", "chicken"],
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) >= 2
        for item in data["items"]:
            name_lower = item["food_name"].lower()
            assert "ức gà" not in name_lower
            assert "chicken" not in name_lower

    finally:
        client.delete(f"/api/v1/users/{user_id}")


def test_recommendation_does_not_auto_seed_when_db_empty():
    """Verify that when foods table is empty, generate_recommendation returns empty items and does NOT seed the database."""
    from unittest.mock import MagicMock
    from app.models.food import Food
    from app.schemas.nutrition import MealRecommendationRequest
    from app.services.nutrition_service import generate_recommendation

    mock_db = MagicMock()
    # Mock empty database: no profile and no foods
    mock_db.scalars.return_value.first.return_value = None
    mock_db.scalars.return_value.all.return_value = []
    mock_db.query.return_value.count.return_value = 0

    req = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
    )

    result = generate_recommendation(mock_db, req)

    # 1. Recommendation is safely empty
    assert result.items == []
    assert result.total_energy_kcal == 0.0
    assert "Không tìm thấy thực phẩm phù hợp" in result.meal_balance_evaluation

    # 2. Database was NOT seeded with Food instances
    added_objects = [call[0][0] for call in mock_db.add.call_args_list if call[0]]
    assert not any(isinstance(obj, Food) for obj in added_objects)
    assert mock_db.query(Food).count() == 0


def test_recommendation_dynamic_portion_api_and_persistence():
    """Verify API scales portion dynamically for custom_target and total nutrients match scaled items."""
    test_email = f"portion_{uuid.uuid4().hex[:8]}@example.com"
    user_res = client.post(
        "/api/v1/users",
        json={"email": test_email, "display_name": "Portion Patient"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={
                "user_id": user_id,
                "meal_type": "lunch",
                "custom_target": {
                    "target_energy_kcal": 600.0,
                    "target_carbohydrate_g": 45.0,
                },
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) >= 2

        # Verify total_energy_kcal matches sum of item energy_kcal (no double multiplication)
        sum_item_kcal = round(sum(i["energy_kcal"] for i in data["items"]), 2)
        assert abs(data["total_energy_kcal"] - sum_item_kcal) < 0.05

        sum_item_carb = round(sum(i["carbohydrate_g"] for i in data["items"]), 2)
        assert abs(data["total_carbohydrate_g"] - sum_item_carb) < 0.05

        # Multiplier must be within [0.5, 2.0]
        for item in data["items"]:
            assert 0.5 <= item["serving_multiplier"] <= 2.0
    finally:
        client.delete(f"/api/v1/users/{user_id}")



