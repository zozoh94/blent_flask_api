"""Shared pytest fixtures.

Every test gets a freshly built application wired to its own in-memory
SQLite database, so tests never share state and never touch real data.
"""

import pytest

from app import create_app, db


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
