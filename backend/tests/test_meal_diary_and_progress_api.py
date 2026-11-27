import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(prefix: str = "diary"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Diary Patient",
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


def test_meal_log_partially_eaten_preserves_recommendation_and_null_nutrients():
    """Verify partially_eaten meal log calculates proportional nutrition, keeps None nutrients as null, and leaves MealRecommendation untouched."""
    from app.db.session import SessionLocal
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    user_id, headers = _register_and_login("diary_part")
    null_food_id = None
    try:
        # 1. Create a food with fiber_g=None and sodium_mg=None to verify null preservation
        null_food_res = client.post(
            "/api/v1/foods",
            json={
                "name": f"Món test null vi chất {uuid.uuid4().hex[:6]}",
                "category": "protein",
                "serving_size_g": 100.0,
                "energy_kcal": 200.0,
                "carbohydrate_g": 0.0,
                "protein_g": 30.0,
                "fat_g": 8.0,
                "fiber_g": None,
                "sodium_mg": None,
                "is_test_data": True,
            },
        )
        assert null_food_res.status_code == 201, null_food_res.text
        null_food_id = null_food_res.json()["id"]

        # Manually ensure DB row has fiber_g=None (FoodBase defaults Decimal("0.00") if None passed? Let's check!)
        from app.models.food import Food
        db = SessionLocal()
        try:
            f_row = db.get(Food, uuid.UUID(null_food_id))
            f_row.fiber_g = None
            f_row.sodium_mg = None
            db.commit()
        finally:
            db.close()

        # 2. Generate original recommendation
        rec_res = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "lunch"},
            headers=headers,
        )
        assert rec_res.status_code == 200
        original_rec = rec_res.json()
        rec_id = original_rec["recommendation_id"]

        # 3. Log partially_eaten (50g out of 100g -> 0.5x = 100 kcal, 15g protein, fiber=None, sodium=None)
        today_str = datetime.now(timezone.utc).date().isoformat()
        log_res = client.post(
            "/api/v1/nutrition/meal-logs",
            json={
                "recommendation_id": rec_id,
                "meal_date": today_str,
                "meal_type": "lunch",
                "status": "partially_eaten",
                "notes": "Chỉ ăn một nửa khẩu phần",
                "items": [
                    {
                        "food_id": null_food_id,
                        "serving_g": 50.0,
                    }
                ],
            },
            headers=headers,
        )
        assert log_res.status_code == 201, log_res.text
        log_data = log_res.json()
        assert log_data["status"] == "partially_eaten"
        assert log_data["actual_nutrition"]["calories_kcal"] == 100.0
        assert log_data["actual_nutrition"]["protein_g"] == 15.0
        assert log_data["actual_nutrition"]["fat_g"] == 4.0
        assert log_data["actual_nutrition"]["fiber_g"] is None
        assert log_data["actual_nutrition"]["sodium_mg"] is None

        # 4. Verify original MealRecommendation snapshot was NOT mutated
        hist = client.get(
            f"/api/v1/nutrition/recommendations/user/{user_id}", headers=headers
        ).json()[0]["result"]
        assert hist["total_energy_kcal"] == original_rec["total_energy_kcal"]
        assert hist["items"] == original_rec["items"]
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)
        if null_food_id:
            client.delete(f"/api/v1/foods/{null_food_id}")


def test_meal_log_crud_ownership_and_recalculation():
    """Verify GET list/detail, PATCH recalculation, DELETE, and cross-user 403 guards."""
    from app.db.session import SessionLocal
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    owner_id, owner_headers = _register_and_login("log_owner")
    other_id, other_headers = _register_and_login("log_other")
    try:
        rice = client.get("/api/v1/foods?search=Gạo lứt nấu chín&limit=5").json()[0]
        today = datetime.now(timezone.utc).date()

        # 1. Create log with 150g brown rice (1.0x)
        create_res = client.post(
            "/api/v1/nutrition/meal-logs",
            json={
                "meal_date": today.isoformat(),
                "meal_type": "dinner",
                "status": "eaten",
                "items": [{"food_id": rice["id"], "serving_g": float(rice["serving_size_g"])}],
            },
            headers=owner_headers,
        )
        assert create_res.status_code == 201, create_res.text
        log = create_res.json()
        log_id = log["id"]
        assert abs(log["actual_nutrition"]["calories_kcal"] - rice["energy_kcal"]) < 0.05

        # 2. List with pagination & filters
        list_res = client.get(
            f"/api/v1/nutrition/meal-logs?date_from={today.isoformat()}&date_to={today.isoformat()}&meal_type=dinner&page=1&page_size=10",
            headers=owner_headers,
        )
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["id"] == log_id

        # 3. Cross-user GET / PATCH / DELETE -> 403 Forbidden
        assert client.get(f"/api/v1/nutrition/meal-logs/{log_id}", headers=other_headers).status_code == 403
        assert (
            client.patch(
                f"/api/v1/nutrition/meal-logs/{log_id}",
                json={"status": "skipped"},
                headers=other_headers,
            ).status_code
            == 403
        )
        assert client.delete(f"/api/v1/nutrition/meal-logs/{log_id}", headers=other_headers).status_code == 403

        # 4. Owner PATCH changes status to eaten_other and updates items -> recalculates actual_nutrition
        patch_res = client.patch(
            f"/api/v1/nutrition/meal-logs/{log_id}",
            json={
                "status": "eaten_other",
                "notes": "Ăn thêm yến mạch ngoài kế hoạch",
                "items": [
                    {
                        "custom_food_name": "Cháo yến mạch tự nấu",
                        "serving_g": 200.0,
                        "calories_kcal": 180.0,
                        "carbs_g": 30.0,
                        "protein_g": 6.0,
                        "fat_g": 3.5,
                        "fiber_g": 4.5,
                    }
                ],
            },
            headers=owner_headers,
        )
        assert patch_res.status_code == 200, patch_res.text
        patched = patch_res.json()
        assert patched["status"] == "eaten_other"
        assert patched["actual_nutrition"]["calories_kcal"] == 180.0
        assert patched["actual_nutrition"]["carbs_g"] == 30.0
        assert patched["actual_nutrition"]["fiber_g"] == 4.5
        assert patched["actual_nutrition"]["sodium_mg"] is None

        # 5. Owner DELETE
        del_res = client.delete(f"/api/v1/nutrition/meal-logs/{log_id}", headers=owner_headers)
        assert del_res.status_code == 200
        assert client.get(f"/api/v1/nutrition/meal-logs/{log_id}", headers=owner_headers).status_code == 404
    finally:
        client.delete(f"/api/v1/users/{owner_id}", headers=owner_headers)
        client.delete(f"/api/v1/users/{other_id}", headers=other_headers)


