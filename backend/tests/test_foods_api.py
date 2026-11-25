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

