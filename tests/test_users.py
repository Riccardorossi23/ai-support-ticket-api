from tests.conftest import PASSWORD


def test_register_ok(client):
    r = client.post("/users/register", json={"username": "anna", "email": "anna@example.com", "password": PASSWORD})
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "user"
    assert "password" not in body and "hashed_password" not in body


def test_register_cannot_choose_admin_role(client):
    # Provo a mandare role=admin: il campo deve essere ignorato.
    r = client.post(
        "/users/register",
        json={"username": "furbo", "email": "furbo@example.com", "password": PASSWORD, "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "user"


def test_register_duplicate_returns_409(client, user_headers):
    r = client.post("/users/register", json={"username": "altro", "email": "MARIO@example.com", "password": PASSWORD})
    assert r.status_code == 409


def test_register_validation_returns_422(client):
    r = client.post("/users/register", json={"username": "ab", "email": "non-una-email", "password": "corta"})
    assert r.status_code == 422


def test_password_is_stored_hashed(client, db_session, user_headers):
    from app.models import User

    user = db_session.query(User).filter(User.username == "mario").one()
    assert user.hashed_password != PASSWORD
    assert user.hashed_password.startswith("pbkdf2_sha256$")


def test_login_ok_returns_bearer_token(client, user_headers):
    r = client.post("/users/login", json={"email": "mario@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_returns_401(client, user_headers):
    r = client.post("/users/login", json={"email": "mario@example.com", "password": "sbagliata"})
    assert r.status_code == 401


def test_login_unknown_user_returns_401(client):
    r = client.post("/users/login", json={"email": "nessuno@example.com", "password": PASSWORD})
    assert r.status_code == 401


def test_me_returns_current_user(client, user_headers):
    r = client.get("/users/me", headers=user_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "mario"


def test_me_without_token_returns_401(client):
    assert client.get("/users/me").status_code == 401


def test_me_with_invalid_token_returns_401(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer token.finto.qualunque"})
    assert r.status_code == 401
