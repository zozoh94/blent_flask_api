import os


class DefaultConfig:
    # Both are read from the environment so they can be overridden in
    # production; the defaults are dev-only. Set JWT_SECRET_KEY in prod.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
