"""Shared pytest fixtures.

Every test gets a freshly built application wired to its own in-memory
SQLite database, so tests never share state and never touch real data.
"""

import pytest

from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    # Build the app against an isolated in-memory database with a known JWT
    # secret, so token signing and verification are deterministic in tests.
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

    # Create the schema once, hand the app to the test, then wipe everything.
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    # The HTTP entry point the integration tests drive.
    return app.test_client()


@pytest.fixture
def auth_header_factory(client):
    """Build an Authorization header for a freshly created user of a given role.

    The user is inserted directly, then logged in through the real API, so the
    header carries a genuine JWT and the tests exercise the true auth path.
    """
    created = []

    def _make(role="client", password="StrongPass123"):
        email = f"{role}-{len(created)}@example.com"
        user = User(email=email, name=f"{role.title()} User", role=role)
        user.password = password
        db.session.add(user)
        db.session.commit()
        created.append(email)

        resp = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        token = resp.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def admin_header(auth_header_factory):
    # Header of a logged-in admin, for the admin-only endpoints.
    return auth_header_factory(role="admin")


@pytest.fixture
def client_header(auth_header_factory):
    # Header of a logged-in regular client, used to prove endpoints are guarded.
    return auth_header_factory(role="client")
