# DigiMarket API

REST API for the DigiMarket e-commerce platform, built with Flask, SQLAlchemy
(SQLite) and JWT authentication.

## Requirements

- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- Python >= 3.12 (uv installs a suitable interpreter automatically)

## Install

```bash
uv sync
```

This creates an isolated virtual environment and installs both the runtime and
the dev dependencies.

## Initialize the database

Create the tables, then (optionally) load some test data:

```bash
uv run flask --app app init-db
uv run flask --app app seed
```

## Run the app

```bash
uv run flask --app app run
```

## API documentation

With the app running, the OpenAPI docs are served under `/api/docs`:

- Swagger UI: http://127.0.0.1:5000/api/docs/swagger
- ReDoc: http://127.0.0.1:5000/api/docs/redoc
- Raw OpenAPI spec: http://127.0.0.1:5000/api/docs/openapi.json

Use the **Authorize** button in Swagger UI to send a JWT (obtained from
`POST /api/auth/login`) on the protected routes.

## Run the tests

```bash
uv run pytest
```

Lint and formatting (the same checks the CI runs):

```bash
uv run ruff check .
uv run ruff format --check .
```
