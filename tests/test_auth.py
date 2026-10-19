"""Integration tests for the authentication routes.

They drive the real HTTP endpoints POST /api/auth/register and
POST /api/auth/login end to end, asserting the contract a client relies on.
"""

from flask_jwt_extended import decode_token

# A valid signup payload reused across tests; individual tests override one
# field at a time to exercise a single rule.
VALID_USER = {
    "email": "alice@example.com",
    "password": "StrongPass123",
    "name": "Alice Martin",
}


def _register(client, **overrides):
    """Register VALID_USER, letting a test tweak any field."""
    return client.post("/api/auth/register", json={**VALID_USER, **overrides})


# --- POST /api/auth/register -------------------------------------------------


def test_register_creates_a_client_account(client):
    resp = _register(client)

    # A fresh signup succeeds and returns the new account as a client.
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["email"] == VALID_USER["email"]
    assert body["name"] == VALID_USER["name"]
    assert body["role"] == "client"
    assert "id" in body

    # The password must never leak back, in any form.
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_a_duplicate_email(client):
    _register(client)

    # The email is the unique identity of an account: a second signup with the
    # same address is a conflict, not a new user.
    resp = _register(client)
    assert resp.status_code == 409


def test_register_rejects_a_missing_field(client):
    # A signup without a password is incomplete and must be refused.
    incomplete = {k: v for k, v in VALID_USER.items() if k != "password"}
    resp = client.post("/api/auth/register", json=incomplete)
    assert resp.status_code == 400


def test_register_rejects_an_invalid_email(client):
    # "adresse email unique" implies a real address: a malformed one is refused.
    resp = _register(client, email="not-an-email")
    assert resp.status_code == 400


def test_register_rejects_a_weak_password(client):
    # "mot de passe sécurisé": a too-short password is rejected.
    # (recommended minimum enforced by the implementation: 8 characters.)
    resp = _register(client, password="abc")
    assert resp.status_code == 400


def test_register_ignores_a_role_sent_by_the_client(client):
    # Security: nobody escalates to admin just by putting "role": "admin" in
    # the signup body. Self-service registration always yields a client.
    resp = _register(client, role="admin")
    assert resp.status_code == 201
    assert resp.get_json()["role"] == "client"


# --- POST /api/auth/login ----------------------------------------------------


def test_login_returns_a_token_for_valid_credentials(client):
    _register(client)

    resp = client.post(
        "/api/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )

    # Correct credentials yield a usable access token.
    assert resp.status_code == 200
    token = resp.get_json()["access_token"]
    assert isinstance(token, str) and token


def test_login_token_identifies_the_user(app, client):
    user_id = _register(client).get_json()["id"]

    resp = client.post(
        "/api/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    token = resp.get_json()["access_token"]

    # The token is a genuine JWT bound to this user: its subject is their id.
    # This is what later lets protected routes know who is calling.
    with app.app_context():
        decoded = decode_token(token)
    assert decoded["sub"] == str(user_id)


def test_login_rejects_a_wrong_password(client):
    _register(client)

    resp = client.post(
        "/api/auth/login",
        json={"email": VALID_USER["email"], "password": "WrongPass999"},
    )
    assert resp.status_code == 401


def test_login_rejects_an_unknown_email(client):
    # No account, no token: an unknown email cannot authenticate.
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert resp.status_code == 401


def test_login_rejects_a_missing_field(client):
    # A login without a password is malformed.
    resp = client.post("/api/auth/login", json={"email": VALID_USER["email"]})
    assert resp.status_code == 400
