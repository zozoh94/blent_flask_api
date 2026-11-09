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

`seed` is idempotent: re-running it skips anything already present.

### Seeded data

**Users** (email / password):

| Role | Email | Password |
|------|-------|----------|
| admin | `admin@digimarket.test` | `AdminPass123` |
| client | `client@digimarket.test` | `ClientPass123` |

**Products:**

| Name | Category | Price | Stock |
|------|----------|------:|------:|
| Clavier mécanique RGB | Périphériques | 89.99 | 40 |
| Souris gaming sans fil | Périphériques | 49.99 | 60 |
| Écran 27" 144 Hz | Écrans | 299.00 | 15 |
| SSD NVMe 1 To | Stockage | 109.90 | 80 |

**Orders:** two `pending` orders for the seed client (one with 1x Clavier and
2x Souris, one with 1x Écran). They are left pending on purpose, since stock is
only consumed once an admin validates an order.

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

## Endpoints

Access: **Public** (no token), **Auth** (any logged-in user), **Admin** (admin only).

| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/api/auth/register` | Public | Create a client account |
| POST | `/api/auth/login` | Public | Log in, returns a JWT access token |
| GET | `/api/products` | Public | List products (paginated; `search`, `sort`, `order`, `page`, `per_page`) |
| GET | `/api/products/<id>` | Public | Get one product |
| POST | `/api/products` | Admin | Create a product |
| PUT | `/api/products/<id>` | Admin | Update a product |
| DELETE | `/api/products/<id>` | Admin | Delete a product |
| GET | `/api/orders` | Auth | List orders (clients see their own, admins see all; `user_id` filter for admins) |
| POST | `/api/orders` | Auth | Place an order |
| GET | `/api/orders/<id>` | Auth | Get one order (owner or admin) |
| PATCH | `/api/orders/<id>` | Admin | Change an order's status |
| GET | `/api/orders/<id>/items` | Auth | List an order's items (owner or admin) |

## Run the tests

```bash
uv run pytest
```

Lint and formatting (the same checks the CI runs):

```bash
uv run ruff check .
uv run ruff format --check .
```
