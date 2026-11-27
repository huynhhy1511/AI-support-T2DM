import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_sample_foods():
    client.post("/api/v1/foods/seed-sample")


def _register_and_login(prefix: str = "nutri"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Nutrition Patient",
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


def test_meal_recommendation_lifecycle_and_history():
    # 1. Register & login user
    user_id, headers = _register_and_login("nutri")

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
            headers=headers,
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
        rec_res = client.post(
            "/api/v1/nutrition/recommend", json=req_payload, headers=headers
        )
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
        veg_res = client.post(
            "/api/v1/nutrition/recommend", json=veg_req, headers=headers
        )
        assert veg_res.status_code == 200
        veg_items = veg_res.json()["items"]
        item_names = [i["food_name"].lower() for i in veg_items]
        assert not any("gà" in n or "hồi" in n for n in item_names)

        # 4b. Generate Vegan Recommendation (should exclude meats, chicken, salmon, eggs, and dairy)
        vegan_req = {
            "user_id": user_id,
            "meal_type": "lunch",
            "dietary_preference": "vegan",
        }
        vegan_res = client.post(
            "/api/v1/nutrition/recommend", json=vegan_req, headers=headers
        )
        assert vegan_res.status_code == 200
        vegan_items = vegan_res.json()["items"]
        vegan_names = [i["food_name"].lower() for i in vegan_items]
        assert not any(
            "gà" in n or "hồi" in n or "trứng" in n or "sữa" in n for n in vegan_names
        )

        # 5. Check recommendation history endpoint
        hist_res = client.get(
            f"/api/v1/nutrition/recommendations/user/{user_id}", headers=headers
        )
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert len(history) >= 2
        assert history[0]["meal_type"] in ["lunch", "dinner", "breakfast", "snack"]

    finally:
        # Cleanup user (cascades delete to profile, recommendations, items)
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_nonexistent_user():
    user_id, headers = _register_and_login("nonexist_rec")
    fake_user_id = str(uuid.uuid4())
    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": fake_user_id, "meal_type": "lunch"},
            headers=headers,
        )
        assert res.status_code == 403
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_invalid_meal_type():
    user_id, headers = _register_and_login("invalid_meal")
    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "midnight_buffet"},
            headers=headers,
        )
        assert res.status_code == 422
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_all_foods_excluded_no_unsafe_fallback():
    """Verify that when all foods are excluded (e.g. severe allergies/restrictions), system returns empty items, NEVER falling back to all foods."""
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models.food import Food

    user_id, headers = _register_and_login("no_fallback")

    db = SessionLocal()
    try:
        all_food_ids = [str(fid) for fid in db.scalars(select(Food.id)).all()]
    finally:
        db.close()

    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={
                "user_id": user_id,
                "meal_type": "lunch",
                "excluded_food_ids": all_food_ids,
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total_energy_kcal"] == 0.0
        assert data["total_carbohydrate_g"] == 0.0
        assert "Không tìm thấy thực phẩm phù hợp với các ràng buộc an toàn" in data["meal_balance_evaluation"]
        assert any("Cảnh báo an toàn" in note for note in data["safety_notes"])

    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_user_allergy_specific_food():
    """Verify that when user specifies an allergy keyword (e.g. ức gà), that food is never recommended while safe foods are."""
    user_id, headers = _register_and_login("allergy")

    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={
                "user_id": user_id,
                "meal_type": "lunch",
                "excluded_keywords": ["ức gà", "chicken"],
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) >= 2
        for item in data["items"]:
            name_lower = item["food_name"].lower()
            assert "ức gà" not in name_lower
            assert "chicken" not in name_lower

    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_does_not_auto_seed_when_db_empty():
    """Verify that when foods table is empty, generate_recommendation returns empty items and does NOT seed the database."""
    from unittest.mock import MagicMock
    from app.models.food import Food
    from app.schemas.nutrition import MealRecommendationRequest
    from app.services.nutrition_service import generate_recommendation

    mock_db = MagicMock()
    mock_db.scalars.return_value.first.return_value = None
    mock_db.scalars.return_value.all.return_value = []
    mock_db.query.return_value.count.return_value = 0

    req = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
    )

    result = generate_recommendation(mock_db, req)

    assert result.items == []
    assert result.total_energy_kcal == 0.0
    assert "Không tìm thấy thực phẩm phù hợp" in result.meal_balance_evaluation

    added_objects = [call[0][0] for call in mock_db.add.call_args_list if call[0]]
    assert not any(isinstance(obj, Food) for obj in added_objects)
    assert mock_db.query(Food).count() == 0