def test_weight_upsert_and_nutrition_progress_planned_vs_actual_and_empty_state():
    """Verify weight upsert syncs to HealthProfile, GET /progress handles empty state cleanly, and aggregates planned vs actual."""
    from app.db.session import SessionLocal
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        seed_vn_foods(db)
    finally:
        db.close()

    user_id, headers = _register_and_login("prog")
    try:
        # 1. Empty state check (brand new user, no logs, no weights, no recommendations)
        empty_prog = client.get("/api/v1/nutrition/progress", headers=headers)
        assert empty_prog.status_code == 200, empty_prog.text
        empty_data = empty_prog.json()
        assert empty_data["summary"]["total_meals_logged"] == 0
        assert empty_data["summary"]["total_meals_skipped"] == 0
        assert empty_data["summary"]["meal_logging_rate"] == 0.0
        assert empty_data["nutrition_trends"] == []
        assert empty_data["weight"]["latest_kg"] is None
        assert empty_data["weight"]["previous_kg"] is None
        assert empty_data["weight"]["records"] == []

        # 2. Setup HealthProfile + upsert weight on 2 days (same date twice -> no duplicate)
        client.put(
            "/api/v1/health-profiles/me",
            json={
                "date_of_birth": "1988-02-10",
                "sex": "male",
                "height_cm": 170.0,
                "weight_kg": 72.0,
                "activity_level": "moderate",
            },
            headers=headers,
        )
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        w1 = client.post(
            "/api/v1/nutrition/progress/weight",
            json={"weight_kg": 71.5, "recorded_at": yesterday.isoformat()},
            headers=headers,
        )
        assert w1.status_code == 200

        w2 = client.post(
            "/api/v1/nutrition/progress/weight",
            json={"weight_kg": 71.0, "recorded_at": today.isoformat()},
            headers=headers,
        )
        w2_upd = client.post(
            "/api/v1/nutrition/progress/weight",
            json={"weight_kg": 70.6, "recorded_at": today.isoformat()},
            headers=headers,
        )
        assert w2.status_code == 200 and w2_upd.status_code == 200

        weights_list = client.get("/api/v1/nutrition/progress/weight", headers=headers).json()
        assert len(weights_list) == 2
        assert weights_list[0]["weight_kg"] == 71.5
        assert weights_list[1]["weight_kg"] == 70.6

        # Verify HealthProfile weight_kg synced to latest (70.6)
        hp_after = client.get("/api/v1/health-profiles/me", headers=headers).json()
        assert hp_after["weight_kg"] == 70.6

        # 3. Generate a planned lunch today + log 1 eaten meal and 1 skipped meal
        rec = client.post(
            "/api/v1/nutrition/recommend",
            json={"user_id": user_id, "meal_type": "lunch"},
            headers=headers,
        ).json()

        rice = client.get("/api/v1/foods?search=Gạo lứt nấu chín&limit=5").json()[0]
        client.post(
            "/api/v1/nutrition/meal-logs",
            json={
                "recommendation_id": rec["recommendation_id"],
                "meal_date": today.isoformat(),
                "meal_type": "lunch",
                "status": "eaten",
                "items": [{"food_id": rice["id"], "serving_g": float(rice["serving_size_g"])}],
            },
            headers=headers,
        )
        client.post(
            "/api/v1/nutrition/meal-logs",
            json={
                "meal_date": today.isoformat(),
                "meal_type": "snack",
                "status": "skipped",
                "items": [],
            },
            headers=headers,
        )

        # 4. Verify GET /nutrition/progress aggregates everything accurately
        prog = client.get("/api/v1/nutrition/progress", headers=headers)
        assert prog.status_code == 200, prog.text
        prog_data = prog.json()
        assert prog_data["summary"]["total_meals_logged"] == 1
        assert prog_data["summary"]["total_meals_skipped"] == 1
        assert prog_data["summary"]["meal_logging_rate"] == 0.5

        today_trend = next(
            t for t in prog_data["nutrition_trends"] if t["date"] == today.isoformat()
        )
        assert abs(today_trend["planned_calories_kcal"] - rec["total_energy_kcal"]) < 0.05
        assert abs(today_trend["actual_calories_kcal"] - rice["energy_kcal"]) < 0.05
        assert abs(today_trend["planned_carbs_g"] - rec["total_carbohydrate_g"]) < 0.05
        assert abs(today_trend["actual_carbs_g"] - rice["carbohydrate_g"]) < 0.05

        assert prog_data["weight"]["latest_kg"] == 70.6
        assert prog_data["weight"]["previous_kg"] == 71.5
        assert len(prog_data["weight"]["records"]) == 2
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)
