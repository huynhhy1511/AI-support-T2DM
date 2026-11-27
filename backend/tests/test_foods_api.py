import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_seed_sample_foods_and_list():
    # 1. Trigger seed
    seed_res = client.post("/api/v1/foods/seed-sample")
    assert seed_res.status_code == 200

    # 2. List foods
    list_res = client.get("/api/v1/foods?limit=50")
    assert list_res.status_code == 200
    foods = list_res.json()
    assert len(foods) > 0

    # 3. Filter by category
    staple_res = client.get("/api/v1/foods?category=staple")
    assert staple_res.status_code == 200
    staples = staple_res.json()
    assert all(f["category"] == "staple" for f in staples)

    # 4. Search by name
    search_res = client.get("/api/v1/foods?search=Gạo")
    assert search_res.status_code == 200
    search_items = search_res.json()
    assert any("Gạo" in f["name"] for f in search_items)


def test_food_crud_lifecycle():
    food_payload = {
        "name": "Thực phẩm kiểm thử độc lập",
        "category": "vegetables",
        "serving_size_g": 100.0,
        "energy_kcal": 25.0,
        "carbohydrate_g": 4.0,
        "protein_g": 2.0,
        "fat_g": 0.2,
        "fiber_g": 2.5,
        "sugar_g": 1.0,
        "glycemic_index": 20.0,
        "glycemic_load": 0.8,
        "is_test_data": True,
        "source_name": "Test Lab",
    }

    # 1. Create
    create_res = client.post("/api/v1/foods", json=food_payload)
    assert create_res.status_code == 201, create_res.text
    food_data = create_res.json()
    food_id = food_data["id"]
    assert food_data["name"] == "Thực phẩm kiểm thử độc lập"

    try:
        # 2. Get by ID
        get_res = client.get(f"/api/v1/foods/{food_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == food_id

        # 3. Update
        update_res = client.put(
            f"/api/v1/foods/{food_id}",
            json={"energy_kcal": 30.0, "fiber_g": 3.0},
        )
        assert update_res.status_code == 200
        assert update_res.json()["energy_kcal"] == 30.0
        assert update_res.json()["fiber_g"] == 3.0

    finally:
        # 4. Delete
        del_res = client.delete(f"/api/v1/foods/{food_id}")
        assert del_res.status_code == 200

    # 5. Verify deleted
    verify_res = client.get(f"/api/v1/foods/{food_id}")
    assert verify_res.status_code == 404


def test_food_validation_errors():
    # Negative serving size should be rejected with 422
    invalid_payload = {
        "name": "Invalid Food",
        "category": "staple",
        "serving_size_g": -50.0,
        "energy_kcal": 100.0,
        "carbohydrate_g": 20.0,
        "protein_g": 5.0,
        "fat_g": 1.0,
    }
    res = client.post("/api/v1/foods", json=invalid_payload)
    assert res.status_code == 422


def test_food_micronutrients_sodium_and_saturated_fat():
    """Verify creating/updating food with sodium_mg & saturated_fat_g and rejecting negative values."""
    food_payload = {
        "name": "Cá thu kho nhạt (Braised Mackerel)",
        "category": "protein",
        "serving_size_g": 100.0,
        "energy_kcal": 190.0,
        "carbohydrate_g": 2.0,
        "protein_g": 20.0,
        "fat_g": 11.0,
        "sodium_mg": 320.5,
        "saturated_fat_g": 2.8,
        "is_test_data": True,
    }
    res = client.post("/api/v1/foods", json=food_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    food_id = data["id"]
    assert data["sodium_mg"] == 320.5
    assert data["saturated_fat_g"] == 2.8

    try:
        # Update micronutrients
        upd_res = client.put(
            f"/api/v1/foods/{food_id}",
            json={"sodium_mg": 450.0, "saturated_fat_g": 3.5},
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["sodium_mg"] == 450.0
        assert upd_res.json()["saturated_fat_g"] == 3.5

        # Negative sodium_mg should be rejected with 422
        neg_sodium = client.post(
            "/api/v1/foods",
            json={**food_payload, "name": "Bad Sodium", "sodium_mg": -10.0},
        )
        assert neg_sodium.status_code == 422

        # Negative saturated_fat_g should be rejected with 422
        neg_sat = client.post(
            "/api/v1/foods",
            json={**food_payload, "name": "Bad Sat Fat", "saturated_fat_g": -1.5},
        )
        assert neg_sat.status_code == 422
    finally:
        client.delete(f"/api/v1/foods/{food_id}")


def test_seed_vn_foods_idempotent_and_metadata_response():
    """Verify running seed_vn_foods twice is idempotent and API returns metadata + structured allergens."""
    from app.db.session import SessionLocal
    from app.models.allergen import Allergen
    from app.models.food import Food
    from app.scripts.seed_vn_foods import seed_vn_foods

    db = SessionLocal()
    try:
        summary_1 = seed_vn_foods(db)
        food_count_1 = db.query(Food).count()
        allergen_count_1 = db.query(Allergen).count()

        summary_2 = seed_vn_foods(db)
        food_count_2 = db.query(Food).count()
        allergen_count_2 = db.query(Allergen).count()

        assert summary_1["foods_total_in_dataset"] >= 60
        assert summary_2["foods_inserted"] == 0
        assert summary_2["foods_updated"] == summary_1["foods_total_in_dataset"]
        assert food_count_1 == food_count_2
        assert allergen_count_1 == allergen_count_2
        assert allergen_count_2 >= 8
    finally:
        db.close()

    # Verify API exposes preparation_state, data_source, data_version, and structured allergens
    res = client.get("/api/v1/foods?search=Tôm sú&limit=20")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    shrimp = next(i for i in items if "Tôm sú" in i["name"])
    assert shrimp["preparation_state"] == "cooked"
    assert shrimp["data_source"] in ("VN_NIN_2007", "USDA_FDC")
    assert shrimp["data_version"] == "v1.0"
    allergen_codes = {a["code"] for a in shrimp["allergens"]}
    assert "shellfish" in allergen_codes
    assert "seafood" in allergen_codes