def test_recommendation_dynamic_portion_api_and_persistence():
    """Verify API scales portion dynamically for custom_target and total nutrients match scaled items."""
    user_id, headers = _register_and_login("portion")

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
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) >= 2

        sum_item_kcal = round(sum(i["energy_kcal"] for i in data["items"]), 2)
        assert abs(data["total_energy_kcal"] - sum_item_kcal) < 0.05

        sum_item_carb = round(sum(i["carbohydrate_g"] for i in data["items"]), 2)
        assert abs(data["total_carbohydrate_g"] - sum_item_carb) < 0.05

        for item in data["items"]:
            assert 0.5 <= item["serving_multiplier"] <= 2.0
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_structured_allergen_filtering_api():
    """Verify recommendation API excludes all foods tagged with user's declared allergens (shellfish, soy, egg)."""
    from app.db.session import SessionLocal
    from app.models.food import Food
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    user_id, headers = _register_and_login("allergen_api")
    try:
        res = client.post(
            "/api/v1/nutrition/recommend",
            json={
                "user_id": user_id,
                "meal_type": "lunch",
                "excluded_allergens": ["shellfish", "soy", "egg"],
            },
            headers=headers,
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data["items"]) >= 2

        db = SessionLocal()
        try:
            for item in data["items"]:
                food = db.get(Food, uuid.UUID(item["food_id"]))
                assert food is not None
                codes = {a.code for a in food.allergens}
                assert not (codes & {"shellfish", "soy", "egg"})
        finally:
            db.close()
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_recommendation_ckd_abstention_and_profile_allergies():
    """Verify CKD comorbidity triggers HTTP 200 abstained response without DB persistence, and profile allergies filter foods."""
    from app.db.session import SessionLocal
    from app.models.food import Food
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    user_id, headers = _register_and_login("ckd_guard")
    try:
        # 1. Set profile with CKD comorbidity
        hp_res = client.put(
            "/api/v1/health-profiles/me",
            json={
                "date_of_birth": "1975-03-10",
                "sex": "female",
                "height_cm": 158.0,
                "weight_kg": 60.0,
                "activity_level": "light",
                "comorbidities": ["ckd"],
                "allergies": ["shellfish", "soy"],
            },
            headers=headers,
        )
        assert hp_res.status_code == 200

        # 2. Request recommendation -> HTTP 200 abstained, CKD_SPECIALIST_REQUIRED, no DB record saved
        abstain_res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "lunch"},
            headers=headers,
        )
        assert abstain_res.status_code == 200, abstain_res.text
        abstain_data = abstain_res.json()
        assert abstain_data["status"] == "abstained"
        assert abstain_data["reason_code"] == "CKD_SPECIALIST_REQUIRED"
        assert abstain_data["items"] == []
        assert abstain_data["total_energy_kcal"] == 0.0

        hist_after_abstain = client.get(
            f"/api/v1/nutrition/recommendations/user/{user_id}", headers=headers
        )
        assert hist_after_abstain.status_code == 200
        assert hist_after_abstain.json() == []

        # 3. Remove CKD (keep allergies=["shellfish", "soy"]) -> generated & respects profile allergies
        upd_res = client.put(
            "/api/v1/health-profiles/me",
            json={"comorbidities": ["hypertension"]},
            headers=headers,
        )
        assert upd_res.status_code == 200

        gen_res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "lunch"},
            headers=headers,
        )
        assert gen_res.status_code == 200, gen_res.text
        gen_data = gen_res.json()
        assert gen_data["status"] == "generated"
        assert gen_data["reason_code"] is None
        assert len(gen_data["items"]) >= 2

        db = SessionLocal()
        try:
            for item in gen_data["items"]:
                food = db.get(Food, uuid.UUID(item["food_id"]))
                assert food is not None
                codes = {a.code for a in food.allergens}
                assert not (codes & {"shellfish", "soy"})
        finally:
            db.close()
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_nutrition_safety_alerts_endpoint():
    """Verify GET /nutrition/safety-alerts flags missing fields, CKD block, hypertension, and BMI."""
    user_id, headers = _register_and_login("safety_alerts")
    try:
        # 1. No profile yet -> MISSING_PROFILE_FIELDS
        res_empty = client.get("/api/v1/nutrition/safety-alerts", headers=headers)
        assert res_empty.status_code == 200, res_empty.text
        empty_data = res_empty.json()
        assert empty_data["is_profile_complete"] is False
        assert empty_data["has_blocking_condition"] is False
        assert any(a["code"] == "MISSING_PROFILE_FIELDS" for a in empty_data["alerts"])

        # 2. Complete profile with CKD + hypertension + obese BMI (>= 30)
        hp_res = client.put(
            "/api/v1/health-profiles/me",
            json={
                "date_of_birth": "1980-05-01",
                "sex": "male",
                "height_cm": 165.0,
                "weight_kg": 90.0,
                "activity_level": "sedentary",
                "comorbidities": ["ckd", "hypertension"],
            },
            headers=headers,
        )
        assert hp_res.status_code == 200

        res_alerts = client.get("/api/v1/nutrition/safety-alerts", headers=headers)
        assert res_alerts.status_code == 200
        alerts_data = res_alerts.json()
        assert alerts_data["is_profile_complete"] is True
        assert alerts_data["has_blocking_condition"] is True
        assert alerts_data["bmi_category"] == "obese"
        codes = {a["code"] for a in alerts_data["alerts"]}
        assert "CKD_SPECIALIST_REQUIRED" in codes
        assert "HYPERTENSION_SODIUM_LIMIT" in codes
        assert "BMI_OBESE" in codes
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_food_alternatives_filters_category_and_user_allergies():
    """Verify GET /foods/{id}/alternatives returns same-category foods excluding original and user allergies."""
    from app.db.session import SessionLocal
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    user_id, headers = _register_and_login("food_alt")
    try:
        # User is allergic to shellfish and soy
        hp_res = client.put(
            "/api/v1/health-profiles/me",
            json={"allergies": ["shellfish", "soy"]},
            headers=headers,
        )
        assert hp_res.status_code == 200

        # Pick a protein food (chicken breast)
        search_res = client.get("/api/v1/foods?search=Ức gà phi lê&limit=10")
        assert search_res.status_code == 200
        chicken = search_res.json()[0]

        alt_res = client.get(
            f"/api/v1/foods/{chicken['id']}/alternatives?limit=8", headers=headers
        )
        assert alt_res.status_code == 200, alt_res.text
        alternatives = alt_res.json()
        assert 1 <= len(alternatives) <= 8
        for alt in alternatives:
            assert alt["id"] != chicken["id"]
            assert alt["category"] == chicken["category"]
            assert "similarity_reason" in alt and alt["similarity_reason"]
            assert "kcal_diff" in alt
            allergen_codes = {a["code"] for a in alt["allergens"]}
            assert not (allergen_codes & {"shellfish", "soy"})

        # Nonexistent food returns 404
        not_found = client.get(
            f"/api/v1/foods/{uuid.uuid4()}/alternatives", headers=headers
        )
        assert not_found.status_code == 404
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_food_substitution_success_allergy_block_and_ownership():
    """Verify POST /nutrition/recommendations/{id}/substitutions updates totals safely, blocks allergies (400), and blocks cross-user (403)."""
    from app.db.session import SessionLocal
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    user_id, headers = _register_and_login("sub_owner")
    other_id, other_headers = _register_and_login("sub_other")
    try:
        # 1. Owner declares shellfish allergy
        client.put(
            "/api/v1/health-profiles/me",
            json={"allergies": ["shellfish"]},
            headers=headers,
        )

        # 2. Generate lunch recommendation
        gen_res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "lunch"},
            headers=headers,
        )
        assert gen_res.status_code == 200, gen_res.text
        rec = gen_res.json()
        rec_id = rec["recommendation_id"]
        protein_item = next(i for i in rec["items"] if i["category"] == "protein")

        # 3. Find a safe alternative protein and a shellfish protein (shrimp)
        alt_res = client.get(
            f"/api/v1/foods/{protein_item['food_id']}/alternatives?limit=5",
            headers=headers,
        )
        assert alt_res.status_code == 200
        safe_alt = alt_res.json()[0]

        shrimp_res = client.get("/api/v1/foods?search=Tôm sú&limit=5")
        shrimp = next(i for i in shrimp_res.json() if "Tôm sú" in i["name"])

        # 4. Cross-user substitution attempt -> 403 Forbidden
        forbidden_res = client.post(
            f"/api/v1/nutrition/recommendations/{rec_id}/substitutions",
            json={
                "original_food_id": protein_item["food_id"],
                "replacement_food_id": safe_alt["id"],
            },
            headers=other_headers,
        )
        assert forbidden_res.status_code == 403

        # 5. Allergen-violating substitution attempt -> 400 Bad Request, original unchanged
        bad_allergy_res = client.post(
            f"/api/v1/nutrition/recommendations/{rec_id}/substitutions",
            json={
                "original_food_id": protein_item["food_id"],
                "replacement_food_id": shrimp["id"],
            },
            headers=headers,
        )
        assert bad_allergy_res.status_code == 400

        # Verify DB still has original protein_item unchanged
        hist_check = client.get(
            f"/api/v1/nutrition/recommendations/user/{user_id}", headers=headers
        ).json()[0]["result"]
        assert any(i["food_id"] == protein_item["food_id"] for i in hist_check["items"])

        # 6. Valid substitution -> 200 OK, totals recalculated accurately and persisted
        sub_res = client.post(
            f"/api/v1/nutrition/recommendations/{rec_id}/substitutions",
            json={
                "original_food_id": protein_item["food_id"],
                "replacement_food_id": safe_alt["id"],
            },
            headers=headers,
        )
        assert sub_res.status_code == 200, sub_res.text
        updated = sub_res.json()
        updated_ids = [i["food_id"] for i in updated["items"]]
        assert safe_alt["id"] in updated_ids
        assert protein_item["food_id"] not in updated_ids

        assert abs(
            updated["total_energy_kcal"]
            - round(sum(i["energy_kcal"] for i in updated["items"]), 2)
        ) < 0.05
        assert abs(
            updated["total_carbohydrate_g"]
            - round(sum(i["carbohydrate_g"] for i in updated["items"]), 2)
        ) < 0.05
        assert abs(
            updated["total_sodium_mg"]
            - round(sum(i["sodium_mg"] for i in updated["items"] if i["sodium_mg"] is not None), 2)
        ) < 0.05
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)
        client.delete(f"/api/v1/users/{other_id}", headers=other_headers)


