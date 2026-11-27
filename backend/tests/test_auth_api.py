import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_user(email: str, password: str = "SecretPass123!", consent: bool = True):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Auth Test User",
            "consent_accepted": consent,
        },
    )


def test_auth_register_login_and_me_lifecycle():
    email = f"auth_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    # 1. Reject registration if consent_accepted is False
    bad_consent = _register_user(email, password, consent=False)
    assert bad_consent.status_code == 400

    # 2. Register successfully
    reg_res = _register_user(email, password, consent=True)
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["email"] == email
    assert reg_data["display_name"] == "Auth Test User"
    assert reg_data["full_name"] == "Auth Test User"
    assert "password_hash" not in reg_data
    user_id = reg_data["id"]

    # 3. Reject duplicate email
    dup_res = _register_user(email, password, consent=True)
    assert dup_res.status_code == 409

    # 4. Wrong password returns 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 5. Valid login returns Bearer JWT token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, login_res.text
    login_data = login_res.json()
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["full_name"] == "Auth Test User"
    assert login_data["user"]["display_name"] == "Auth Test User"
    token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 6. GET /auth/me returns current user
        me_res = client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["id"] == user_id
        assert me_res.json()["email"] == email
        assert me_res.json()["full_name"] == "Auth Test User"
        assert me_res.json()["display_name"] == "Auth Test User"
    finally:
        client.delete(f"/api/v1/users/{user_id}", headers=headers)


def test_protected_endpoints_require_valid_token():
    random_id = str(uuid.uuid4())

    # Missing token -> 401 Unauthorized
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get(f"/api/v1/users/{random_id}").status_code == 401
    assert client.get(f"/api/v1/health-profiles/user/{random_id}").status_code == 401
    assert client.get(f"/api/v1/glucose-records/user/{random_id}").status_code == 401
    assert client.post("/api/v1/nutrition/recommend", json={"user_id": random_id, "meal_type": "lunch"}).status_code == 401

    # Invalid/malformed token -> 401 Unauthorized
    bad_headers = {"Authorization": "Bearer invalid.jwt.token"}
    assert client.get("/api/v1/auth/me", headers=bad_headers).status_code == 401
    assert client.get(f"/api/v1/users/{random_id}", headers=bad_headers).status_code == 401


def test_cross_user_access_forbidden():
    """Verify User A with valid JWT receives 403 Forbidden when accessing or modifying User B's resources."""
    email_a = f"user_a_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"user_b_{uuid.uuid4().hex[:8]}@example.com"
    pw = "Password123!"

    res_a = _register_user(email_a, pw, consent=True)
    res_b = _register_user(email_b, pw, consent=True)
    assert res_a.status_code == 201 and res_b.status_code == 201

    id_a = res_a.json()["id"]
    id_b = res_b.json()["id"]

    tok_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": pw}).json()["access_token"]
    tok_b = client.post("/api/v1/auth/login", json={"email": email_b, "password": pw}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {tok_a}"}
    headers_b = {"Authorization": f"Bearer {tok_b}"}

    try:
        # User B creates health profile and glucose record
        hp_b = client.post(
            "/api/v1/health-profiles",
            json={"user_id": id_b, "height_cm": 165.0, "weight_kg": 60.0},
            headers=headers_b,
        )
        assert hp_b.status_code == 201

        gr_b = client.post(
            "/api/v1/glucose-records",
            json={"user_id": id_b, "glucose_value": 6.5, "unit": "mmol/L"},
            headers=headers_b,
        )
        assert gr_b.status_code == 201
        gr_b_id = gr_b.json()["id"]

        # User A attempts to access/modify User B's resources -> all 403 Forbidden
        assert client.get(f"/api/v1/users/{id_b}", headers=headers_a).status_code == 403
        assert client.put(f"/api/v1/users/{id_b}", json={"display_name": "Hacked"}, headers=headers_a).status_code == 403
        assert client.delete(f"/api/v1/users/{id_b}", headers=headers_a).status_code == 403

        assert client.get(f"/api/v1/health-profiles/user/{id_b}", headers=headers_a).status_code == 403
        assert client.put(f"/api/v1/health-profiles/user/{id_b}", json={"weight_kg": 99.0}, headers=headers_a).status_code == 403
        assert client.delete(f"/api/v1/health-profiles/user/{id_b}", headers=headers_a).status_code == 403

        assert client.get(f"/api/v1/glucose-records/user/{id_b}", headers=headers_a).status_code == 403
        assert client.get(f"/api/v1/glucose-records/user/{id_b}/stats", headers=headers_a).status_code == 403
        assert client.get(f"/api/v1/glucose-records/{gr_b_id}", headers=headers_a).status_code == 403
        assert client.put(f"/api/v1/glucose-records/{gr_b_id}", json={"glucose_value": 9.9}, headers=headers_a).status_code == 403
        assert client.delete(f"/api/v1/glucose-records/{gr_b_id}", headers=headers_a).status_code == 403

        assert client.post("/api/v1/nutrition/recommend", json={"user_id": id_b, "meal_type": "lunch"}, headers=headers_a).status_code == 403
        assert client.get(f"/api/v1/nutrition/recommendations/user/{id_b}", headers=headers_a).status_code == 403

    finally:
        client.delete(f"/api/v1/users/{id_a}", headers=headers_a)
        client.delete(f"/api/v1/users/{id_b}", headers=headers_b)
