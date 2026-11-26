import uuid
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_glucose_records_lifecycle_and_stats():
    # 1. Create user
    test_email = f"glucose_{uuid.uuid4().hex[:8]}@example.com"
    user_res = client.post(
        "/api/v1/users",
        json={"email": test_email, "display_name": "Glucose Tester"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    try:
        # 2. Add first record (fasting)
        rec1_res = client.post(
            "/api/v1/glucose-records",
            json={
                "user_id": user_id,
                "glucose_value": 6.20,
                "unit": "mmol/L",
                "measurement_context": "fasting",
                "note": "Early morning",
            },
        )
        assert rec1_res.status_code == 201, rec1_res.text
        rec1 = rec1_res.json()
        rec1_id = rec1["id"]
        assert rec1["glucose_value"] == 6.20
        assert rec1["measurement_context"] == "fasting"

        # 3. Add second record (after_meal)
        rec2_res = client.post(
            "/api/v1/glucose-records",
            json={
                "user_id": user_id,
                "glucose_value": 8.40,
                "unit": "mmol/L",
                "measurement_context": "after_meal",
                "note": "2 hours post-lunch",
            },
        )
        assert rec2_res.status_code == 201
        rec2 = rec2_res.json()
        rec2_id = rec2["id"]

        # 4. List records for user
        list_res = client.get(f"/api/v1/glucose-records/user/{user_id}")
        assert list_res.status_code == 200
        records = list_res.json()
        assert len(records) == 2

        # 5. Filter by context
        filter_res = client.get(f"/api/v1/glucose-records/user/{user_id}?context=fasting")
        assert filter_res.status_code == 200
        filtered = filter_res.json()
        assert len(filtered) == 1
        assert filtered[0]["id"] == rec1_id

        # 6. Test statistics endpoint
        stats_res = client.get(f"/api/v1/glucose-records/user/{user_id}/stats?unit=mmol/L")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["count"] == 2
        assert stats["avg_value"] == 7.30
        assert stats["min_value"] == 6.20
        assert stats["max_value"] == 8.40

        # 7. Get record by ID
        get_res = client.get(f"/api/v1/glucose-records/{rec1_id}")
        assert get_res.status_code == 200
        assert get_res.json()["note"] == "Early morning"

        # 8. Update record
        update_res = client.put(
            f"/api/v1/glucose-records/{rec1_id}",
            json={"glucose_value": 6.30, "note": "Updated morning note"},
        )
        assert update_res.status_code == 200
        assert update_res.json()["glucose_value"] == 6.30
        assert update_res.json()["note"] == "Updated morning note"

        # 9. Delete record
        del_res = client.delete(f"/api/v1/glucose-records/{rec1_id}")
        assert del_res.status_code == 200

        # Verify deletion
        del_check = client.get(f"/api/v1/glucose-records/{rec1_id}")
        assert del_check.status_code == 404

    finally:
        # Cleanup user (will also cascade delete rec2)
        client.delete(f"/api/v1/users/{user_id}")


def test_glucose_record_validations():
    fake_user_id = str(uuid.uuid4())

    # Negative glucose value should fail with 422
    res_neg = client.post(
        "/api/v1/glucose-records",
        json={"user_id": fake_user_id, "glucose_value": -5.0, "unit": "mmol/L"},
    )
    assert res_neg.status_code == 422

    # Zero glucose value should fail with 422
    res_zero = client.post(
        "/api/v1/glucose-records",
        json={"user_id": fake_user_id, "glucose_value": 0, "unit": "mmol/L"},
    )
    assert res_zero.status_code == 422

    # Invalid unit should fail with 422
    res_unit = client.post(
        "/api/v1/glucose-records",
        json={"user_id": fake_user_id, "glucose_value": 6.5, "unit": "g/L"},
    )
    assert res_unit.status_code == 422

    # Invalid measurement context should fail with 422
    res_ctx = client.post(
        "/api/v1/glucose-records",
        json={
            "user_id": fake_user_id,
            "glucose_value": 6.5,
            "measurement_context": "midnight_snack",
        },
    )
    assert res_ctx.status_code == 422