def test_daily_recommendations_today_and_empty_state():
    """Verify GET /nutrition/recommendations/today returns empty state initially and aggregates daily meals."""
    user_id, headers = _register_and_login("daily_rec")
    try:
        # 1. Empty state before generating any meal
        empty_res = client.get(
            "/api/v1/nutrition/recommendations/today", headers=headers
        )
        assert empty_res.status_code == 200, empty_res.text
        empty_data = empty_res.json()
        assert empty_data["meals"] == []
        assert empty_data["daily_summary"]["meals_count"] == 0
        assert empty_data["daily_summary"]["total_energy_kcal"] == 0.0

        # 2. Generate breakfast and lunch
        b_res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "breakfast"},
            headers=headers,
        )
        l_res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "lunch"},
            headers=headers,
        )
        assert b_res.status_code == 200 and l_res.status_code == 200

        # 3. Fetch today's recommendations -> returns breakfast + lunch + daily_summary
        today_res = client.get(
            "/api/v1/nutrition/recommendations/today", headers=headers
        )
        assert today_res.status_code == 200, today_res.text
        today_data = today_res.json()
        assert len(today_data["meals"]) == 2
        assert [m["meal_type"] for m in today_data["meals"]] == ["breakfast", "lunch"]
        expected_kcal = round(
            b_res.json()["total_energy_kcal"] + l_res.json()["total_energy_kcal"], 2
        )
        assert abs(today_data["daily_summary"]["total_energy_kcal"] - expected_kcal) < 0.05
        assert today_data["daily_summary"]["meals_count"] == 2

        # 4. Past date with no data -> HTTP 200 empty state
        past_res = client.get(
            "/api/v1/nutrition/recommendations/today?target_date=2020-01-01",
            headers=headers,
        )
        assert past_res.status_code == 200
        assert past_res.json()["meals"] == []
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)



