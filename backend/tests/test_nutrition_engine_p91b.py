import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_test_user(email_prefix: str = "p91b") -> str:
    res = client.post(
        "/api/v1/users",
        json={
            "email": f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com",
            "full_name": "Test Patient P91B",
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_ckd_abstention_on_recommend_and_daily():
    uid = _create_test_user("ckd")
    res = client.post(
        "/api/v1/nutrition/recommend",
        json={
            "user_id": uid,
            "meal_type": "lunch",
            "comorbidities": ["CKD stage 3", "type2"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_abstained"] is True
    assert data["items"] == []
    assert "thận" in data["abstention_reason"].lower()

    daily_res = client.post(
        "/api/v1/nutrition/recommend-daily",
        json={
            "user_id": uid,
            "comorbidities": ["bệnh thận mạn"],
        },
    )
    assert daily_res.status_code == 200
    assert daily_res.json()["is_abstained"] is True


def test_incomplete_profile_abstention_when_required():
    uid = _create_test_user("incomplete")
    res = client.post(
        "/api/v1/nutrition/recommend",
        json={
            "user_id": uid,
            "meal_type": "dinner",
            "require_complete_profile": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_abstained"] is True
    assert len(data["missing_profile_fields"]) == 5


def test_allergy_exclusion_and_no_unsafe_fallback():
    uid = _create_test_user("allergy")
    # Strict allergy: Hải sản, Đậu nành, Trứng
    res = client.post(
        "/api/v1/nutrition/recommend-daily",
        json={
            "user_id": uid,
            "allergies": ["Hải sản", "Đậu nành", "Trứng"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_abstained"] is False
    forbidden = ["tôm", "cá", "đậu phụ", "đậu hũ", "trứng", "hải sản"]
    for meal in data["meals"].values():
        for item in meal["items"]:
            name_l = item["food_name"].lower()
            assert not any(f in name_l for f in forbidden), f"Allergen leaked: {item['food_name']}"

    # If everything is excluded, must abstain rather than returning unsafe foods
    impossible_res = client.post(
        "/api/v1/nutrition/recommend",
        json={
            "user_id": uid,
            "meal_type": "lunch",
            "excluded_keywords": ["a", "e", "i", "o", "u", "ă", "â", "ê", "ô", "ơ", "ư"],
        },
    )
    assert impossible_res.status_code == 200
    assert impossible_res.json()["is_abstained"] is True
    assert impossible_res.json()["items"] == []


def test_daily_meal_plan_calculation_accuracy():
    uid = _create_test_user("daily")
    res = client.post(
        "/api/v1/nutrition/recommend-daily",
        json={
            "user_id": uid,
            "comorbidities": ["hypertension"],
            "nutrition_goal": "weight_loss",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_abstained"] is False
    assert set(data["meals"].keys()) == {"breakfast", "lunch", "dinner", "snack"}

    calc_kcal = round(sum(m["total_energy_kcal"] for m in data["meals"].values()), 1)
    calc_carb = round(sum(m["total_carbohydrate_g"] for m in data["meals"].values()), 1)
    calc_sodium = round(sum(m["total_sodium_mg"] for m in data["meals"].values()), 1)

    assert abs(data["daily_total_energy_kcal"] - calc_kcal) < 0.2
    assert abs(data["daily_total_carbohydrate_g"] - calc_carb) < 0.2
    assert abs(data["daily_total_sodium_mg"] - calc_sodium) < 0.2
    assert sum(data["macro_distribution_pct"].values()) > 98.0


def test_food_substitution_api():
    uid = _create_test_user("sub")
    # Pick a food from /foods
    foods_res = client.get("/api/v1/foods?category=protein&limit=10")
    assert foods_res.status_code == 200
    foods = foods_res.json()
    assert len(foods) >= 2

    target_food_id = foods[0]["id"]
    sub_res = client.post(
        "/api/v1/nutrition/substitute",
        json={
            "user_id": uid,
            "food_id_to_replace": target_food_id,
            "meal_type": "lunch",
            "allergies": ["Hải sản"],
            "limit": 3,
        },
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["original_food_id"] == target_food_id
    for s in sub_data["substitutes"]:
        assert s["food_id"] != target_food_id
        assert s["category"] == "protein"
        assert "tôm" not in s["food_name"].lower()
        assert "cá" not in s["food_name"].lower()
